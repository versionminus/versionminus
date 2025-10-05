#!/usr/bin/env bash
set -euo pipefail

# Embedding smoke test (no mocks):
#  1. Health + embeddings/health checks
#  2. Create unique user
#  3. Create a note for that user
#  4. Embed the note (real embedding model + Milvus upsert)
#  5. Verify the note is flagged embedded in DB
#  6. Perform semantic search and assert the note appears in top results
#
# Requirements (must be set in the running API environment):
#   - MODELHUB_API_KEY, MODELHUB_BASE_URL (so embeddings model client is configured)
#   - Milvus running with a 'notes' collection already created
#
# Environment overrides:
#   BASE_URL (default http://licodex-api:8000)
#   API_PREFIX (default /api/v1)
#   EMBEDDING_MODEL (default text-embedding-ada-002)
#   SEARCH_TOP_K (default 5)
#
# Flags:
#   --clean-before   Remove any existing prior smoke embed user (by timestamp token) before run
#   --clean-after    Delete user & note created by this script after successful run
#
# Exit codes: 0 success; non-zero on first failure

BASE_URL="${BASE_URL:-http://licodex-api:8000}"
API_PREFIX="${API_PREFIX:-/api/v1}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-text-embedding-ada-002}"  # keep in sync with config default
SEARCH_TOP_K="${SEARCH_TOP_K:-5}"

CLEAN_BEFORE=0
CLEAN_AFTER=0

log() { printf '[smoke-embed] %s\n' "$*"; }
fail() { echo "[smoke-embed][ERROR] $*" >&2; exit 1; }

curl_json() {
  local method="$1"; shift
  local path="$1"; shift
  local data="${1:-}"
  if [[ -n "$data" ]]; then
    curl -sS -X "$method" -H 'Content-Type: application/json' --fail "${BASE_URL}${path}" -d "$data"
  else
    curl -sS -X "$method" --fail "${BASE_URL}${path}"
  fi
}

curl_json_status() {
  local method="$1"; shift
  local path="$1"; shift
  local data="${1:-}"
  local tmp http
  tmp="$(mktemp)"
  if [[ -n "$data" ]]; then
    http=$(curl -sS -o "$tmp" -w '%{http_code}' -X "$method" -H 'Content-Type: application/json' "${BASE_URL}${path}" -d "$data" || true)
  else
    http=$(curl -sS -o "$tmp" -w '%{http_code}' -X "$method" "${BASE_URL}${path}" || true)
  fi
  CURL_BODY="$(cat "$tmp")"
  CURL_STATUS="$http"
  rm -f "$tmp"
}

