#!/bin/bash
# phase_esc.sh K : escalation round K = Clover (same Kilo session) with prompts/E$K.txt. Needs RUN.
set -u; source "$(dirname "$0")/env.sh"; K=$1; T0=$(date +%s)
tl.sh "e$K ESCALATION start (Claude-written recipe, counted as an escalation)"; swap.sh clover || { tl.sh "e$K ABORT swap failed"; exit 1; }
cd "$W" || exit 1; timeout 2700 kilo run --dir "$W" --format json --title "e$K-esc" --session "$(cat $RUN/kilo-session)" "$(cat $ROOT/prompts/E$K.txt)" </dev/null 2>"$RUN/kilo-e$K.err" \
  | tee "$RUN/kilo-e$K.jsonl" | python3 $ROOT/bin/summarize.py | sed "s/^/[e$K code] /" >> "$RUN/live.log"
RC=${PIPESTATUS[0]}; reap
git -C "$W" add -A && git -C "$W" commit -q --allow-empty -m "escalation $K" && tl.sh "e$K committed $(git -C $W rev-parse --short HEAD)"
mkdir -p "$RUN/snap/e$K-code"; rsync -a --exclude .git --exclude __pycache__ "$W/" "$RUN/snap/e$K-code/"
tl.sh "e$K ESCALATION end exit=$RC tool_calls=$(grep -c '"type":"tool_use"' $RUN/kilo-e$K.jsonl) duration=$(( $(date +%s) - T0 ))s"
