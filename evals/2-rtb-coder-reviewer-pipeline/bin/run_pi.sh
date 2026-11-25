#!/bin/bash
# run_pi.sh PIDFILE SECS PROMPT : cwd = work dir. exec keeps the pid, so capwatch can SIGTERM `timeout` (which stops pi).
echo $$ > "$1"
exec timeout "$2" pi -nc --offline --mode json --session-dir "$RUN/pi-sessions" --tools read,bash,edit,write -p "$3" </dev/null
