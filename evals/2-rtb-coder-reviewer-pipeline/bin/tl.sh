#!/bin/bash
# tl.sh <phase> <event...> : append "t+mm:ss phase event" to $RUN/timeline.log
S=$(cat "$RUN/.start" 2>/dev/null || date +%s); N=$(( $(date +%s) - S ))
printf 't+%02d:%02d %s\n' $((N/60)) $((N%60)) "$*" >> "$RUN/timeline.log"
