#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automatically fix broken Korean commit messages
This script creates a rebase todo file and applies fixes
"""

import subprocess
import sys
import os
import tempfile

# Map of short commit hashes to new English messages
COMMIT_FIXES = {
    "8dd146d": "Add final cleanup verification report",
    "76dfecc": "Add final cleanup summary document",
    "4e481ae": "Add final file cleanup verification report",
    "3c4393e": "Add final file cleanup analysis and completion report",
    "a855e44": "Remove unnecessary CSV and SQL files (migration completed)",
    "b03ca7b": "Add file cleanup and cleanup report",
    "e26c9d8": "Create cloud migration document and remove unnecessary files",
    "60f8539": "Add VM setup and startup guide",
    "0253e9a": "Add migration method using Cloud SQL public IP directly",
    "1197020": "Add migration method via SSH tunnel",
    "8b5e76d": "Add local PostgreSQL setup script and VM migration guide",
    "f50e147": "Add final migration method from local DB via VM",
    "73ea1b9": "Add SQL file import guide",
    "b44ad5b": "Add script to create SQL dump via console",
    "d7f83b3": "Update SSH tunnel migration guide",
    "3220fff": "Add manual CSV import guide",
    "ae309ca": "Add migration method via SSH tunnel for batch",
    "46ca67c": "Fix CSV import script None value handling",
    "36cbf34": "Add CSV import script using Python (encoding issue fixed)",
    "4e8e21c": "Add CSV batch import script (encoding issue fixed)",
    "92992b6": "Fix CSV file generation (Out-File encoding issue fixed)",
    "91d461f": "Fix CSV file generation (explicit columns, UTF-8)",
    "e51ba63": "Add CSV encoding fix script",
    "8739dc0": "Add CSV batch file (temporary)",
    "807a371": "Add CSV import script",
    "d47a280": "Add migration method via VM for batch",
    "5d8734a": "Add local batch migration guide",
    "ff567c4": "Add Cloud SQL table creation script",
    "24dbab7": "Add Cloud SQL Admin API setup guide",
    "fe27f92": "Add GCP setup guide from console",
    "3c5e21e": "Add Cloud SQL Proxy connection timeout fix guide",
    "3f18988": "Add GCP VM initial setup script",
    "b2a6279": "Add GCP initial setup: Cloud SQL, VM setup, initial setup scripts",
}

def get_commit_list(count=35):
    """Get list of recent commits"""
    result = subprocess.run(
        ["git", "log", "--format=%H|%s", f"-{count}"],
        capture_output=True,
        text=True,
        check=True
    )
    commits = []
    for line in result.stdout.strip().split('\n'):
        if '|' in line:
            hash_full, msg = line.split('|', 1)
            hash_short = hash_full[:7]
            commits.append((hash_short, hash_full, msg))
    return commits

def create_rebase_todo(commits):
    """Create rebase todo file"""
    todo_lines = []
    for hash_short, hash_full, msg in commits:
        if hash_short in COMMIT_FIXES:
            todo_lines.append(f"reword {hash_short} {COMMIT_FIXES[hash_short]}")
        else:
            todo_lines.append(f"pick {hash_short} {msg}")
    return '\n'.join(todo_lines)

def main():
    print("=" * 60)
    print("Auto-fix Broken Korean Commit Messages")
    print("=" * 60)
    
    # Get recent commits
    print("\n[1] Getting recent commits...")
    commits = get_commit_list(35)
    print(f"   Found {len(commits)} commits")
    
    # Count commits to fix
    to_fix = [c for c in commits if c[0] in COMMIT_FIXES]
    print(f"   {len(to_fix)} commits need fixing")
    
    if not to_fix:
        print("\n✅ No commits to fix!")
        return
    
    print("\n[2] Commits to fix:")
    for hash_short, _, _ in to_fix:
        print(f"   - {hash_short}: {COMMIT_FIXES[hash_short]}")
    
    print("\n" + "=" * 60)
    print("⚠️  WARNING: This will rewrite Git history!")
    print("=" * 60)
    print("\nTo fix these commits manually:")
    print("1. Run: git rebase -i HEAD~35")
    print("2. Change 'pick' to 'reword' for each commit above")
    print("3. Enter the English message when prompted")
    print("4. After rebase: git push --force-with-lease origin main")
    print("\nOr use the provided COMMIT_MESSAGE_FIXES.md as reference.")

if __name__ == "__main__":
    main()

