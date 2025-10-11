#!/usr/bin/env bash
set -euo pipefail

# Smoke test against a running instance (default: http://localhost:8000)
# Validates:
#  - health & root endpoints
#  - ensure specific users exist (idempotent): diogo, nuno, shan
#  - for each user: create several unique threads
#  - for each thread: create several messages
#  - basic verification of creations

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_PREFIX="${API_PREFIX:-/api/v1}"
HELPER="$(dirname "$0")/smoke_helpers.py"

# Flags (default: no cleaning before or after)
CLEAN_BEFORE=0
CLEAN_AFTER=0

usage() {
  cat <<USAGE
Usage: $0 [--clean-before] [--clean-after]

Options:
  --clean-before   Delete existing smoke resources (test users, their threads & messages) before running
  --clean-after    Delete smoke resources after successful run
  -h, --help       Show this help

Environment overrides:
  BASE_URL, API_PREFIX, THREADS_PER_USER, MESSAGES_PER_THREAD
  FORCED_USER_IDS   Comma-separated list mapping emails to fixed IDs. Example:
                    FORCED_USER_IDS="diogo@licodex.com=ad66a062-fda4-41e5-8d4e-f260965dc4f4,nuno@licodex.com=11111111-2222-3333-4444-555555555555"
                    If provided, the script will attempt to create users with these IDs (by sending id in POST).
                    If the API rejects custom IDs and a user already exists (409), the existing ID MUST match the forced one or the script fails.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean-before) CLEAN_BEFORE=1 ;;
    --clean-after) CLEAN_AFTER=1 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done

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

THREADS_PER_USER=${THREADS_PER_USER:-0}
# Messages creation disabled per request; retain variable for backward compatibility if externally referenced
MESSAGES_PER_THREAD=${MESSAGES_PER_THREAD:-0}

USERS=(
  "diogo@licodex.com"
)

FORCED_USER_IDS="diogo@licodex.com=ad66a062-fda4-41e5-8d4e-f260965dc4f4"

# Optional forced user IDs (email -> id) provided via FORCED_USER_IDS env var
# Format: email1=id1,email2=id2
declare -A FORCED_IDS
if [[ -n "${FORCED_USER_IDS:-}" ]]; then
  IFS=',' read -r -a __forced_pairs <<<"$FORCED_USER_IDS"
  for __pair in "${__forced_pairs[@]}"; do
    [[ -z "$__pair" ]] && continue
    if [[ "$__pair" =~ ^([^=]+)=(.+)$ ]]; then
      __f_email="${BASH_REMATCH[1]}"
      __f_id="${BASH_REMATCH[2]}"
      FORCED_IDS["$__f_email"]="$__f_id"
    else
      log "Ignoring malformed FORCED_USER_IDS entry: $__pair"
    fi
  done
  log "Forced user IDs active for: ${!FORCED_IDS[*]}"
fi

declare -A USER_IDS

########################################
# Cleanup logic
########################################
clean_smoke_resources() {
  log "Cleaning existing smoke resources (users: ${USERS[*]})"
  # Fetch users and build map email->id for target emails
  local users_json
  if ! users_json=$(curl_json GET "${API_PREFIX}/users/"); then
    log "Could not list users during cleanup; skipping"; return 0
  fi
  # Extract ids via python helper for reliability
  mapfile -t existing_ids < <(printf '%s' "$users_json" | /usr/bin/env python3 "$HELPER" users-filter --emails "${USERS[@]}")
  declare -A email_to_id
  for line in "${existing_ids[@]}"; do
    [[ -z "$line" ]] && continue
    email_to_id["${line%%$'\t'*}"]="${line#*$'\t'}"
  done
  # If none, nothing to do
  local any=0
  for e in "${USERS[@]}"; do
    if [[ -n "${email_to_id[$e]:-}" ]]; then any=1; fi
  done
  if [[ $any -eq 0 ]]; then
    log "No target users present; nothing to clean"
    return 0
  fi
  # List threads to find those belonging to target users
  local threads_json
  if ! threads_json=$(curl_json GET "${API_PREFIX}/threads/"); then
    log "Could not list threads; aborting cleanup"; return 0
  fi
  # For each thread owned by target user, collect thread_id and then list messages
  # shellcheck disable=SC2068 # we intentionally expand to multiple args
  mapfile -t target_threads < <(printf '%s' "$threads_json" | /usr/bin/env python3 "$HELPER" threads-filter --user-ids ${email_to_id[@]})
  local deleted_messages=0 deleted_threads=0 deleted_users=0
  for tt in "${target_threads[@]}"; do
    [[ -z "$tt" ]] && continue
    local thread_id="${tt%%$'\t'*}"
    # List messages for thread
    local msgs_json
    if msgs_json=$(curl -sS -X GET --fail "${BASE_URL}${API_PREFIX}/messages/thread/$thread_id" || true); then
      mapfile -t msg_ids < <(printf '%s' "$msgs_json" | /usr/bin/env python3 "$HELPER" message-ids)
      for mid in "${msg_ids[@]}"; do
        [[ -z "$mid" ]] && continue
        curl -sS -X DELETE "${BASE_URL}${API_PREFIX}/messages/$mid" -o /dev/null || true
        ((deleted_messages++)) || true
      done
    fi
    # Delete thread
    curl -sS -X DELETE "${BASE_URL}${API_PREFIX}/threads/$thread_id" -o /dev/null || true
    ((deleted_threads++)) || true
  done
  # Delete users last
  for e in "${USERS[@]}"; do
    uid="${email_to_id[$e]:-}"
    [[ -z "$uid" ]] && continue
    curl -sS -X DELETE "${BASE_URL}${API_PREFIX}/users/$uid" -o /dev/null || true
    ((deleted_users++)) || true
  done
  log "Cleanup removed: $deleted_messages messages, $deleted_threads threads, $deleted_users users"
}

