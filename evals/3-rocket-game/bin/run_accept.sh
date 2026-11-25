#!/bin/bash
# run_accept.sh CELL [shots] : independent acceptance of a finished cell ($RUN/CELL/snap). Writes $RUN/CELL/accept.json (+ accept.log).
# Everything runs on COPIES. Without `shots` nothing is rendered to screenshots, but the Python app probe still opens an offscreen graphics context; `shots` renders screenshots (Godot window / Panda3D offscreen).
set -u; source "$(dirname "$0")/env.sh"; CELL=$1; SHOTS=${2:-}; D=$RUN/$CELL; SNAP=$D/snap; A=$ROOT/accept; OUT=$D/accept.json; LOGF=$D/accept.log; : > "$LOGF"
[ -d "$SNAP" ] || { echo "no snapshot"; exit 1; }
TMP=$(mktemp -d) && [ -d "$TMP" ] || { echo "mktemp failed"; exit 1; }; cp -R "$SNAP" "$TMP/w"; TRACK=${CELL%%-*}; J="{\"cell\":\"$CELL\""
if [ $TRACK = G ]; then
  ln -s "$ROCKET/base-godot/node_modules" "$TMP/w/node_modules"
  ( cd "$TMP/w" && PATH=$ROOT/shims:$PATH timeout 300 npm test 2>&1 | grep -E "^ℹ (pass|fail|tests)" ) >> "$LOGF" 2>&1
  NPMT=$(grep -E "^ℹ fail" "$LOGF" | head -1 | awk '{print $3}')
  ( cd "$TMP/w" && PATH=$ROOT/shims:$PATH timeout 300 npm run godot:check >>"$LOGF" 2>&1 ); GC=$?
  ls "$TMP/w/game/tests" 2>/dev/null | grep -c '\.gd$' > "$D/n_gd_tests.txt"
  P=$("$A/g_probe.sh" "$SNAP" probe 2>>"$LOGF" | grep '^PROBE ' | head -1 | cut -c7-); [ -z "$P" ] && P='{"fatal":"probe produced no output"}'
  J="$J,\"npm_test_failures\":\"${NPMT:-?}\",\"godot_check_exit\":$GC,\"probe\":$P"
  [ -n "$SHOTS" ] && "$A/g_probe.sh" "$SNAP" shots "$D/shots" >>"$LOGF" 2>&1
else
  PY=$ROCKET/base-python/.venv/bin/python
  ( cd "$TMP/w" && timeout 300 $PY -m unittest discover -s python_game/tests -v >"$D/own-tests.log" 2>&1 ); UC=$?; tail -4 "$D/own-tests.log" >> "$LOGF"
  NT=$(grep -E "^Ran [0-9]+ tests?" "$D/own-tests.log" | awk '{print $2}')
  C=$(/usr/bin/python3 "$A/p_controller_probe.py" "$SNAP" 2>>"$LOGF" | tail -1); [ -z "$C" ] && C='{"fatal":"no output"}'
  if [ -n "$SHOTS" ]; then AP=$(/usr/bin/python3 "$A/p_app_probe.py" "$SNAP" "$D/shots" 2>>"$LOGF" | tail -1)
  else AP=$(/usr/bin/python3 "$A/p_app_probe.py" "$SNAP" 2>>"$LOGF" | tail -1); fi
  [ -z "$AP" ] && AP='{"fatal":"no output"}'
  J="$J,\"own_tests_exit\":$UC,\"own_tests_n\":${NT:-0},\"controller_probe\":$C,\"app_probe\":$AP"
fi
echo "$J}" > "$OUT"; rm -rf "$TMP"; echo "wrote $OUT"
