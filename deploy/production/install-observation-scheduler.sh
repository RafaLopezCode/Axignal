#!/bin/sh
set -eu
dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
case "${1:---check}" in
  --check|--install) ;;
  *) echo 'usage: install-observation-scheduler.sh [--check|--install]' >&2; exit 2 ;;
esac

/bin/sh -n "$dir/run-observation-daily.sh"
/usr/bin/systemd-analyze verify \
  "$dir/axignal-observation-daily.service" "$dir/axignal-observation-daily.timer"
if [ "${1:---check}" = --check ]; then
  echo '{"state":"VALIDATED","default_enabled":false}'
  exit 0
fi

# Install only scheduler units/config. Never copy into or move the immutable release/current.
install -d -o root -g www-data -m 0750 /etc/axignal/observation-runtime
if [ ! -e /etc/axignal/observation-runtime/scheduler.env ]; then
  install -o root -g www-data -m 0640 "$dir/observation-scheduler.env.example" \
    /etc/axignal/observation-runtime/scheduler.env
fi
for unit in axignal-observation-daily.service axignal-observation-daily.timer; do
  install -o root -g root -m 0644 "$dir/$unit" "/etc/systemd/system/$unit"
done
systemctl daemon-reload
systemctl enable --now axignal-observation-daily.timer
echo '{"state":"INSTALLED","configuration_preserved":true}'
