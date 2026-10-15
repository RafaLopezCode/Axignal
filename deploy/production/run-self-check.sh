#!/bin/sh
# AXIGNAL observes axignal.com and ten organizations it knows with certainty (truth_set.json)
# with the release just deployed and checks each reading against
# what we know to be true (tools/evaluation/self_truth.json, truths/). Every disagreement is an engine
# defect; a check that passed after the previous deploy and fails now is a regression.
#
# Isolated and read-only for production: a throwaway container from the deployed image,
# runtime data mounted read-only and copied inside it (tools/evaluation/run_golden.py).
# Reports stay on the host in /var/lib/axignal/self-check/<sha>/; latest.json is the
# baseline for the next deploy. Never blocks or reverts a deploy: it reports.
set -eu

release="$(readlink -f /srv/axignal/docker/current)"
[ -n "$release" ] && [ -d "$release" ] || {
  echo '{"state":"NO_CURRENT_RELEASE"}' >&2
  exit 2
}
sha="$(basename "$release")"
image="axignal-runtime:$sha"
/usr/bin/docker image inspect "$image" >/dev/null

root=/var/lib/axignal/self-check
work="$root/$sha"
umask 077
mkdir -p "$work"
# Same configuration as the running runtime; the env file never leaves this host.
/usr/bin/docker inspect axignal-prod-runtime --format '{{range .Config.Env}}{{println .}}{{end}}' > "$work/env"
trap 'rm -f "$work/env"' EXIT

set -- /usr/bin/docker run --rm --name axignal-self-check --group-add 1991 --memory 1500m --cpus 1 \
  --entrypoint /app/.venv/bin/python --env-file "$work/env" \
  -e AXIGNAL_ADMIN_ACCESS_ENABLED=false \
  -e AXIGNAL_GOLDEN_SET=/app/tools/evaluation/truth_set.json \
  -v /var/lib/axignal/runtime:/src:ro \
  -v /etc/axignal/subscriber-runtime.conf:/run/secrets/subscriber_configuration:ro
for secret in openai_api_key crux_api_key google_client_secret typesafe_api_key; do
  if [ -r "/etc/axignal/secrets/$secret" ]; then
    set -- "$@" -v "/etc/axignal/secrets/$secret:/run/secrets/$secret:ro"
  fi
done
"$@" "$image" -m tools.evaluation.run_golden > "$work/views.json" 2> "$work/observe.log"

if [ -f "$root/latest.json" ]; then cp "$root/latest.json" "$work/previous.json"; else echo '{}' > "$work/previous.json"; fi
chmod 644 "$work/views.json" "$work/previous.json"
status=0
# No network, nothing writable: the report comes back on stdout, the summary on stderr.
/usr/bin/docker run --rm --network none --read-only --entrypoint /app/.venv/bin/python \
  -v "$work/views.json:/self/views.json:ro" -v "$work/previous.json:/self/previous.json:ro" \
  "$image" -m tools.evaluation.self_check /self/views.json --out - --previous /self/previous.json \
  > "$work/report.json" 2> "$work/summary.txt" || status=$?
cat "$work/summary.txt"
[ "$status" -eq 0 ] && [ -s "$work/report.json" ] && cp "$work/report.json" "$root/latest.json"
echo "{\"state\":\"DONE\",\"sha\":\"$sha\",\"report\":\"$work/report.json\",\"regressions\":$(grep -c '^REGRESSION' "$work/summary.txt" || true)}"
