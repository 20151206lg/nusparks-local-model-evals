#!/bin/bash
# run_all.sh : the four cells in order. Needs RUN. If a cell cannot start, the remaining cells are marked ABORT (so accept_watch.sh can finish).
source "$(dirname "$0")/env.sh"
check_run || { echo "RUN must be an existing directory <path under your home>/runs/<id>"; exit 1; }
failed=0
for c in "G clover" "P clover" "G mova" "P mova"; do
  set -- $c; name="$1-$2"
  if [ "$failed" = 1 ]; then tl.sh "$name ABORT skipped after an earlier failure"; continue; fi
  run_cell.sh "$1" "$2" || { rc=$?; failed=1; grep -q "$name \(END\|ABORT\)" "$RUN/timeline.log" || tl.sh "$name ABORT run_cell.sh exited $rc"; }
done
tl.sh "ALL CELLS DONE"
[ "$failed" = 0 ]
