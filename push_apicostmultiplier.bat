@echo off
REM Script to initialize, commit, and push the apicostmultiplier folder to GitHub.
REM Run this from the repo folder where this script resides.

REM Change to script directory
cd /d "%~dp0"

REM Initialize git repo (if not already)
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  git init
)

REM Ensure user has configured name/email; if not, this will use global settings
git add --all

REM Create commit (allow empty commit message if nothing changed will fail, so guard)
git diff --staged --quiet
if errorlevel 1 (
  git commit -m "Export apicostmultiplier: GUI wiring and logging updates"
) else (
  echo No changes to commit.
)

REM Configure remote (replace any existing origin)
git remote remove origin 2>nul || rem
git remote add origin https://github.com/morganross/apicostmultiplier.git

REM Ensure main branch name and push
git branch -M main 2>nul || rem

echo Pushing to origin main...
git push -u origin main
