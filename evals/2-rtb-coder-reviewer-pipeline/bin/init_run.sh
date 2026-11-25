#!/bin/bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export RUN=$ROOT/runs/$(date +%Y%m%d-%H%M); mkdir -p "$RUN"; date +%s > "$RUN/.start"; : > "$RUN/live.log"; : > "$RUN/timeline.log"
echo "$RUN"
