#!/bin/bash
# phase_review.sh N [passes] [suffix] : v2 protocol. swap to MoVA; each pass on a fresh copy of the cycle-N snapshot, with a tool-call cap
# (capwatch) and a minutes cap. Partial REVIEW.md/CHECKED.md are always kept. No retry after a cap/timeout. Needs RUN.
set -u; source "$(dirname "$0")/env.sh"; N=$1; T0=$(date +%s)
PASSES=${2:-"A1 A2 A3 B"}; SUF=${3:-}; OUT="$RUN/REVIEW-c$N.md"; [ -z "${2:-}" ] && { : > "$OUT"; : > "$RUN/CHECKED-c$N.md"; }
tl.sh "c$N REVIEW start (v2 protocol, passes: $PASSES)"; swap.sh mova || { tl.sh "c$N ABORT swap mova failed"; exit 1; }
tl.sh "c$N swap to mova ok"
for P in $PASSES; do
  case $P in A1) CAP=45; MIN=20;; A2) CAP=45; MIN=20;; A3) CAP=55; MIN=25;; B) CAP=90; MIN=35;; *) tl.sh "unknown pass $P"; exit 1;; esac
  D="$RUN/review/c$N-$P$SUF"; mkdir -p "$D/work"; rsync -a --exclude __pycache__ "$RUN/snap/c$N-code/" "$D/work/"; rm -f "$D/work/REVIEW.md" "$D/work/CHECKED.md"
  PROMPT="$(cat $ROOT/prompts/R-common.txt) $(cat $ROOT/prompts/R-$P.txt)"; PF="$D/pi.pid"; rm -f "$PF" "$PF.count" "$PF.capped"
  tl.sh "c$N pass $P start (cap $CAP tool calls, $MIN min)"; T1=$(date +%s)
  ( cd "$D/work" && run_pi.sh "$PF" $((MIN*60)) "$PROMPT" 2>"$RUN/pi-c$N-$P$SUF.err" ) \
    | python3 $ROOT/bin/capwatch.py $CAP "$PF" | tee "$RUN/pi-c$N-$P$SUF.jsonl" | python3 $ROOT/bin/summarize.py | sed "s/^/[c$N review $P] /" >> "$RUN/live.log"
  RC=${PIPESTATUS[0]}; reap
  DUR=$(( $(date +%s) - T1 )); CALLS=$(cat "$PF.count" 2>/dev/null || echo ?); WHY="finished"
  [ -e "$PF.capped" ] && WHY="CAPPED at tool call $(cat $PF.capped)"; [ "$RC" = 124 ] && [ "$WHY" = finished ] && WHY="TIMEOUT"
  touch "$D/work/REVIEW.md" "$D/work/CHECKED.md"; cp "$D/work/REVIEW.md" "$RUN/REVIEW-c$N-$P$SUF.md"; cp "$D/work/CHECKED.md" "$RUN/CHECKED-c$N-$P$SUF.md"
  V=$(grep -E '^VERDICT: (PASS|FAIL)' "$D/work/REVIEW.md" | tail -1); [ -z "$V" ] && V="VERDICT: MISSING"
  NF=$(grep -c '^## ' "$D/work/REVIEW.md"); NOK=$(grep -c '^ok:' "$D/work/CHECKED.md")
  { echo "## Pass $P (findings below are the reviewer's own, verbatim)"; grep -v '^VERDICT:' "$D/work/REVIEW.md"; echo; } >> "$OUT"
  { echo "## Pass $P"; cat "$D/work/CHECKED.md"; echo; } >> "$RUN/CHECKED-c$N.md"
  tl.sh "c$N pass $P end exit=$RC why='$WHY' calls=$CALLS findings=$NF ok_lines=$NOK $V duration=${DUR}s"
done
tl.sh "c$N REVIEW end duration=$(( $(date +%s) - T0 ))s"
