#!/bin/sh
set -eu

release="$(readlink -f /srv/axignal/docker/current)"
[ -n "$release" ] && [ -d "$release" ] || {
  echo '{"state":"NO_CURRENT_RELEASE"}' >&2
  exit 2
}

sha="$(basename "$release")"
image="axignal-runtime:$sha"
secret="/etc/axignal/secrets/gsc_oauth.json"

[ -r "$secret" ] || {
  echo '{"state":"NOT_CONFIGURED"}'
  exit 0
}

/usr/bin/docker image inspect "$image" >/dev/null

exec /usr/bin/docker run --rm   --name axignal-prod-gsc-sync   --network axignal_prod_internal   --user 33:33   --read-only   --tmpfs /tmp:size=32m,mode=1777   --cap-drop ALL   --security-opt no-new-privileges:true   --pids-limit 64   --memory 256m   --cpus 0.5   --env AXIGNAL_GSC_ENABLED=true   --env AXIGNAL_GSC_PROPERTY=sc-domain:axignal.com   --env AXIGNAL_GSC_OAUTH_SECRET_FILE=/run/secrets/gsc_oauth.json   --env AXIGNAL_DATA_DIR=/var/lib/axignal/runtime   --mount type=bind,src=/var/lib/axignal/runtime,dst=/var/lib/axignal/runtime   --mount type=bind,src="$secret",dst=/run/secrets/gsc_oauth.json,readonly   --entrypoint python   "$image"   -m tools.runtime.gsc_sync
