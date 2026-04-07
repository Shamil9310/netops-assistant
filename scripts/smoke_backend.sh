#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
USERNAME="${USERNAME:-engineer}"
PASSWORD="${PASSWORD:-engineer123}"

echo "[smoke] health"
curl -fsS "${API_BASE_URL}/api/v1/health" >/dev/null

echo "[smoke] login"
LOGIN_RESPONSE_HEADERS="$(mktemp)"
LOGIN_RESPONSE_BODY="$(mktemp)"
curl -fsS -D "${LOGIN_RESPONSE_HEADERS}" -o "${LOGIN_RESPONSE_BODY}" \
  -H "Content-Type: application/json" \
  -X POST "${API_BASE_URL}/api/v1/auth/login" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}"

SESSION_COOKIE="$(grep -i "set-cookie: netops_session=" "${LOGIN_RESPONSE_HEADERS}" | head -n 1 | sed -E 's/.*netops_session=([^;]+).*/\1/')"
CSRF_COOKIE="$(grep -i "set-cookie: netops_csrf=" "${LOGIN_RESPONSE_HEADERS}" | head -n 1 | sed -E 's/.*netops_csrf=([^;]+).*/\1/')"

if [[ -z "${SESSION_COOKIE}" ]]; then
  echo "[smoke] session cookie not found" >&2
  exit 1
fi

echo "[smoke] dashboard today"
curl -fsS "${API_BASE_URL}/api/v1/dashboard/today" \
  -H "Cookie: netops_session=${SESSION_COOKIE}" >/dev/null

echo "[smoke] reports history"
curl -fsS "${API_BASE_URL}/api/v1/reports/history" \
  -H "Cookie: netops_session=${SESSION_COOKIE}" >/dev/null

echo "[smoke] logout"
curl -fsS -X POST "${API_BASE_URL}/api/v1/auth/logout" \
  -H "Cookie: netops_session=${SESSION_COOKIE}; netops_csrf=${CSRF_COOKIE}" \
  -H "X-CSRF-Token: ${CSRF_COOKIE}" >/dev/null

rm -f "${LOGIN_RESPONSE_HEADERS}" "${LOGIN_RESPONSE_BODY}"
echo "[smoke] done"