usage() {
  cat <<USAGE
Embedding smoke test (no mocks). Ensures end-to-end embedding + search works.

Usage: $0 [--clean-before] [--clean-after] [-h|--help]

Options:
  --clean-before   Attempt to remove leftover previous smoke embed user/note (best-effort)
  --clean-after    Delete created user & note after success
  -h, --help       Show this help

Environment variables:
  BASE_URL, API_PREFIX, EMBEDDING_MODEL, SEARCH_TOP_K
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

########################################
# Cleanup helpers (best-effort, idempotent)
########################################
cleanup_user_and_notes() {
  local token="$1"  # timestamp token used in email pattern embed-<token>@
  local users_json user_id
  if ! users_json=$(curl -sS --fail "${BASE_URL}${API_PREFIX}/users/" 2>/dev/null); then
    log "Skip cleanup: list users failed"; return 0
  fi
  # Extract first user whose email contains token
  user_id=$(sed -n "s/.*{\\\"id\\\":\\\"\\([^\\\"]*\\)\\\",\\\"email\\\":\\\"embed-${token}@licodex.com\\\".*/\\1/p" <<<"$users_json" | head -n1 || true)
  if [[ -z "$user_id" ]]; then
    # fallback: any email containing token
    user_id=$(sed -n "s/.*{\\\"id\\\":\\\"\\([^\\\"]*\\)\\\",\\\"email\\\":\\\"[^\\\"]*${token}[^\\\"]*\\\".*/\\1/p" <<<"$users_json" | head -n1 || true)
  fi
  [[ -z "$user_id" ]] && { log "No prior smoke embed user found for token $token"; return 0; }
  log "Cleaning user $user_id (token=$token)"
  # Delete notes belonging to user (iterate list notes)
  local notes_json
  if notes_json=$(curl -sS --fail "${BASE_URL}${API_PREFIX}/notes/" 2>/dev/null); then
    note_ids=()
    tmp_notes=$(mktemp)
    printf '%s' "$notes_json" > "$tmp_notes"
    while IFS= read -r nid; do
      [[ -n "$nid" ]] && note_ids+=("$nid")
    done < <(python3 - "$user_id" "$tmp_notes" <<'PY'
import json,sys,os
uid=sys.argv[1]
path=sys.argv[2]
try:
  with open(path,'r',encoding='utf-8') as f:
    data=json.load(f)
except Exception:
  data=[]
for n in data:
  if isinstance(n, dict) and n.get('user_id')==uid:
    print(n.get('id'))
PY
    )
    rm -f "$tmp_notes"
    for nid in "${note_ids[@]}"; do
      [[ -z "$nid" ]] && continue
      curl -sS -X DELETE "${BASE_URL}${API_PREFIX}/notes/$nid" -o /dev/null || true
    done
  fi
  curl -sS -X DELETE "${BASE_URL}${API_PREFIX}/users/$user_id" -o /dev/null || true
  log "Cleanup complete for user $user_id"
}

log "Health: liveness"
live_json=$(curl_json GET "${API_PREFIX}/health/liveness") || fail "liveness failed"
grep -q '"status":"ok"' <<<"$live_json" || fail "liveness status not ok"

log "Health: embeddings/health"
emb_health=$(curl_json GET "${API_PREFIX}/embeddings/health") || fail "embeddings health failed"
grep -q '"ready":true' <<<"$emb_health" || log "WARNING: embeddings health not ready (continuing)"

timestamp=$(date +%s%N)
if [[ $CLEAN_BEFORE -eq 1 ]]; then
  cleanup_user_and_notes "$timestamp" || true
fi
email="charlotte@licodex.com"
note_token="EMBEDTEST-${timestamp}"
note_content="This is an embedding smoke test note containing token '${note_token}' to validate vector search retrieval. Search for token ${note_token} to find this note."

log "Create user $email"
user_payload=$(printf '{"email":"%s","role":"user"}' "$email")
curl_json_status POST "${API_PREFIX}/users/" "$user_payload"
[[ "$CURL_STATUS" == "201" ]] || fail "user create failed: $CURL_STATUS $CURL_BODY"
user_id=$(sed -n 's/.*"id":"\([^"]*\)".*/\1/p' <<<"$CURL_BODY")
[[ -n "$user_id" ]] || fail "Could not parse user id"
log "User id: $user_id"

log "Create note"
safe_note_content=${note_content//"/\\"}
note_payload=$(printf '{"user_id":"%s","content":"%s"}' "$user_id" "$safe_note_content")
curl_json_status POST "${API_PREFIX}/notes/" "$note_payload"
[[ "$CURL_STATUS" == "201" ]] || fail "note create failed: $CURL_STATUS $CURL_BODY"
note_id=$(sed -n 's/.*"id":"\([^"]*\)".*/\1/p' <<<"$CURL_BODY")
[[ -n "$note_id" ]] || fail "Could not parse note id"
log "Note id: $note_id"

log "Embed note (model=$EMBEDDING_MODEL)"
embed_payload=$(printf '{"model":"%s","input":["%s"],"collection":"notes","note_ids":["%s"],"user_ids":["%s"],"upsert":true}' "$EMBEDDING_MODEL" "$safe_note_content" "$note_id" "$user_id")
curl_json_status POST "${API_PREFIX}/embeddings/" "$embed_payload"
[[ "$CURL_STATUS" == "200" ]] || fail "embedding request failed: $CURL_STATUS $CURL_BODY"
grep -q '"count":1' <<<"$CURL_BODY" || log "WARNING: embed response did not show count=1 (body=$CURL_BODY)"

log "Verify note embedded flag"
note_get=$(curl_json GET "${API_PREFIX}/notes/$note_id") || fail "fetch note failed"
grep -q '"embedded":true' <<<"$note_get" || fail "note not marked embedded"

log "Search for token via embeddings/search"
search_payload=$(printf '{"collection":"notes","query":"%s","top_k":%s}' "$note_token" "$SEARCH_TOP_K")
curl_json_status POST "${API_PREFIX}/embeddings/search" "$search_payload"
[[ "$CURL_STATUS" == "200" ]] || fail "search request failed: $CURL_STATUS $CURL_BODY"
grep -q "$note_id" <<<"$CURL_BODY" || fail "search results missing note_id ($note_id)"
log "Search returned note successfully"

log "Embedding smoke test PASS (user=$user_id note=$note_id)"
if [[ $CLEAN_AFTER -eq 1 ]]; then
  cleanup_user_and_notes "$timestamp" || true
  log "Post-run cleanup finished"
fi
exit 0
