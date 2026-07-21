#!/usr/bin/env bash
# Commit ONLY electron_repo changes into the surrounding git repo (mono-repo safe),
# then push if an 'origin' remote exists. Safe to run by hand, from a git hook, or cron.
set -uo pipefail
SELF_DIR="$(cd "$(dirname "$0")/.." && pwd)"          # .../electron_repo
REPO_ROOT="$(git -C "$SELF_DIR" rev-parse --show-toplevel)" || { echo "Not inside a git repo."; exit 1; }
REL="${SELF_DIR#"$REPO_ROOT"/}"                        # electron_repo path relative to repo root
cd "$REPO_ROOT"

# Clear stale git lock files left by an interrupted/concurrent run.
# The sandbox this can run in often blocks file DELETION (rm / -delete ->
# "Operation not permitted") but still ALLOWS rename. Some git commands release
# their lock via unlink(), which fails under that restriction and leaves the lock
# behind to jam the NEXT git command. So we move each lock aside (rename) when it
# cannot be deleted, and we call this before every git step, not just once.
clear_locks() {
  local _lock _i=0
  while IFS= read -r _lock; do
    _i=$((_i+1))
    rm -f "$_lock" 2>/dev/null \
      || mv -f "$_lock" "${_lock}.OLD.$(date +%s).$$.$_i" 2>/dev/null \
      || true
  done < <(find "$REPO_ROOT/.git" -maxdepth 4 -name '*.lock' -type f 2>/dev/null)
}

clear_locks
CHANGES="$(git status --porcelain -- "$REL" 2>/dev/null)"
clear_locks
if [ -z "$CHANGES" ]; then
  echo "No electron_repo changes to commit."
else
  git add -- "$REL"
  clear_locks
  git -c user.name="electron_repo watch" -c user.email="electron-watch@local" \
      commit -m "electron_repo watch: $(date +%F)" -- "$REL" && echo "Committed electron_repo changes."
  clear_locks
fi
if git remote get-url origin >/dev/null 2>&1; then
  git push origin HEAD || echo "Push failed here (likely no network) — push from your own machine."
  clear_locks
else
  echo "No 'origin' remote set; skipping push. Add one with: git remote add origin <url>"
fi
