#!/bin/bash
# round.sh N PROMPT_FILE TOOLS [wall_min] [tool_cap] [idle_s] : Pi round N in $W. N=1 starts a fresh session; N>1 continues it (-c).
# The pid file is written by an `sh -c` that then execs timeout/pi: `$$` inside a ( ) subshell is the PARENT shell's pid, so a cap would kill this script, not Pi.
# Caps (wall, tool calls, idle) are enforced from outside. stdin comes from /dev/null (Pi blocks without it). Pi has NO permission system:
# run in a disposable environment; the shims in ../shims block a few commands by name only. Needs RUN.
set -u; source "$(dirname "$0")/env.sh"; check_run || { echo "RUN must be an existing directory <path under your home>/runs/<id>"; exit 1; }
N=$1; PF_PROMPT=$2; TOOLS=$3; MIN=${4:-60}; CAP=${5:-300}; IDLE=${6:-900}; T0=$(date +%s)
D=$RUN/r$N; mkdir -p "$D"; PF="$D/agent.pid"; rm -f "$PF" "$PF".count "$PF".capped "$PF".idle
CONT=""; [ "$N" != 1 ] && CONT="-c"
tl.sh "r$N START tools=$TOOLS wall=${MIN}m cap=$CAP idle=${IDLE}s prompt=$(basename "$PF_PROMPT")"
( cd "$W" && export PATH=$ROOT/shims:$PATH && exec sh -c 'echo $$ > "$0"; exec "$@"' "$PF" timeout $((MIN*60)) pi -nc --offline --mode json --session-dir "$RUN/pi-sessions" $CONT --tools "$TOOLS" -p "$(cat "$PF_PROMPT")" </dev/null 2>"$D/agent.err" ) \
  | python3 "$ROOT/bin/capwatch.py" $CAP $IDLE "$PF" pi | tee "$D/agent.jsonl" | python3 "$ROOT/bin/summarize.py" | sed -l "s/^/[r$N] /" >> "$RUN/live.log"
RC=${PIPESTATUS[0]}; reap
WHY=finished; [ -e "$PF.capped" ] && WHY="CAPPED at tool call $(cat $PF.capped)"; [ -e "$PF.idle" ] && WHY="IDLE $(cat $PF.idle)s"; [ "$RC" = 124 ] && [ "$WHY" = finished ] && WHY="WALL-TIMEOUT"
tl.sh "r$N END exit=$RC why='$WHY' calls=$(cat $PF.count 2>/dev/null || echo ?) duration=$(( $(date +%s) - T0 ))s"
git -C "$W" add -A 2>/dev/null; git -C "$W" -c user.name=rtb-run -c user.email=rtb-run@localhost commit -q --allow-empty -m "round $N (harness commit)"
mkdir -p "$D/snap"; rsync -a --exclude .git --exclude __pycache__ "$W/" "$D/snap/"; tl.sh "r$N committed $(git -C "$W" rev-parse --short HEAD)"
