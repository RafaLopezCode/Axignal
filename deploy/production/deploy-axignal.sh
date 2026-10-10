#!/bin/sh
# The sole supported production Compose entrypoint. Prevents silently dropping
# the optional subscriber overlay (the 2026-10-10 root cause).
set -eu

usage() {
  echo 'Usage: AXIGNAL_CODE_SHA=<full-sha> sh deploy/production/deploy-axignal.sh {check|build|up}' >&2
  exit 2
}
[ "$#" -eq 1 ] || usage
case "$1" in check|build|up) operation=$1;; *) usage;; esac
: "${AXIGNAL_CODE_SHA:?Full canonical SHA is required}"
case "$AXIGNAL_CODE_SHA" in *[!0123456789abcdef]*|'') echo 'SHA is not lowercase hexadecimal' >&2; exit 2;; esac
[ "${#AXIGNAL_CODE_SHA}" -eq 40 ] || { echo 'Full 40-character SHA required' >&2; exit 2; }

# Refuse a run from an unrelated project or mutable checkout.
[ -f deploy/production/compose.yml ] || { echo 'Run from the AXIGNAL immutable release root' >&2; exit 2; }
if command -v git >/dev/null 2>&1 && git rev-parse --verify HEAD >/dev/null 2>&1; then
  [ "$(git rev-parse HEAD)" = "$AXIGNAL_CODE_SHA" ] || { echo 'Release source does not match SHA' >&2; exit 2; }
fi

runtime_config=${AXIGNAL_SUBSCRIBER_CONFIGURATION_HOST_FILE:-/etc/axignal/subscriber-runtime.conf}
google_secret=${AXIGNAL_GOOGLE_CLIENT_SECRET_HOST_FILE:-/etc/axignal/secrets/google_client_secret}
runtime_env=${AXIGNAL_RUNTIME_ENV_FILE:-/etc/axignal/runtime.env}

[ -s "$runtime_config" ] || { echo 'Subscriber config unavailable: refusing to downgrade to base-only Compose' >&2; exit 2; }
[ -s "$google_secret" ] || { echo 'Google secret unavailable: refusing to downgrade to base-only Compose' >&2; exit 2; }
[ -f "$runtime_env" ] || { echo 'Runtime environment file missing' >&2; exit 2; }

# Do not source the config. Only the explicit subscriber profile can serve the
# subscriber product. Base Compose is reserved for documented, manual rollback.
case ${AXIGNAL_DEPLOY_PROFILE:-subscriber} in
 subscriber) : ;;
 *) echo 'Refusing to deploy without subscriber overlay. Use documented rollback for base.' >&2; exit 2 ;;
esac
export AXIGNAL_CODE_SHA
docker compose --env-file "$runtime_env" -p axignal-prod \
  -f deploy/production/compose.yml \
  -f deploy/production/compose.subscriber.override.yml config --quiet
case "$operation" in
 check) echo 'AXIGNAL_RELEASE_PROFILE=subscriber; validation=passed' ;;
 build)
  docker compose --env-file "$runtime_env" -p axignal-prod \
    -f deploy/production/compose.yml \
    -f deploy/production/compose.subscriber.override.yml build runtime experience landing ;;
 up)
  docker compose --env-file "$runtime_env" -p axignal-prod \
    -f deploy/production/compose.yml \
    -f deploy/production/compose.subscriber.override.yml up -d --no-build runtime experience landing
  # A Docker "healthy" state is not product acceptance. Fail the release if
  # its public login/demo/customer boundary disagrees with the artifact.
  attempt=0
  until sh deploy/production/verify-product-surface.sh; do
    attempt=$((attempt + 1))
    [ "$attempt" -lt 15 ] || { echo "Product surface validation failed after cutover" >&2; exit 1; }
    sleep 3
  done ;;
esac
