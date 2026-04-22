#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-${DECLUTTER_BASE_URL:-}}"
if [[ -z "${base_url}" ]]; then
  echo "usage: $0 https://api.your-domain.example" >&2
  echo "or set DECLUTTER_BASE_URL" >&2
  exit 64
fi

base_url="${base_url%/}"

curl -fsS "${base_url}/health/" >/tmp/declutter-health.json
curl -fsS "${base_url}/health/readiness" >/tmp/declutter-readiness.json
curl -fsS "${base_url}/launch/status" >/tmp/declutter-launch-status.json

printf 'health: '
cat /tmp/declutter-health.json
printf '\nreadiness: '
cat /tmp/declutter-readiness.json
printf '\nlaunch: '
cat /tmp/declutter-launch-status.json
printf '\n'
