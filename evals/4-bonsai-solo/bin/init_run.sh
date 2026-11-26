#!/bin/bash
# init_run.sh TASK_REPO BRANCH : new run directory $HOME/runs/<id> with the task worktree in <run>/work (a git worktree of BRANCH, which must hold only the task spec).
# Then: source $HOME/runs/CURRENT.env
set -eu; [ $# -eq 2 ] || { echo "usage: init_run.sh TASK_REPO BRANCH" >&2; exit 2; }
TASK_REPO=$1; BRANCH=$2; ID=$(date +%Y%m%d-%H%M); export RUN=$HOME/runs/$ID; mkdir -p "$RUN"; date +%s > "$RUN/.start"
source "$(dirname "$0")/env.sh"
git -C "$TASK_REPO" worktree add "$W" -b "bonsai-$ID" "$BRANCH"
echo "export RUN=$RUN" > "$HOME/runs/CURRENT.env"; tl.sh "init $ID worktree $(git -C "$W" rev-parse --short HEAD)"; echo "$RUN"
