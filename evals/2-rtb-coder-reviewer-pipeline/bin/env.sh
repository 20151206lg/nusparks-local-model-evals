# source me: common paths. RUN must be set by the caller (run dir).
export ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
export W=${W:-$RUN/work}   # coder worktree: one per run, so reap() can be scoped to the run
export KILO_CONFIG=$ROOT/kilo-pipeline.jsonc
export LOG=$RUN/swap.log
export PATH=$ROOT/bin:$PATH
# W (the coder worktree) must live inside RUN
case "$W" in "$RUN"/*) ;; *) echo "W must be inside RUN ($RUN)"; exit 1;; esac
case "$W" in *..*) echo "W must not contain .."; exit 1;; esac
check_run() {  # RUN must be an existing directory <path under your home>/runs/<id>; sets RUN_REAL to its canonical path
  [ -n "${RUN:-}" ] && [ -d "$RUN" ] || return 1
  local r h; r=$(cd "$RUN" && pwd -P) || return 1; h=$(cd "$HOME" && pwd -P) || return 1
  case "$r" in "$h"/*/runs/*|"$h"/runs/*) ;; *) return 1;; esac
  [ "$(basename "$(dirname "$r")")" = runs ] || return 1
  RUN_REAL=$r
}
reap() {
  check_run && [ -n "${RUN_REAL:-}" ] || { echo "reap: RUN must be an existing directory <path under your home>/runs/<id>; refusing"; return 1; }
  for pid in $(pgrep -u "$(id -u)" -if 'python' 2>/dev/null); do
    d=$(lsof -a -p $pid -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')
    case "$d" in "$RUN_REAL"|"$RUN_REAL"/*) kill $pid 2>/dev/null && tl.sh "reaped leftover pid $pid (cwd $d)";; esac
  done
}
