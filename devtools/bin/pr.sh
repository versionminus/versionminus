#!/bin/bash
# ./bin/pr.sh "Your PR Title"
# pr "Your PR Title"
set -e  # Exit on any error

# Accept PR title either as first arg or PR_TITLE env var (Makefile passes arg)
if [ -n "$1" ]; then
    PR_TITLE="$1"
fi

if [ -z "$PR_TITLE" ]; then
    echo "Error: PR title is required"
    echo "Usage: $0 <pr-title> or set PR_TITLE environment variable"
    exit 1
fi

PR_BODY=${PR_BODY:-"[licodex] Automated PR"}
CURRENT_BRANCH=$(git branch --show-current)

# Check if we're on dev branch
if [ "$CURRENT_BRANCH" = "dev" ]; then
    echo "Error: Cannot create PR from dev branch"
    exit 1
fi

# Check if gh CLI is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "Error: GitHub CLI is not authenticated"
    echo "Please run: gh auth login"
    exit 1
fi


echo "Creating PR from branch '$CURRENT_BRANCH' to dev..."

CREATE_ARGS=(--title "$PR_TITLE" --base dev --head "$CURRENT_BRANCH" --body "$PR_BODY")

if [ -n "$PR_DRAFT" ]; then
    CREATE_ARGS+=(--draft)
fi

gh pr create "${CREATE_ARGS[@]}" || {
    echo "gh pr create failed (maybe PR already exists). Attempting to show existing..." >&2
    gh pr view --web || true
    exit 1
}

echo "PR created. Leaving it open for review."
echo "Set PR_AUTO_MERGE=1 to auto-merge once checks pass (rebase strategy)."

if [ "$PR_AUTO_MERGE" = "1" ]; then
    PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --json number --jq '.[0].number')
    if [ -n "$PR_NUMBER" ]; then
        echo "Enabling auto-merge for PR #$PR_NUMBER (rebase)..."
        gh pr merge "$PR_NUMBER" --rebase --auto || echo "Auto-merge enabling failed (maybe requirements not met)."
    fi
fi

echo "✅"

if [ "$PR_CLOSE" = "1" ]; then
    echo "PR_CLOSE=1 set; closing PR and cleaning up branch..."
    PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --json number --jq '.[0].number')
    if [ -z "$PR_NUMBER" ]; then
            echo "Error: Could not find PR number to close"
            exit 1
    fi
    echo "Closing PR #$PR_NUMBER..."
    gh pr close "$PR_NUMBER" --comment "Auto-closed by pr.sh script" --delete-branch=false
    echo "PR closed successfully"
    echo "Checking out dev and deleting branch..."
    git checkout dev
    git pull origin dev
    git branch -D "$CURRENT_BRANCH" || true
    git push origin --delete "$CURRENT_BRANCH" || true
    echo "✅"
fi
