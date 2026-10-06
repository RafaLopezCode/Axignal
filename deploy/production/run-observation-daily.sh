#!/bin/sh
set -eu

release="$(readlink -f /srv/axignal/docker/current)"
[ -n "$release" ] && [ -d "$release" ] || {
  echo '{"state":"NO_CURRENT_RELEASE"}' >&2
  exit 2
}

sha="$(basename "$release")"
image="axignal-runtime:$sha"
config_dir="/etc/axignal/observation-runtime"
attention="$config_dir/attention.json"
enrollment="$config_dir/enrollment.json"

[ -r "$attention" ] && [ -r "$enrollment" ] || {
  echo '{"state":"NOT_CONFIGURED"}'
  exit 0
}

/usr/bin/docker image inspect "$image" >/dev/null

exec /usr/bin/docker run --rm   --name axignal-prod-observation-daily   --network axignal_prod_internal   --user 33:33   --read-only   --tmpfs /tmp:size=64m,mode=1777   --cap-drop ALL   --security-opt no-new-privileges:true   --pids-limit 96   --memory 512m   --cpus 1.0   --env AXIGNAL_OBSERVATION_RUNTIME_ENABLED=true   --env AXIGNAL_DATA_DIR=/var/lib/axignal/runtime   --env AXIGNAL_CODE_SHA="$sha"   --env AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE="$attention"   --env AXIGNAL_OBSERVATION_RUNTIME_ENROLLMENT_FILE="$enrollment"   --mount type=bind,src=/var/lib/axignal/runtime,dst=/var/lib/axignal/runtime   --mount type=bind,src="$config_dir",dst="$config_dir",readonly   --entrypoint python   "$image"   -m tools.runtime.observation_daily
