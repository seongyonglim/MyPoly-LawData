# Commit Message Fixes

This document lists all commits with broken Korean messages and their English replacements.

## Instructions

To fix these commits, you need to use `git rebase -i` and change `pick` to `reword` for each commit, then enter the new message when prompted.

Alternatively, use the provided script or manually edit each commit.

## Commit Fixes

1. `8dd146d` → "Add final cleanup verification report"
2. `76dfecc` → "Add final cleanup summary document"
3. `4e481ae` → "Add final file cleanup verification report"
4. `3c4393e` → "Add final file cleanup analysis and completion report"
5. `a855e44` → "Remove unnecessary CSV and SQL files (migration completed)"
6. `b03ca7b` → "Add file cleanup and cleanup report"
7. `e26c9d8` → "Create cloud migration document and remove unnecessary files"
8. `60f8539` → "Add VM setup and startup guide"
9. `0253e9a` → "Add migration method using Cloud SQL public IP directly"
10. `1197020` → "Add migration method via SSH tunnel"
11. `8b5e76d` → "Add local PostgreSQL setup script and VM migration guide"
12. `f50e147` → "Add final migration method from local DB via VM"
13. `73ea1b9` → "Add SQL file import guide"
14. `b44ad5b` → "Add script to create SQL dump via console"
15. `d7f83b3` → "Update SSH tunnel migration guide"
16. `3220fff` → "Add manual CSV import guide"
17. `ae309ca` → "Add migration method via SSH tunnel for batch"
18. `46ca67c` → "Fix CSV import script None value handling"
19. `36cbf34` → "Add CSV import script using Python (encoding issue fixed)"
20. `4e8e21c` → "Add CSV batch import script (encoding issue fixed)"
21. `92992b6` → "Fix CSV file generation (Out-File encoding issue fixed)"
22. `91d461f` → "Fix CSV file generation (explicit columns, UTF-8)"
23. `e51ba63` → "Add CSV encoding fix script"
24. `8739dc0` → "Add CSV batch file (temporary)"
25. `807a371` → "Add CSV import script"
26. `d47a280` → "Add migration method via VM for batch"
27. `5d8734a` → "Add local batch migration guide"
28. `ff567c4` → "Add Cloud SQL table creation script"
29. `24dbab7` → "Add Cloud SQL Admin API setup guide"
30. `fe27f92` → "Add GCP setup guide from console"
31. `3c5e21e` → "Add Cloud SQL Proxy connection timeout fix guide"
32. `3f18988` → "Add GCP VM initial setup script"
33. `b2a6279` → "Add GCP initial setup: Cloud SQL, VM setup, initial setup scripts"

## Manual Fix Process

Since these commits are already pushed, you'll need to:

1. Run `git rebase -i HEAD~33` (or however many commits need fixing)
2. Change `pick` to `reword` for each commit with a broken message
3. When the editor opens for each commit, replace the message with the English version
4. After rebase completes, force push: `git push --force-with-lease origin main`

**Warning**: Force pushing rewrites history. Make sure no one else is working on this branch.

