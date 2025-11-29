#!/bin/bash
# Fix remaining broken Korean commit messages

cd "$(dirname "$0")"

export FILTER_BRANCH_SQUELCH_WARNING=1

echo "Fixing remaining broken commit messages..."

git filter-branch -f --msg-filter '
case "$GIT_COMMIT" in
    24dbab71edc61fd066594c88f5bf2d72f3e32b73)
        echo "Add Cloud SQL Admin API setup guide"
        ;;
    fe27f926fe2546c33a0da84bfa56814022d3d028)
        echo "Add GCP setup guide from console"
        ;;
    3c5e21e768303c872cc41e28541394ffb079a0bc)
        echo "Add Cloud SQL Proxy connection timeout fix guide"
        ;;
    3f18988c30d9a16b070dfc1ae1f57a7ab416b13f)
        echo "Add GCP VM initial setup script"
        ;;
    b2a627952504e0548aa164394fa9b859877d2587)
        echo "Add GCP initial setup: Cloud SQL, VM setup, initial setup scripts"
        ;;
    *)
        cat
        ;;
esac
' 24dbab7^..HEAD

if [ $? -eq 0 ]; then
    echo ""
    echo "Success! Remaining commit messages have been fixed."
    echo ""
    echo "To push the changes:"
    echo "  git push --force-with-lease origin main"
else
    echo ""
    echo "Error: filter-branch failed"
    exit 1
fi

