#!/bin/bash
export RUN=$HOME/local-llm/rocket/runs/$(date +%Y%m%d-%H%M); mkdir -p "$RUN"; date +%s > "$RUN/.start"; : > "$RUN/live.log"; : > "$RUN/timeline.log"
echo "export RUN=$RUN" > $HOME/local-llm/rocket/runs/CURRENT.env; echo "$RUN"
