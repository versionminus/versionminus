#!/usr/bin/env python3
"""Helper subcommands for the smoke test script.

Reads JSON from stdin (expected to be arrays of objects) and emits simple
text outputs used by the surrounding bash script, replacing brittle inline
python one-liners.

Subcommands:
  users-filter   -> filter users by email; prints "<email>\t<id>" per match
  user-id        -> extract a single user id by email; prints id (or empty)
  threads-filter -> filter threads by owner user ids; prints "<id>\t<user_id>"
  message-ids    -> list message ids in a thread message list; prints each id

All commands ignore JSON parsing errors by treating input as empty list.
Exit codes:
  0 success (even if no matches)
  2 usage / argument errors

"""
from __future__ import annotations
import sys
import json
import argparse
from typing import List, Any


def load_stdin_list() -> List[Any]:
    data = sys.stdin.read()
    if not data.strip():
        return []
    try:
        parsed = json.loads(data)
    except Exception:
        return []
    if isinstance(parsed, list):
        return parsed
    # Some endpoints might return an object (unexpected here); treat as empty.
    return []


def cmd_users_filter(args: argparse.Namespace) -> int:
    items = load_stdin_list()
    targets = set(args.emails)
    for u in items:
        try:
            email = u.get("email")
            if email in targets:
                uid = u.get("id", "")
                if uid:
                    print(f"{email}\t{uid}")
        except AttributeError:
            continue
    return 0


def cmd_user_id(args: argparse.Namespace) -> int:
    items = load_stdin_list()
    email = args.email
    for u in items:
        if isinstance(u, dict) and u.get("email") == email:
            uid = u.get("id", "")
            if uid:
                print(uid)
            return 0
    # no match prints nothing
    return 0


def cmd_threads_filter(args: argparse.Namespace) -> int:
    items = load_stdin_list()
    targets = set(args.user_ids)
    for t in items:
        if not isinstance(t, dict):
            continue
        user_id = t.get("user_id")
        if user_id is None:
            continue
        if str(user_id) in targets:
            tid = t.get("id")
            if tid:
                print(f"{tid}\t{user_id}")
    return 0


def cmd_message_ids(args: argparse.Namespace) -> int:
    items = load_stdin_list()
    for m in items:
        if isinstance(m, dict):
            mid = m.get("id")
            if mid:
                print(mid)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="smoke_helpers",
        description="Helpers for smoke.sh (JSON filtering)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_users = sub.add_parser("users-filter", help="Filter users by email")
    p_users.add_argument("--emails", nargs="+", required=True, help="Emails to match")
    p_users.set_defaults(func=cmd_users_filter)

    p_user_id = sub.add_parser("user-id", help="Extract a single user id by email")
    p_user_id.add_argument("--email", required=True)
    p_user_id.set_defaults(func=cmd_user_id)

    p_threads = sub.add_parser("threads-filter", help="Filter threads by user ids")
    p_threads.add_argument("--user-ids", nargs="+", required=True)
    p_threads.set_defaults(func=cmd_threads_filter)

    p_msgs = sub.add_parser("message-ids", help="List message ids from messages JSON")
    p_msgs.set_defaults(func=cmd_message_ids)

    return p


def main(argv: List[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
