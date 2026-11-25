#!/bin/bash
# collect_review.sh N [suffix] : rebuild REVIEW-cN.md / CHECKED-cN.md from the pass dirs, merging a REVIEW.md/CHECKED.md the reviewer wrote
# into pi-k2-rtb/ (it cd'd there) with the one in the work dir. Reviewer text is copied verbatim; only the location is fixed. Needs RUN.
set -u; source "$(dirname "$0")/env.sh"; N=$1; SUF=${2:-}
OUT="$RUN/REVIEW-c$N.md"; CK="$RUN/CHECKED-c$N.md"; : > "$OUT"; : > "$CK"
for P in A1 A2 A3 B; do
  D="$RUN/review/c$N-$P$SUF/work"; [ -d "$D" ] || continue
  : > "$RUN/REVIEW-c$N-$P$SUF.md"; : > "$RUN/CHECKED-c$N-$P$SUF.md"; STRAY=""
  for F in "$D/REVIEW.md" "$D/pi-k2-rtb/REVIEW.md"; do [ -s "$F" ] && { cat "$F" >> "$RUN/REVIEW-c$N-$P$SUF.md"; echo >> "$RUN/REVIEW-c$N-$P$SUF.md"; [ "$F" != "$D/REVIEW.md" ] && STRAY="$STRAY REVIEW.md-in-pi-k2-rtb"; }; done
  for F in "$D/CHECKED.md" "$D/pi-k2-rtb/CHECKED.md"; do [ -s "$F" ] && { cat "$F" >> "$RUN/CHECKED-c$N-$P$SUF.md"; [ "$F" != "$D/CHECKED.md" ] && STRAY="$STRAY CHECKED.md-in-pi-k2-rtb"; }; done
  V=$(grep -E '^VERDICT: (PASS|FAIL)' "$RUN/REVIEW-c$N-$P$SUF.md" | tail -1); [ -z "$V" ] && V="VERDICT: MISSING"
  NF=$(grep -c '^## ' "$RUN/REVIEW-c$N-$P$SUF.md"); NOK=$(grep -c '^ok:' "$RUN/CHECKED-c$N-$P$SUF.md")
  { echo "## Pass $P (findings below are the reviewer's own, verbatim)"; grep -v '^VERDICT:' "$RUN/REVIEW-c$N-$P$SUF.md"; echo; } >> "$OUT"
  { echo "## Pass $P"; cat "$RUN/CHECKED-c$N-$P$SUF.md"; echo; } >> "$CK"
  tl.sh "c$N pass $P COLLECTED findings=$NF ok_lines=$NOK $V${STRAY:+ (HARNESS FIX: reviewer wrote$STRAY; merged verbatim)}"
done
