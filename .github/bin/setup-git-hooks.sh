#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

hook_dir="$repo_root/.githooks"

if [ ! -d "$hook_dir" ]; then
    echo "Git hooks directory '$hook_dir' is missing." >&2
    exit 1
fi

git config core.hooksPath ".githooks"

# Ensure every hook is executable
if command -v find >/dev/null 2>&1; then
    find "$hook_dir" -type f -exec chmod +x {} +
else
    chmod +x "$hook_dir"/*
fi

echo "Git hooks configured to use $hook_dir"

