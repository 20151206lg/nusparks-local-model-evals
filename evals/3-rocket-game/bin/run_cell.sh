#!/bin/bash
# run_cell.sh G|P clover|mova [wall_min] [tool_cap] : one experiment cell. Fresh clone of the base repo, preflight (untouched repo
# passes its own checks), swap to the model's server, run the agent (Kilo for clover, Pi for mova) with a tool-call cap, an idle cap and a wall cap,
# then reap leftovers, commit whatever is left, snapshot. Needs RUN. No retry after a cap/timeout.
set -u; source "$(dirname "$0")/env.sh"
check_run || { echo "RUN must be an existing directory <path under your home>/runs/<id> (run bin/init_run.sh and source runs/CURRENT.env)"; exit 1; }
TRACK=$1; MODEL=$2; MIN=${3:-120}; CAP=${4:-400}; IDLE=1200; CELL=$TRACK-$MODEL; T0=$(date +%s)
case $MODEL in clover) AGENT=kilo;; mova) AGENT=pi;; *) echo bad model; exit 2;; esac
case $TRACK in G) BASE=$ROCKET/base-godot;; P) BASE=$ROCKET/base-python;; *) echo bad track; exit 2;; esac
PROMPT="$(python3 "$ROOT/bin/render_prompt.py" "${PROMPT_FILE:-$ROOT/prompts/$TRACK.txt}")" || { echo "prompt rendering failed; nothing was started"; exit 2; }
D=$RUN/$CELL; WORK=$D/work; mkdir -p "$RUN" && mkdir "$D" 2>/dev/null || { echo "cell directory $D already exists (or RUN unusable); use a new run directory"; exit 1; }
tl.sh "$CELL start (agent=$AGENT, wall cap ${MIN} min, tool cap $CAP, idle cap ${IDLE}s)"
git clone -q "$BASE" "$WORK" && git -C "$WORK" config user.name "rocket-run" && git -C "$WORK" config user.email "rocket-run@localhost" || { tl.sh "$CELL ABORT clone"; exit 1; }
if [ $TRACK = G ]; then
  cp -R "$BASE/node_modules" "$WORK/node_modules"; ( cd "$WORK" && timeout 900 npm test >"$D/preflight.log" 2>&1 && timeout 900 npm run godot:check >>"$D/preflight.log" 2>&1 ) || { tl.sh "$CELL ABORT preflight failed (see preflight.log)"; exit 1; }
else
  ( cd "$WORK" && timeout 900 uv venv -q --python 3.14 .venv && timeout 900 uv pip install -q --python .venv/bin/python -r python_game/requirements.txt && timeout 900 .venv/bin/python python_game/environment_check.py --render >"$D/preflight.log" 2>&1 ) || { tl.sh "$CELL ABORT preflight failed (see preflight.log)"; exit 1; }
  rm -rf "$WORK/python_game/artifacts"
fi
git -C "$WORK" status --short > "$D/preflight-status.txt"
tl.sh "$CELL preflight ok"
swap.sh $MODEL || { tl.sh "$CELL ABORT swap $MODEL failed"; exit 1; }
tl.sh "$CELL swap to $MODEL ok"
PF="$D/agent.pid"; rm -f "$PF" "$PF".count "$PF".capped "$PF".idle
tl.sh "$CELL AGENT start"; T1=$(date +%s)
( cd "$WORK" && run_agent.sh $AGENT "$PF" $((MIN*60)) "$PROMPT" 2>"$D/agent.err" ) \
  | python3 "$ROOT/bin/capwatch.py" $CAP $IDLE "$PF" $AGENT | tee "$D/agent.jsonl" | python3 "$ROOT/bin/summarize.py" | sed "s/^/[$CELL] /" >> "$RUN/live.log"
RC=${PIPESTATUS[0]}; reap
WHY=finished; [ -e "$PF.capped" ] && WHY="CAPPED at tool call $(cat "$PF.capped")"; [ -e "$PF.idle" ] && WHY="IDLE $(cat "$PF.idle")s"; [ "$RC" = 124 ] && [ "$WHY" = finished ] && WHY="WALL-TIMEOUT"
CALLS=$(cat "$PF.count" 2>/dev/null || echo ?)
tl.sh "$CELL AGENT end exit=$RC why='$WHY' calls=$CALLS duration=$(( $(date +%s) - T1 ))s"
git -C "$WORK" add -A 2>/dev/null; git -C "$WORK" commit -q --allow-empty -m "end of run (harness commit of whatever was left)" 2>/dev/null
echo "$(git -C "$WORK" branch --show-current) $(git -C "$WORK" rev-parse --short HEAD)" > "$D/final-commit.txt"
mkdir -p "$D/snap" && rsync -a --exclude node_modules --exclude .venv --exclude .godot --exclude __pycache__ "$WORK/" "$D/snap/" || { tl.sh "$CELL ABORT snapshot failed"; exit 1; }
tl.sh "$CELL END $(cat "$D/final-commit.txt") total=$(( $(date +%s) - T0 ))s"
