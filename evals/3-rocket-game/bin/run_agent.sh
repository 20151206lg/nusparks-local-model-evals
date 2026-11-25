#!/bin/bash
# run_agent.sh kilo|pi PIDFILE SECS PROMPT : cwd = work dir. exec keeps the pid so capwatch can SIGTERM `timeout`.
echo $$ > "$2"; export PATH=$ROOT/shims:$PATH
if [ "$1" = pi ]; then
  exec timeout "$3" pi -nc --offline --mode json --session-dir "$RUN/pi-sessions" --tools read,bash,edit,write -p "$4" </dev/null
else
  exec timeout "$3" kilo run --dir "$PWD" --format json --title "rocket" "$4" </dev/null
fi
