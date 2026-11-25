#!/bin/bash
# g_probe.sh SNAPSHOT_DIR [probe|shots] [OUTDIR] : run the Godot black-box probe on a COPY of the snapshot's game/ (never the snapshot itself).
# Usage: ROCKET_NODE=<name of the rocket Node3D> GODOT_BIN=/path/to/godot bash accept/g_probe.sh SNAPSHOT probe
# SNAPSHOT must contain a Godot project in SNAPSHOT/game (project.godot with a main scene that contains the rocket node).
set -u
SNAP=$(cd "${1:?usage: g_probe.sh SNAPSHOT_DIR [probe|shots] [OUTDIR]}" && pwd) || exit 1
[ -L "$SNAP/game" ] && { echo "SNAPSHOT/game must not be a symlink"; exit 1; }
[ -f "$SNAP/game/project.godot" ] || { echo "no Godot project at $SNAP/game"; exit 1; }
MODE=${2:-probe}; OUT=${3:-}
D=$(mktemp -d) && [ -n "$D" ] && [ -d "$D" ] || { echo "mktemp failed"; exit 1; }
trap 'rm -rf "$D"' EXIT
cp -RP "$SNAP/game" "$D/game" || exit 1; [ -d "$D/game" ] && [ ! -L "$D/game" ] || { echo "copy failed"; exit 1; }; rm -rf "$D/game/screenshots"
[ -z "$(find "$D/game" -type l | head -1)" ] || { echo "the project contains symlinks; refusing to run the probe on it"; exit 1; }
cp "$(dirname "$0")/g_probe.gd" "$D/game/_accept_probe.gd" || exit 1
export GODOT_BIN=${GODOT_BIN:-$HOME/local-llm/rocket/tools/bin/godot}
export ROCKET_NODE=${ROCKET_NODE:-Rocket}
( cd "$D/game" && timeout 120 "$GODOT_BIN" --headless --audio-driver Dummy --editor --import >/dev/null 2>&1 )   # build the import cache
if [ "$MODE" = shots ]; then mkdir -p "$OUT"; ( cd "$D/game" && timeout 180 "$GODOT_BIN" --audio-driver Dummy --fixed-fps 60 --script res://_accept_probe.gd -- shots "$OUT" 2>&1 | tail -5 )
else ( cd "$D/game" && timeout 600 "$GODOT_BIN" --headless --audio-driver Dummy --fixed-fps 60 --script res://_accept_probe.gd -- probe 2>&1 | grep -E "^PROBE|SCRIPT ERROR|Parse Error|WATCHDOG" | head -5 ); fi
