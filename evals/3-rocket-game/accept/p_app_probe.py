#!/usr/bin/env python3
"""p_app_probe.py SNAPSHOT_DIR [SHOTS_OUTDIR] : run every app scenario in its own subprocess on a COPY of the snapshot (venv python of base-python,
same pinned Panda3D). Prints one JSON object."""
import sys, os, json, subprocess, shutil, tempfile
snap = os.path.abspath(sys.argv[1]); shots = sys.argv[2] if len(sys.argv) > 2 else None
PY = os.path.expanduser("~/local-llm/rocket/base-python/.venv/bin/python"); HERE = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(); work = os.path.join(tmp, "snap"); shutil.copytree(snap, work, ignore=shutil.ignore_patterns(".git", ".venv", "node_modules", ".godot", "__pycache__"))
def scen(name, arg="", timeout=240):
    try:
        p = subprocess.run([PY, os.path.join(HERE, "p_app_scenario.py"), work, name, arg], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        line = [l for l in p.stdout.splitlines() if l.startswith("SCEN ")]
        if line: return json.loads(line[-1][5:])
        return {"error": "no SCEN line", "rc": p.returncode, "stderr": p.stderr[-400:]}
    except subprocess.TimeoutExpired:
        return {"error": f"timeout {timeout}s"}
out = {"scenarios": {}}
for name in ["space_alone", "countdown_liftoff", "continuous_thrust", "reset_in_flight", "reset_in_countdown", "ground_impact_terminal", "pad_sit", "time_limit"]:
    out["scenarios"][name] = scen(name)
trials = []
for b in (1.0, 1.5, 2.0, 2.5):
    for c in (0.5, 1.0, 1.5, 2.0):
        r = scen("pulse", f"{b},{c}")
        trials.append(r)
        if r.get("won_alt", -1) > 0: break
    if any(t.get("won_alt", -1) > 0 for t in trials): break
out["pulse_trials"] = trials
out["some_pulse_policy_wins"] = any(t.get("won_alt", -1) > 0 for t in trials)
if shots: out["shots"] = scen("shots", shots, timeout=300)
ok = sum(1 for v in out["scenarios"].values() if v.get("ok")) + (1 if out["some_pulse_policy_wins"] else 0)
out["passed"] = ok; out["total"] = len(out["scenarios"]) + 1
shutil.rmtree(tmp, ignore_errors=True); print(json.dumps(out, default=str))
