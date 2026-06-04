#!/usr/bin/env bash
# Commit ONLY electron_repo changes into the surrounding git repo (mono-repo safe),
# then push if an 'origin' remote exists. Safe to run by hand, from a git hook, or cron.
set -uo pipefail
SELF_DIR="$(cd "$(dirname "$0")/.." && pwd)"          # .../electron_repo
REPO_ROOT="$(git -C "$SELF_DIR" rev-parse --show-toplevel)" || { echo "Not inside a git repo."; exit 1; }
REL="${SELF_DIR#"$REPO_ROOT"/}"                        # electron_repo path relative to repo root
cd "$REPO_ROOT"
if [ -z "$(git status --porcelain -- "$REL")" ]; then
  echo "No electron_repo changes to commit."
else
  git add -- "$REL"
  git -c user.name="electron_repo watch" -c user.email="electron-watch@local" \
      commit -m "electron_repo watch: $(date +%F)" -- "$REL" && echo "Committed electron_repo changes."
fi
if git remote get-url origin >/dev/null 2>&1; then
  git push origin HEAD || echo "Push failed here (likely no network) — push from your own machine."
else
  echo "No 'origin' remote set; skipping push. Add one with: git remote add origin <url>"
fi
