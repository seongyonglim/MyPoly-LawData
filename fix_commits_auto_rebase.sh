#!/bin/bash
# Auto-fix commit messages using git rebase
# This script creates a rebase todo file automatically

# Set encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Commits to fix (short hash -> English message)
declare -A COMMIT_FIXES=(
    ["8dd146d"]="Add final cleanup verification report"
    ["76dfecc"]="Add final cleanup summary document"
    ["4e481ae"]="Add final file cleanup verification report"
    ["3c4393e"]="Add final file cleanup analysis and completion report"
    ["a855e44"]="Remove unnecessary CSV and SQL files (migration completed)"
    ["b03ca7b"]="Add file cleanup and cleanup report"
    ["e26c9d8"]="Create cloud migration document and remove unnecessary files"
    ["60f8539"]="Add VM setup and startup guide"
    ["0253e9a"]="Add migration method using Cloud SQL public IP directly"
    ["1197020"]="Add migration method via SSH tunnel"
    ["8b5e76d"]="Add local PostgreSQL setup script and VM migration guide"
    ["f50e147"]="Add final migration method from local DB via VM"
    ["73ea1b9"]="Add SQL file import guide"
    ["b44ad5b"]="Add script to create SQL dump via console"
    ["d7f83b3"]="Update SSH tunnel migration guide"
    ["3220fff"]="Add manual CSV import guide"
    ["ae309ca"]="Add migration method via SSH tunnel for batch"
    ["46ca67c"]="Fix CSV import script None value handling"
    ["36cbf34"]="Add CSV import script using Python (encoding issue fixed)"
    ["4e8e21c"]="Add CSV batch import script (encoding issue fixed)"
    ["92992b6"]="Fix CSV file generation (Out-File encoding issue fixed)"
    ["91d461f"]="Fix CSV file generation (explicit columns, UTF-8)"
    ["e51ba63"]="Add CSV encoding fix script"
    ["8739dc0"]="Add CSV batch file (temporary)"
    ["807a371"]="Add CSV import script"
    ["d47a280"]="Add migration method via VM for batch"
    ["5d8734a"]="Add local batch migration guide"
    ["ff567c4"]="Add Cloud SQL table creation script"
    ["24dbab7"]="Add Cloud SQL Admin API setup guide"
    ["fe27f92"]="Add GCP setup guide from console"
    ["3c5e21e"]="Add Cloud SQL Proxy connection timeout fix guide"
    ["3f18988"]="Add GCP VM initial setup script"
    ["b2a6279"]="Add GCP initial setup: Cloud SQL, VM setup, initial setup scripts"
)

echo "========================================"
echo "Auto-fix Broken Korean Commit Messages"
echo "========================================"
echo ""
echo "Found ${#COMMIT_FIXES[@]} commits to fix"
echo ""

# Get recent commits
echo "Getting recent commits..."
git log --format="%h|%s" -35 > /tmp/commits_list.txt

# Create rebase todo file
echo "Creating rebase todo file..."
cat > /tmp/rebase_todo.txt << 'EOF'
# Rebase todo - change pick to reword for commits that need fixing
EOF

# Process each commit
while IFS='|' read -r hash msg; do
    if [[ -n "${COMMIT_FIXES[$hash]}" ]]; then
        echo "reword $hash ${COMMIT_FIXES[$hash]}" >> /tmp/rebase_todo.txt
        echo "  - $hash: ${COMMIT_FIXES[$hash]}"
    else
        echo "pick $hash $msg" >> /tmp/rebase_todo.txt
    fi
done < /tmp/commits_list.txt

echo ""
echo "Rebase todo file created: /tmp/rebase_todo.txt"
echo ""
echo "To apply fixes:"
echo "1. Review /tmp/rebase_todo.txt"
echo "2. Run: GIT_SEQUENCE_EDITOR='cat /tmp/rebase_todo.txt' git rebase -i HEAD~35"
echo ""
echo "Or manually:"
echo "  git rebase -i HEAD~35"
echo "  (Change 'pick' to 'reword' for each commit above)"
echo ""

