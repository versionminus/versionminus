#!/usr/bin/env bash
set -euo pipefail

# Smoke test against a running instance (default: http://licodex-api:8000)
# Validates:
#  - health & root endpoints
#  - ensure specific users exist (idempotent): diogo, nuno, shan
#  - for each user: create several unique threads
#  - for each thread: create several messages
#  - basic verification of creations

BASE_URL="${BASE_URL:-http://licodex-api:8000}"
API_PREFIX="${API_PREFIX:-/api/v1}"

log() { printf "[smoke] %s\n" "$*"; }
fail() { echo "[smoke][ERROR] $*" >&2; exit 1; }

curl_json() {
  local method="$1"; shift
  local path="$1"; shift
  local data="${1:-}"
  if [[ -n "$data" ]]; then
    curl -sS -X "$method" -H 'Content-Type: application/json' \
      --fail "${BASE_URL}${path}" -d "$data"
  else
    curl -sS -X "$method" --fail "${BASE_URL}${path}"
  fi
}

log "Health liveness"
live_json=$(curl_json GET "${API_PREFIX}/health/liveness") || fail "liveness endpoint failed"
grep -q '"status":"ok"' <<<"$live_json" || fail "liveness not ok"

log "Root"
root_json=$(curl_json GET "/") || fail "root endpoint failed"
grep -q '"status":"ok"' <<<"$root_json" || fail "root not ok"

#############################
# Helper allowing non-2xx
#############################
curl_json_status() {
  local method="$1"; shift
  local path="$1"; shift
  local data="${1:-}"
  local tmp http
  tmp=$(mktemp)
  if [[ -n "$data" ]]; then
    http=$(curl -sS -o "$tmp" -w '%{http_code}' -X "$method" -H 'Content-Type: application/json' "${BASE_URL}${path}" -d "$data" || true)
  else
    http=$(curl -sS -o "$tmp" -w '%{http_code}' -X "$method" "${BASE_URL}${path}" || true)
  fi
  CURL_BODY="$(cat "$tmp")"
  CURL_STATUS="$http"
  rm -f "$tmp"
}

THREADS_PER_USER=${THREADS_PER_USER:-2}
MESSAGES_PER_THREAD=${MESSAGES_PER_THREAD:-3}

USERS=(
  "diogo@licodex.com"
  "nuno@licodex.com"
  "shan@licodex.com"
)

declare -A USER_IDS

log "Ensuring users exist (${USERS[*]})"
for email in "${USERS[@]}"; do
  curl_json_status POST "${API_PREFIX}/users/" "{\"email\":\"$email\",\"role\":\"user\"}"
  body="$CURL_BODY"
  status="$CURL_STATUS"
  if [[ "$status" == "201" ]]; then
    user_id=$(sed -n 's/.*"id":"\([^"]*\)".*/\1/p' <<<"$body")
    [[ -n "$user_id" ]] || fail "Could not parse new user id for $email"
    log "Created user $email ($user_id)"
  elif [[ "$status" == "409" ]]; then
    # Already exists: fetch list and extract id via Python for robustness
    users_json=$(curl_json GET "${API_PREFIX}/users/") || fail "list users failed while resolving existing user $email"
  user_id=$( LOOKUP_EMAIL="$email" /usr/bin/env python3 - <<PYEOF
import json,os
data=json.loads('''$users_json''')
email=os.environ['LOOKUP_EMAIL']
print(next((u.get("id") for u in data if u.get("email")==email), ""))
PYEOF
  )
    [[ -n "$user_id" ]] || fail "Could not resolve existing user id for $email"
    log "User already existed $email ($user_id)"
  else
    fail "Unexpected status creating user $email: $status ($body)"
  fi
  USER_IDS[$email]="$user_id"
done

created_thread_ids=()
created_message_ids=()

ts_base=$(date +%s%N)

for email in "${USERS[@]}"; do
  user_id=${USER_IDS[$email]}
  log "Creating threads for $email (user_id=$user_id)"
  for ((t=1; t<=THREADS_PER_USER; t++)); do
    thread_title="smoke-${ts_base}-${t}-$(echo "$email" | tr '@.' '--')"
    thread_json=$(curl_json POST "${API_PREFIX}/threads/" "{\"title\":\"$thread_title\",\"user_id\":\"$user_id\"}") || fail "thread create failed for $email"
    thread_id=$(sed -n 's/.*"id":"\([^"]*\)".*/\1/p' <<<"$thread_json")
    [[ -n "$thread_id" ]] || fail "Could not extract thread id ($email t=$t)"
    created_thread_ids+=("$thread_id")
    grep -q "$thread_title" <<<"$thread_json" || fail "Thread title mismatch ($thread_title)"
    log "  Created thread $thread_title ($thread_id)"

    # Messages
    for ((m=1; m<=MESSAGES_PER_THREAD; m++)); do
      content="Message $m for $thread_title"
      msg_json=$(curl_json POST "${API_PREFIX}/messages/" "{\"thread_id\":\"$thread_id\",\"content\":\"$content\"}") || fail "message create failed (thread $thread_id)"
      msg_id=$(sed -n 's/.*"id":"\([^"]*\)".*/\1/p' <<<"$msg_json")
      [[ -n "$msg_id" ]] || fail "Could not parse message id (thread $thread_id)"
      created_message_ids+=("$msg_id")
    done

    # Verify messages count for thread
    list_msgs=$(curl_json GET "${API_PREFIX}/messages/thread/$thread_id") || fail "list messages failed (thread $thread_id)"
    # count occurrences of id field within this thread list
    msg_count=$(grep -o '"id":"' <<<"$list_msgs" | wc -l | tr -d ' ')
    if [[ "$msg_count" -lt "$MESSAGES_PER_THREAD" ]]; then
      fail "Expected >= $MESSAGES_PER_THREAD messages for $thread_id got $msg_count"
    fi
    log "  Messages created: $msg_count"
  done
done

# Final verification: list threads and ensure each created thread appears
threads_json=$(curl_json GET "${API_PREFIX}/threads/") || fail "list threads failed"
for tid in "${created_thread_ids[@]}"; do
  grep -q "$tid" <<<"$threads_json" || fail "Created thread $tid not in list"
done

log "Summary: ${#USER_IDS[@]} users ensured, ${#created_thread_ids[@]} threads created, ${#created_message_ids[@]} messages created"
log "Smoke test PASSED"
exit 0