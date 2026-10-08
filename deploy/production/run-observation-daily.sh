#!/bin/sh
set -eu

# The systemd EnvironmentFile supplies the existing runtime flag. No default activation.
if [ "${AXIGNAL_OBSERVATION_RUNTIME_ENABLED:-false}" != true ]; then
  echo '{"state":"DISABLED"}'
  exit 0
fi

release="$(readlink -f "${AXIGNAL_OBSERVATION_RELEASE:-/srv/axignal/docker/current}" 2>/dev/null || true)"
[ -n "$release" ] && [ -d "$release" ] || {
  echo '{"state":"NO_CURRENT_RELEASE"}' >&2
  exit 2
}

sha="$(basename "$release")"
image="axignal-runtime:$sha"
config_dir="${AXIGNAL_OBSERVATION_CONFIG_DIR:-/etc/axignal/observation-runtime}"
data_dir="${AXIGNAL_DATA_DIR:-/var/lib/axignal/runtime}"
name="${AXIGNAL_OBSERVATION_CONTAINER_NAME:-axignal-prod-observation-daily}"
network="${AXIGNAL_OBSERVATION_NETWORK:-axignal_prod_internal}"
docker="${AXIGNAL_OBSERVATION_DOCKER:-/usr/bin/docker}"
attention="$config_dir/attention.json"
enrollment="$config_dir/enrollment.json"
subscriber_config="${AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE:-/etc/axignal/subscriber-runtime.conf}"

[ -r "$attention" ] && [ -r "$enrollment" ] || {
  echo '{"state":"NOT_CONFIGURED"}'
  exit 0
}
[ -d "$data_dir" ] || {
  echo '{"state":"NO_DATA_DIRECTORY"}' >&2
  exit 2
}

# Research rechecks the existing PilotGrant/Billing entitlement, without payment secrets.
set --
if [ -r "$subscriber_config" ]; then
  set -- --env AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE=/run/axignal-subscriber.conf \
    --mount "type=bind,src=$subscriber_config,dst=/run/axignal-subscriber.conf,readonly"
fi
if [ -r "$config_dir/materialization.json" ]; then
  set -- "$@" --env AXIGNAL_OBSERVATION_MATERIALIZATION_FILE=/run/axignal-materialization.json \
    --mount "type=bind,src=$config_dir/materialization.json,dst=/run/axignal-materialization.json,readonly"
fi

# Host serialization complements, never replaces, the runtime's SQLite fencing.
# The stable container name also prevents overlap if its Docker CLI is killed.
exec 9>"$data_dir/observation-daily.lock"
if ! /usr/bin/flock -n 9; then
  echo '{"state":"INVOCATION_HELD"}'
  exit 0
fi
if "$docker" container inspect "$name" >/dev/null 2>&1; then
  echo '{"state":"CONTAINER_PRESENT"}'
  exit 0
fi
"$docker" image inspect "$image" >/dev/null

exec "$docker" run --rm --init \
  --name "$name" --network "$network" --user 33:33 \
  --read-only --tmpfs /tmp:size=64m,mode=1777 \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --pids-limit 96 --memory 512m --cpus 1.0 --stop-timeout 15 \
  --env AXIGNAL_OBSERVATION_RUNTIME_ENABLED=true \
  --env AXIGNAL_DATA_DIR=/var/lib/axignal/runtime \
  --env AXIGNAL_CODE_SHA="$sha" \
  --env AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE=/run/axignal-attention.json \
  --env AXIGNAL_OBSERVATION_RUNTIME_ENROLLMENT_FILE=/run/axignal-enrollment.json \
  --mount "type=bind,src=$data_dir,dst=/var/lib/axignal/runtime" \
  --mount "type=bind,src=$attention,dst=/run/axignal-attention.json,readonly" \
  --mount "type=bind,src=$enrollment,dst=/run/axignal-enrollment.json,readonly" \
  "$@" \
  --entrypoint python "$image" -m tools.runtime.observation_daily
