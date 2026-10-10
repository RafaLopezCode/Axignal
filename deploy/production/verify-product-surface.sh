#!/bin/sh
# Read-only live gate. Fails a deployment when old public UX or missing
# subscriber overlay leaves a "healthy" product unusable.
set -eu
origin=${AXIGNAL_PUBLIC_ORIGIN:-https://axignal.com}
case "$origin" in https://axignal.com|https://www.axignal.com) : ;; *) echo 'Invalid public origin' >&2; exit 2;; esac

status() { curl --silent --show-error --max-time 12 -o /dev/null -w '%{http_code}' "$origin$1"; }
expect() {
  actual=$(status "$1")
  [ "$actual" = "$2" ] || { echo "FAIL $1 expected $2, got $actual" >&2; exit 1; }
  echo "PASS $1 ($2)"
}
expect / 200
expect /demo 200
expect /panorama 308
expect /account 200
expect /login 200
expect /signup 200
expect /api/auth/status 200
# A 200 status alone is insufficient: base-only runtime can report all providers
# UNAVAILABLE while the marketing site appears healthy.
curl --silent --show-error --max-time 12 "$origin/api/auth/status" |
  python3 -c 'import json,sys; d=json.load(sys.stdin); assert any(p.get("id")=="google" and p.get("status")=="AVAILABLE" for p in d.get("providers",[])), "Google OIDC is not available"' ||
  { echo 'FAIL: Google sign-in unavailable' >&2; exit 1; }
echo 'PASS: Google sign-in available'
expect /api/subscriber/portfolio 401
expect /admin 404
expect /admin/customer-zero 404
expect /api/admin/session 404
curl --silent --show-error --max-time 12 "$origin/demo" | grep -q 'data-product-surface="living-observatory"' ||
  { echo 'FAIL: public example is not the current subscriber Observatory' >&2; exit 1; }
echo 'PASS: actual Observatory example is served'

# Container checks are only available on the authorized production host.
if command -v docker >/dev/null 2>&1; then
  for component in runtime experience landing; do
    healthy=$(docker inspect -f '{{.State.Health.Status}}' "axignal-prod-$component")
    [ "$healthy" = healthy ] || { echo "FAIL: $component not healthy" >&2; exit 1; }
  done
  [ -r /srv/axignal/docker/DEPLOYED_SHA ] || exit 1
  sha=${AXIGNAL_CODE_SHA:-$(cat /srv/axignal/docker/DEPLOYED_SHA)}
  for component in runtime experience landing; do
    actual=$(docker inspect -f '{{.Config.Image}}' "axignal-prod-$component")
    [ "$actual" = "axignal-$component:$sha" ] ||
      { echo "FAIL: $component is not on deployed SHA" >&2; exit 1; }
  done
  echo 'PASS: all three service images and SHA match'
fi
