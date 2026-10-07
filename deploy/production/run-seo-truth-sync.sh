#!/bin/sh
set -eu

release="$(readlink -f /srv/axignal/docker/current)"
[ -n "$release" ] && [ -d "$release" ] || {
  echo '{"state":"NO_CURRENT_RELEASE"}' >&2
  exit 2
}

sha="$(basename "$release")"
image="axignal-runtime:$sha"
oauth_secret="/etc/axignal/secrets/gsc_oauth.json"
crux_secret="/etc/axignal/secrets/crux_api_key"

[ -r "$oauth_secret" ] || {
  echo '{"state":"NOT_CONFIGURED"}'
  exit 0
}

/usr/bin/docker image inspect "$image" >/dev/null

set -- /usr/bin/docker run --rm   --name axignal-prod-seo-truth-sync   --network axignal_prod_internal   --user 33:33   --read-only   --tmpfs /tmp:size=32m,mode=1777   --cap-drop ALL   --security-opt no-new-privileges:true   --pids-limit 64   --memory 256m   --cpus 0.5   --env AXIGNAL_SEO_TRUTH_ENABLED=true   --env AXIGNAL_GSC_PROPERTY=sc-domain:axignal.com   --env AXIGNAL_GSC_OAUTH_SECRET_FILE=/run/secrets/gsc_oauth.json   --env AXIGNAL_PUBLIC_ORIGIN=https://axignal.com   --env AXIGNAL_SEO_SITEMAP_URL=https://axignal.com/sitemap.xml   --env AXIGNAL_SEO_INSPECTION_LIMIT=750   --env AXIGNAL_DATA_DIR=/var/lib/axignal/runtime   --mount type=bind,src=/var/lib/axignal/runtime,dst=/var/lib/axignal/runtime   --mount type=bind,src="$oauth_secret",dst=/run/secrets/gsc_oauth.json,readonly

if [ -r "$crux_secret" ]; then
  set -- "$@"     --env AXIGNAL_CRUX_API_KEY_FILE=/run/secrets/crux_api_key     --mount type=bind,src="$crux_secret",dst=/run/secrets/crux_api_key,readonly
fi

set -- "$@" --entrypoint python "$image" -m tools.runtime.seo_truth_sync
exec "$@"
