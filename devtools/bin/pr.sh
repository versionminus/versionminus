#!/bin/bash
# ./bin/pr.sh "Your PR Title"
# pr "Your PR Title"
set -e  # Exit on any error

# Check if title parameter is provided
if [ -z "$1" ]; then
    echo "Error: PR title is required"
    echo "Usage: $0 <pr-title>"
    exit 1
fi

PR_TITLE="$1"
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

# Create PR with merge commit strategy
gh pr create \
    --title "[merge-commit] $PR_TITLE" \
    --base dev \
    --head "$CURRENT_BRANCH" \
    --body "[licodex] Automated PR" \
    --merge

echo "PR created successfully"

# Get the PR number for closing it
PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --json number --jq '.[0].number')

if [ -z "$PR_NUMBER" ]; then
    echo "Error: Could not find PR number"
    exit 1
fi

echo "Closing PR #$PR_NUMBER..."

# Close the PR with admin privileges
gh pr close "$PR_NUMBER" --comment "Auto-closed by pr.sh script" --delete-branch=false

echo "PR closed successfully"

# Checkout to dev branch
echo "Checking out to dev branch..."
git checkout dev

# Pull latest changes from dev
echo "Pulling latest changes from dev..."
git pull origin dev

# Delete the feature branch locally
echo "Deleting local branch '$CURRENT_BRANCH'..."
git branch -D "$CURRENT_BRANCH"

# Delete the feature branch remotely
echo "Deleting remote branch '$CURRENT_BRANCH'..."
git push origin --delete "$CURRENT_BRANCH"

echo "✅"
