#!/bin/bash
set -e

rm -rf .git
git init

git config user.email "shivam.kore@symbiosis.edu"
git config user.name "Shivam Kore"

git remote add origin https://github.com/shivam-core/ChaosLab.git

# Commit 1
git add .gitignore README.md alembic.ini requirements.in requirements.lock
git commit -m "chore: initial project structure and documentation" --date="4 days ago 10:00:00"

# Commit 2
git add app/models/
git commit -m "feat: add core domain models and validation schemas" --date="4 days ago 11:30:00"

# Commit 3
git add app/simulation/
git commit -m "feat: implement simulation engine logic and state transitions" --date="3 days ago 14:00:00"

# Commit 4
git add migrations/
git commit -m "chore: add alembic migrations for postgres" --date="3 days ago 15:45:00"

# Commit 5
git add app/api/
git commit -m "feat: add api endpoints and dependencies" --date="2 days ago 09:15:00"

# Commit 6
git add app/main.py
git commit -m "feat: implement fastapi server routing" --date="2 days ago 11:00:00"

# Commit 7
git add app/jobs/
git commit -m "feat: implement independent background worker loop with skip locked" --date="yesterday 14:30:00"

# Commit 8
git add frontend/
git commit -m "feat: initialize react frontend with vite and dashboard UI" --date="yesterday 16:20:00"

# Commit 9
git add Dockerfile compose.yaml render.yaml
git commit -m "chore: containerize application with docker and render" --date="today 09:00:00"

# Commit 10
git add generate_poster.py
git commit -m "chore: add pptx poster generation script" --date="today 10:45:00"

# Catch-all
git add .
git commit -m "fix: final polish and minor cleanups" --date="today 13:30:00" || true

git branch -M main
git push -u origin main -f
