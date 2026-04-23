# Git Command Cheat Sheet (Ubuntu/Linux)

## Initial Setup
```bash
# Configure git (one-time setup)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# View your config
git config --global --list
```

## Cloning a Repository
```bash
# Clone a repo into your current directory
git clone https://github.com/USERNAME/REPO.git

# Navigate into the cloned folder
cd REPO
```

## Checking Status
```bash
# See what files have changed, what's staged, what's untracked
git status

# See the diff of unstaged changes
git diff

# See the diff of staged changes
git diff --staged
```

## Staging and Committing Files
```bash
# Stage a specific file
git add path/to/file.txt

# Stage all changes in the current directory
git add .

# Stage all changes in the entire repo
git add -A

# Unstage a file (keep changes locally)
git reset path/to/file.txt

# Commit staged changes
git commit -m "Your commit message here"

# Commit and skip staging (only for tracked files)
git commit -a -m "Your commit message"
```

## Branches
```bash
# List all branches (local)
git branch

# List all branches (including remote)
git branch -a

# Create a new branch
git branch branch-name

# Switch to a branch
git checkout branch-name

# Create and switch to a new branch in one command
git checkout -b branch-name

# Delete a branch (local)
git branch -d branch-name

# Delete a branch (force delete if not merged)
git branch -D branch-name
```

## Pushing and Pulling
```bash
# Push commits to a specific branch on the remote
git push origin branch-name

# Push all branches to remote
git push origin --all

# Pull updates from a specific branch
git pull origin branch-name

# Pull updates from the current branch
git pull

# Fetch updates without merging (see what's new)
git fetch origin
```

## Viewing History
```bash
# View commit history
git log

# View commit history with one line per commit
git log --oneline

# View commits from a specific branch
git log branch-name

# View commits affecting a specific file
git log -- path/to/file.txt
```

## .gitignore
```bash
# Create or edit .gitignore file
nano .gitignore

# Common patterns to add:
*.log              # Ignore all .log files
node_modules/      # Ignore node_modules folder
__pycache__/       # Ignore Python cache
.env               # Ignore environment variables
dist/              # Ignore build output
*.pyc              # Ignore compiled Python files
```

## Undoing Changes
```bash
# Discard changes in a file (restore to last commit)
git checkout -- path/to/file.txt

# Unstage all changes but keep them locally
git reset

# Undo the last commit but keep changes
git reset --soft HEAD~1

# Undo the last commit and discard changes
git reset --hard HEAD~1
```

## Quick Workflow Example
```bash
# 1. Clone the repo
git clone https://github.com/USERNAME/REPO.git
cd REPO

# 2. Create a new branch for your work
git checkout -b feature-branch

# 3. Make changes, then check status
git status

# 4. Stage your changes
git add .

# 5. Commit with a message
git commit -m "Add new feature"

# 6. Push to the remote
git push origin feature-branch
```

---
**Pro Tip:** Use `cat git_cheat_sheet.md` in your terminal anytime you need a quick reference!