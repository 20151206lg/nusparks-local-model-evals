#!/bin/bash
# phase_review.sh N : swap to MoVA, review pass A then B on fresh copies of the cycle-N snapshot.  Needs RUN.
set -u; source "$(dirname "$0")/env.sh"; N=$1; T0=$(date +%s)
tl.sh "c$N REVIEW start"; swap.sh mova || { tl.sh "c$N ABORT swap mova failed"; exit 1; }
tl.sh "c$N swap to mova ok"
PASSES=${2:-"A B"}; SUF=${3:-}; OUT="$RUN/REVIEW-c$N.md"; [ -z "${2:-}" ] && : > "$OUT"
for P in $PASSES; do
  D="$RUN/review/c$N-$P$SUF"; mkdir -p "$D/work"; rsync -a "$RUN/snap/c$N-code/" "$D/work/"; rm -f "$D/work/REVIEW.md"
  PROMPT="$(cat $ROOT/prompts/R-common.txt) $(cat $ROOT/prompts/R-$P.txt)"
  tl.sh "c$N pass $P start"; T1=$(date +%s)
  ( cd "$D/work" && timeout 2400 pi -nc --offline --mode json --session-dir "$RUN/pi-sessions" --tools read,bash,edit,write -p "$PROMPT" </dev/null 2>"$RUN/pi-c$N-$P$SUF.err" ) \
    | tee "$RUN/pi-c$N-$P$SUF.jsonl" | python3 $ROOT/bin/summarize.py | sed "s/^/[c$N review $P] /" >> "$RUN/live.log"
  RC=${PIPESTATUS[0]}; reap
  if [ -s "$D/work/REVIEW.md" ]; then SRC="REVIEW.md written by reviewer"; cp "$D/work/REVIEW.md" "$RUN/REVIEW-c$N-$P$SUF.md"
  else SRC="NO REVIEW.md: using final message text"; python3 - "$RUN/pi-c$N-$P$SUF.jsonl" > "$RUN/REVIEW-c$N-$P$SUF.md" <<'PY'
import sys, json
last = ""
for l in open(sys.argv[1]):
    try: d = json.loads(l)
    except Exception: continue
    if d.get("type") == "turn_end":
        m = d.get("message", {})
        t = "".join(c.get("text", "") for c in m.get("content", []) if c.get("type") == "text")
        if t.strip(): last = t
print(last)
PY
  fi
  V=$(grep -E '^VERDICT: (PASS|FAIL)' "$RUN/REVIEW-c$N-$P$SUF.md" | tail -1); [ -z "$V" ] && V="VERDICT: MISSING"
  { echo "## Pass $P"; cat "$RUN/REVIEW-c$N-$P$SUF.md"; echo; } >> "$OUT"
  tl.sh "c$N pass $P end exit=$RC src='$SRC' $V duration=$(( $(date +%s) - T1 ))s"
done
tl.sh "c$N REVIEW end duration=$(( $(date +%s) - T0 ))s"
