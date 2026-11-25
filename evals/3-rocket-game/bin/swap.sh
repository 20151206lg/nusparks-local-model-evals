#!/bin/bash
# swap.sh clover|mova : make exactly one llama-server resident. Aborts loudly on any failed step.
# Leaves exactly one LaunchAgent enabled (reboot-safe). Env LOG = file to append progress to.
set -u
[ "${EVAL_ALLOW_SERVICE_CHANGES:-}" = 1 ] || { echo "swap.sh enables/disables macOS LaunchAgents (com.llamacpp.server, com.k2horizon.server) and restarts them. Read it, create those agents yourself, then set EVAL_ALLOW_SERVICE_CHANGES=1." >&2; exit 2; }
D=gui/$(id -u); LA=$HOME/Library/LaunchAgents
case "${1:-}" in
  clover) T=com.llamacpp.server;  TP=8000; O=com.k2horizon.server; OP=8001;;
  mova)   T=com.k2horizon.server; TP=8001; O=com.llamacpp.server;  OP=8000;;
  *) echo "usage: swap.sh clover|mova" >&2; exit 2;;
esac
log(){ echo "$(date +%T) swap[$1]: $2" | tee -a "${LOG:-/dev/null}" >&2; }
die(){ log "$1" "FAILED: $2"; exit 1; }
gpu(){ ioreg -r -d 1 -c AGXAccelerator | grep -o '"In use system memory"=[0-9]*' | head -1 | cut -d= -f2; }
loaded(){ launchctl print "$D/$1" >/dev/null 2>&1; }
healthy(){ [ "$(curl -s -m 3 127.0.0.1:$1/health)" = '{"status":"ok"}' ]; }

# 1. stop the other service (disable first so a reboot cannot restart it)
if loaded $O || lsof -nP -iTCP:$OP -sTCP:LISTEN >/dev/null 2>&1; then
  log $1 "stopping $O"
  launchctl disable $D/$O
  launchctl bootout $D/$O 2>/dev/null
  for i in $(seq 60); do lsof -nP -iTCP:$OP -sTCP:LISTEN >/dev/null 2>&1 || break; sleep 1; done
  lsof -nP -iTCP:$OP -sTCP:LISTEN >/dev/null 2>&1 && die $1 "port $OP still listening after 60 s"
else
  launchctl disable $D/$O
fi

# 2. GPU memory must settle (trap 3), only needed if the target is not already up
if ! (loaded $T && healthy $TP); then
  for i in $(seq 120); do g=$(gpu); [ "${g:-99999999999}" -lt 2000000000 ] && break; sleep 1; done
  [ "${g:-99999999999}" -lt 2000000000 ] || die $1 "GPU in-use still ${g} bytes after 120 s"
  log $1 "GPU settled (${g} bytes in use)"
  # 3. start target
  launchctl enable $D/$T
  if loaded $T; then launchctl kickstart -k $D/$T || die $1 "kickstart $T"; else launchctl bootstrap $D $LA/$T.plist || die $1 "bootstrap $T"; fi
  for i in $(seq 240); do healthy $TP && break; sleep 1; done
  healthy $TP || die $1 "no healthy {\"status\":\"ok\"} on :$TP after 240 s"
fi

# 4. exactly one listener, it is llama-server, and a real generation works
n=$(lsof -nP -iTCP:8000 -iTCP:8001 -sTCP:LISTEN | tail -n +2 | wc -l | tr -d ' ')
[ "$n" = 1 ] || die $1 "expected 1 listener on 8000/8001, found $n"
lsof -nP -iTCP:$TP -sTCP:LISTEN | grep -q llama-ser || die $1 "listener on :$TP is not llama-server"
code=$(curl -s -m 120 -o /dev/null -w '%{http_code}' 127.0.0.1:$TP/v1/chat/completions \
  -H 'Content-Type: application/json' -d '{"model":"x","max_tokens":16,"messages":[{"role":"user","content":"Say OK."}]}')
[ "$code" = 200 ] || die $1 "liveness generation returned HTTP $code"
log $1 "OK: $T on :$TP, $O disabled+stopped, GPU in use $(gpu) bytes"
