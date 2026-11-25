#!/bin/bash
# accept_watch.sh : run the no-screenshot acceptance of each cell as soon as its END line appears. Needs RUN.
source "$(dirname "$0")/env.sh"
for CELL in G-clover P-clover G-mova P-mova; do
  waited=0
  until grep -q "$CELL END\|$CELL ABORT" "$RUN/timeline.log"; do sleep 20; waited=$((waited+20)); [ "$waited" -ge "${MAX_WAIT_S:-14400}" ] && { tl.sh "$CELL acceptance gave up waiting (${MAX_WAIT_S:-14400}s)"; break; }; done
  grep -q "$CELL ABORT" "$RUN/timeline.log" && continue
  grep -q "$CELL END" "$RUN/timeline.log" || continue
  sleep 5; run_accept.sh $CELL >> "$RUN/accept_watch.out" 2>&1; tl.sh "$CELL acceptance done (no screenshots)"
done
tl.sh "ACCEPT WATCH DONE"
