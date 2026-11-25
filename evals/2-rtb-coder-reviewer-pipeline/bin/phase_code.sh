#!/bin/bash
# phase_code.sh N : swap to Clover, run the coder (Kilo), commit + snapshot.   Needs RUN.
set -u; source "$(dirname "$0")/env.sh"; N=$1; T0=$(date +%s)
tl.sh "c$N CODER start"; swap.sh clover || { tl.sh "c$N ABORT swap clover failed"; exit 1; }
tl.sh "c$N swap to clover ok"
cd "$W" || exit 1
if [ "$N" = 1 ]; then
  PROMPT=$(cat $ROOT/prompts/C1.txt); SESS=()
else
  cp "$RUN/REVIEW-c$((N-1)).md" "$W/REVIEW.md"; PROMPT=$(cat $ROOT/prompts/Cn.txt)
  SESS=(--session "$(cat $RUN/kilo-session)")
fi
timeout 2700 kilo run --dir "$W" --format json --title "c$N-code" ${SESS[@]+"${SESS[@]}"} "$PROMPT" </dev/null 2>"$RUN/kilo-c$N.err" \
  | tee "$RUN/kilo-c$N.jsonl" | python3 $ROOT/bin/summarize.py | sed "s/^/[c$N code] /" >> "$RUN/live.log"
RC=${PIPESTATUS[0]}
[ "$N" = 1 ] && python3 -c "import json;print(json.loads(open('$RUN/kilo-c1.jsonl').readline())['sessionID'])" > "$RUN/kilo-session"
rm -f "$W/REVIEW.md"; reap
TOOLS=$(grep -c '"type":"tool_use"' "$RUN/kilo-c$N.jsonl"); DUR=$(( $(date +%s) - T0 ))
git -C "$W" add -A && git -C "$W" commit -q --allow-empty -m "cycle $N: coder phase" && tl.sh "c$N committed $(git -C $W rev-parse --short HEAD)"
mkdir -p "$RUN/snap/c$N-code"; rsync -a --exclude .git --exclude __pycache__ "$W/" "$RUN/snap/c$N-code/"
tl.sh "c$N CODER end exit=$RC tool_calls=$TOOLS duration=${DUR}s"
exit $RC