if [[ $CLEAN_BEFORE -eq 1 ]]; then
  clean_smoke_resources || true
fi

log "Ensuring users exist (${USERS[*]})"
for email in "${USERS[@]}"; do
  desired_id="${FORCED_IDS[$email]:-}"
  if [[ -n "$desired_id" ]]; then
    log "Attempting creation with forced id for $email: $desired_id"
    payload="{\"id\":\"$desired_id\",\"email\":\"$email\",\"role\":\"user\"}"
  else
    payload="{\"email\":\"$email\",\"role\":\"user\"}"
  fi

  curl_json_status POST "${API_PREFIX}/users/" "$payload"
  body="$CURL_BODY"
  status="$CURL_STATUS"

  # If we tried with forced id and got an unexpected error (not 201/409), retry without id once
  if [[ -n "$desired_id" && "$status" != "201" && "$status" != "409" ]]; then
    log "Create with explicit id returned $status. Retrying without id for $email (API may not allow client-specified IDs)."
    curl_json_status POST "${API_PREFIX}/users/" "{\"email\":\"$email\",\"role\":\"user\"}"
    body="$CURL_BODY"
    status="$CURL_STATUS"
  fi

  if [[ "$status" == "201" ]]; then
    user_id=$(sed -n 's/.*"id":"\([^" ]*\)".*/\1/p' <<<"$body")
    [[ -n "$user_id" ]] || fail "Could not parse new user id for $email"
    if [[ -n "$desired_id" && "$user_id" != "$desired_id" ]]; then
      fail "Forced id mismatch for $email: expected $desired_id got $user_id"
    fi
    log "Created user $email ($user_id)"
  elif [[ "$status" == "409" ]]; then
    # Already exists: fetch list and extract id via Python for robustness
    users_json=$(curl_json GET "${API_PREFIX}/users/") || fail "list users failed while resolving existing user $email"
    user_id=$(printf '%s' "$users_json" | /usr/bin/env python3 "$HELPER" user-id --email "$email")
    [[ -n "$user_id" ]] || fail "Could not resolve existing user id for $email"
    if [[ -n "$desired_id" && "$user_id" != "$desired_id" ]]; then
      fail "Existing user id for $email ($user_id) does not match forced id $desired_id"
    fi
    log "User already existed $email ($user_id)"
  else
    fail "Unexpected status creating user $email: $status ($body)"
  fi
  USER_IDS[$email]="$user_id"
done

created_thread_ids=()

for email in "${USERS[@]}"; do
  user_id=${USER_IDS[$email]}
  log "Creating threads for $email (user_id=$user_id)"
  for ((t=1; t<=THREADS_PER_USER; t++)); do
    thread_title="${t}-$(echo "$email" | tr '@.' '--')"
    thread_json=$(curl_json POST "${API_PREFIX}/threads/" "{\"title\":\"$thread_title\",\"user_id\":\"$user_id\"}") || fail "thread create failed for $email"
    thread_id=$(sed -n 's/.*"id":"\([^"]*\)".*/\1/p' <<<"$thread_json")
    [[ -n "$thread_id" ]] || fail "Could not extract thread id ($email t=$t)"
    created_thread_ids+=("$thread_id")
    grep -q "$thread_title" <<<"$thread_json" || fail "Thread title mismatch ($thread_title)"
    log "  Created thread $thread_title ($thread_id)"

    # Message creation intentionally skipped
    log "  (message creation skipped)"
  done
done

# Final verification: list threads and ensure each created thread appears
threads_json=$(curl_json GET "${API_PREFIX}/threads/") || fail "list threads failed"
for tid in "${created_thread_ids[@]}"; do
  grep -q "$tid" <<<"$threads_json" || fail "Created thread $tid not in list"
done

log "Summary: ${#USER_IDS[@]} users ensured, ${#created_thread_ids[@]} threads created (message creation skipped)"
if [[ $CLEAN_AFTER -eq 1 ]]; then
  clean_smoke_resources || true
  log "Post-run cleanup complete"
fi
log "Smoke test PASSED"
exit 0