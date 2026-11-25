# source me. RUN must be set by the caller (run dir). Paths for the rocket-game experiment.
export ROCKET=$HOME/local-llm/rocket
export ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
export PATH=$ROOT/bin:$ROCKET/tools/bin:$PATH
export GODOT_BIN=$ROCKET/tools/bin/godot
export KILO_CONFIG=$ROOT/kilo-rocket.jsonc
export LOG=${RUN:-/tmp}/swap.log
check_run() {  # RUN must be an existing directory <path under your home>/runs/<id>; sets RUN_REAL to its canonical path
  [ -n "${RUN:-}" ] && [ -d "$RUN" ] || return 1
  local r h; r=$(cd "$RUN" && pwd -P) || return 1; h=$(cd "$HOME" && pwd -P) || return 1
  case "$r" in "$h"/*/runs/*|"$h"/runs/*) ;; *) return 1;; esac
  [ "$(basename "$(dirname "$r")")" = runs ] || return 1
  RUN_REAL=$r
}
reap() {
  check_run && [ -n "${RUN_REAL:-}" ] || { echo "reap: RUN must be an existing directory <path under your home>/runs/<id>; refusing"; return 1; }
  for pid in $(pgrep -u "$(id -u)" -if 'python|godot|node' 2>/dev/null); do
    d=$(lsof -a -p $pid -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')
    case "$d" in "$RUN_REAL"|"$RUN_REAL"/*) kill $pid 2>/dev/null && tl.sh "reaped leftover pid $pid (cwd $d)";; esac
  done
}
