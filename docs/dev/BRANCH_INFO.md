# MPSM Branch Structure

## Overview

This repository uses a three-branch workflow optimized for Claude Code development sessions.

## Branch Structure

### 1. Session Branch: `claude/read-docs-framework-011CUxQMRWYEsQjTZ9nDjo92`
**Purpose**: Active development branch
**Use**: All new development work happens here
**Tracks**: `origin/claude/read-docs-framework-011CUxQMRWYEsQjTZ9nDjo92`

This is the primary working branch where all commits are made during development sessions.

### 2. Dev Branch: `claude/dev-011CUxQMRWYEsQjTZ9nDjo92`
**Purpose**: Synchronized development branch
**Use**: Automatically syncs with session branch
**Tracks**: `origin/claude/read-docs-framework-011CUxQMRWYEsQjTZ9nDjo92` (session branch)

This branch is configured to pull from the session branch, providing a stable synchronized copy of development work.

### 3. Main Branch: `claude/main-011CUxQMRWYEsQjTZ9nDjo92`
**Purpose**: Stable/release branch
**Use**: Production-ready code
**Tracks**: `origin/claude/main-011CUxQMRWYEsQjTZ9nDjo92`

This branch contains stable, tested code ready for deployment.

---

## Development Workflow

### Working on Session Branch

```bash
# Switch to session branch
git checkout claude/read-docs-framework-011CUxQMRWYEsQjTZ9nDjo92

# Make changes
# ... edit files ...

# Commit changes
git add .
git commit -m "Your commit message"

# Push to remote
git push
```

### Syncing Dev Branch

```bash
# Switch to dev branch
git checkout claude/dev-011CUxQMRWYEsQjTZ9nDjo92

# Pull latest from session branch (automatic tracking configured)
git pull

# Push to dev remote
git push origin claude/dev-011CUxQMRWYEsQjTZ9nDjo92
```

### Promoting to Main Branch

```bash
# Switch to main branch
git checkout claude/main-011CUxQMRWYEsQjTZ9nDjo92

# Merge from dev or session branch
git merge claude/dev-011CUxQMRWYEsQjTZ9nDjo92

# Push to main remote
git push
```

---

## Branch Configuration

The dev branch is configured to automatically track the session branch:

```
branch.claude/dev-011CUxQMRWYEsQjTZ9nDjo92.remote = origin
branch.claude/dev-011CUxQMRWYEsQjTZ9nDjo92.merge = refs/heads/claude/read-docs-framework-011CUxQMRWYEsQjTZ9nDjo92
```

This means when on the dev branch, running `git pull` will pull changes from the session branch.

---

## Quick Reference

| Branch | Purpose | Tracks |
|--------|---------|--------|
| `claude/read-docs-framework-011CUxQMRWYEsQjTZ9nDjo92` | Active development | Own remote |
| `claude/dev-011CUxQMRWYEsQjTZ9nDjo92` | Synced development | Session branch |
| `claude/main-011CUxQMRWYEsQjTZ9nDjo92` | Stable/release | Own remote |

---

## Setting Default Branch on GitHub

To set `claude/main-011CUxQMRWYEsQjTZ9nDjo92` as the default branch on GitHub:

1. Go to repository **Settings**
2. Click on **Branches** in the left sidebar
3. Under "Default branch", click the switch icon
4. Select `claude/main-011CUxQMRWYEsQjTZ9nDjo92`
5. Click "Update" and confirm

---

## Cleanup

The following branches have been removed:

**Local**:
- `claude/setup-readme-review-011CUxN9X6Ks7dnVaWcMpRDC` (old session branch)
- `main` (duplicate local branch)

**Remote** (manual deletion required via GitHub UI):
- `claude/setup-readme-review-011CUxN9X6Ks7dnVaWcMpRDC`

To delete the old remote branch via GitHub:
1. Go to repository branches page
2. Find `claude/setup-readme-review-011CUxN9X6Ks7dnVaWcMpRDC`
3. Click the trash icon to delete

---

**Last Updated**: 2025-11-09
