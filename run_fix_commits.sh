#!/bin/bash
# Run this script in Git Bash to fix broken Korean commit messages

cd "$(dirname "$0")"

echo "========================================"
echo "Fix Broken Korean Commit Messages"
echo "========================================"
echo ""

# Check if msg_filter.sh exists
if [ ! -f "msg_filter.sh" ]; then
    echo "Error: msg_filter.sh not found"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: You have uncommitted changes."
    echo "Please commit or stash them before proceeding."
    exit 1
fi

echo "This will rewrite Git history to fix broken Korean commit messages."
echo ""
echo "WARNING: This will rewrite history. Make sure:"
echo "  - No one else is working on this branch"
echo "  - You have a backup"
echo "  - You understand the implications"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

export FILTER_BRANCH_SQUELCH_WARNING=1

echo ""
echo "Starting filter-branch..."
echo ""

git filter-branch -f --msg-filter 'bash msg_filter.sh' HEAD~35..HEAD

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Success! Commit messages have been fixed."
    echo "========================================"
    echo ""
    echo "To push the changes:"
    echo "  git push --force-with-lease origin main"
    echo ""
    echo "To verify the changes:"
    echo "  git log --oneline -35"
else
    echo ""
    echo "Error: filter-branch failed"
    echo "You may need to clean up:"
    echo "  git filter-branch --abort"
    exit 1
fi

