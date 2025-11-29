# Commit Message Fix Guide

## Problem

Many commit messages written in Korean are showing as garbled text in Git history due to encoding issues in PowerShell.

## Solution

We need to rewrite the commit messages in English using `git rebase -i`.

## Steps

### 1. Identify Broken Commits

Run this to see all commits with Korean characters:
```powershell
git log --oneline -50 | Select-String -Pattern "[\uAC00-\uD7A3]"
```

### 2. Interactive Rebase

Run:
```bash
git rebase -i HEAD~33
```

This will open an editor with the last 33 commits. For each commit with a broken message:

1. Change `pick` to `reword` (or `r`)
2. Save and close
3. When the commit message editor opens, replace with the English version
4. Save and close
5. Repeat for each commit

### 3. Force Push

After rebase completes:
```bash
git push --force-with-lease origin main
```

**⚠️ Warning**: This rewrites history. Make sure:
- No one else is working on this branch
- You have backups
- You understand the implications

## Alternative: Automated Script

If you have many commits to fix, you can use a script. However, this requires careful handling and may not work in all environments.

## Reference

See `COMMIT_MESSAGE_FIXES.md` for the complete list of commit hash → English message mappings.

