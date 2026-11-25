#!/usr/bin/env python3
"""p_controller_probe.py SNAPSHOT_DIR : black-box differential test of python_game/controller.py against rules_oracle.py (an executable form of ../RULES.md).
Public API only (start_countdown, advance, reset, get_countdown, fields). Prints one JSON object. Exit 0 always (it is a measurement)."""
import sys, json, random, importlib.util, os, math, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules_oracle import Oracle as Ref
snap = os.path.abspath(sys.argv[1]); res = {"snapshot": snap, "checks": {}, "mismatches": []}
def norm_phase(p):
    s = getattr(p, "value", None); s = str(getattr(p, "name", p)) if s is None or not isinstance(s, str) else s
    return s.split(".")[-1].lower()
try:
    sys.path.insert(0, snap)
    spec = importlib.util.spec_from_file_location("controller_under_test", os.path.join(snap, "python_game", "controller.py"))
    m = importlib.util.module_from_spec(spec); sys.modules["controller_under_test"] = m; sys.path.insert(0, os.path.join(snap, "python_game")); spec.loader.exec_module(m); C = m.LaunchController
except Exception as e:
    res["import_error"] = repr(e); print(json.dumps(res)); sys.exit(0)
FIELDS = ["countdown_left", "altitude", "vertical_speed", "fuel", "heat", "flight_time"]
def snapshot(c):
    return {"phase": norm_phase(c.phase), **{k: getattr(c, k) for k in FIELDS}, "airborne": bool(c.airborne),
            "thrust_active": bool(c.thrust_active), "result_reason": str(c.result_reason or "")}
def refsnap(r):
    return {"phase": r.phase, **{k: getattr(r, k) for k in FIELDS}, "airborne": r.airborne, "thrust_active": r.thrust_active, "result_reason": r.result_reason}
def diff(a, b, tol=1e-6):
    out = []
    for k in a:
        x, y = a[k], b[k]
        if isinstance(x, float) or isinstance(y, float):
            if abs(float(x) - float(y)) > tol: out.append((k, x, y))
        elif x != y: out.append((k, x, y))
    return out
def check(name, ok, detail=""): res["checks"][name] = {"ok": bool(ok), "detail": detail}
def run(c, r, script):
    """script = list of (op, arg): ('s',None) start, ('a',(dt,thrust)), ('r',None) reset. returns first mismatch or None"""
    for i, (op, arg) in enumerate(script):
        if op == "s": c.start_countdown(); r.start_countdown()
        elif op == "r": c.reset(); r.reset()
        else: c.advance(arg[0], arg[1]); r.advance(arg[0], arg[1])
        d = diff(snapshot(c), refsnap(r))
        if d: return {"step": i, "op": op, "arg": arg, "diff": d[:3]}
    return None
def steps(n, dt, thrust): return [("a", (dt, thrust))] * n
def policy(on_heat=70, off_heat=30):
    # closed-loop policy needs the controller's own heat: generate with the reference (it is the oracle) and replay on both
    r = Ref(); r.start_countdown(); sc = [("s", None)]; thrust = True
    for _ in range(3000):
        if r.phase == "result": break
        if r.phase == "flight":
            if r.heat >= on_heat: thrust = False
            elif r.heat <= off_heat: thrust = True
        r.advance(1/60, thrust); sc.append(("a", (1/60, thrust)))
    return sc, r.phase, r.result_reason, r.altitude
try:
    scen = {
      "ready_idle": steps(120, 1/60, True),
      "countdown_then_flight": [("s", None)] + steps(240, 1/60, False),
      "continuous_thrust": [("s", None)] + steps(900, 1/60, True),
      "no_thrust_time_limit": [("s", None)] + steps(2200, 1/60, False),
      "short_burn_ground_impact": [("s", None)] + steps(200, 1/60, False) + steps(30, 1/60, True) + steps(900, 1/60, False),
      "reset_in_countdown": [("s", None)] + steps(60, 1/60, False) + [("r", None)] + steps(60, 1/60, True) + [("s", None)] + steps(300, 1/60, True),
      "reset_in_flight": [("s", None)] + steps(260, 1/60, True) + [("r", None)] + [("s", None)] + steps(260, 1/60, True),
      "delta_clamp_big": [("s", None), ("a", (1.0, False)), ("a", (5.0, False)), ("a", (-1.0, True)), ("a", (0.0, True))] + steps(10, 1/60, True),
      "start_twice": [("s", None)] + steps(30, 1/60, False) + [("s", None)] + steps(30, 1/60, False),
    }
    pol, ph, why, alt = policy()
    scen["policy_70_30_second_step_1_120"] = [("s", None)] + [("a", (1/120 if op == "a" else 0, arg[1])) if op == "a" else (op, arg) for op, arg in pol[1:]] * 1
    scen["policy_70_30"] = pol
    res["reference_policy_70_30"] = {"phase": ph, "reason": why, "altitude": alt}
    for name, sc in scen.items():
        c = C(); r = Ref(); mm = run(c, r, sc)
        check("diff:" + name, mm is None, "" if mm is None else json.dumps(mm, default=str)[:300])
    # get_countdown contract
    c = C(); r = Ref(); c.start_countdown(); r.start_countdown(); gc = []
    for _ in range(190):
        c.advance(1/60, False); r.advance(1/60, False); gc.append((str(c.get_countdown()), r.get_countdown()))
    bad = [g for g in gc if g[0] != g[1]]
    check("get_countdown_matches_reference", not bad, "" if not bad else f"first mismatch (got, ref) = {bad[0]} of {len(bad)}")
    # random differential traces
    rnd = random.Random(7); nbad = 0; first = None
    for t in range(300):
        sc = []
        for _ in range(rnd.randint(1, 60)):
            k = rnd.random()
            if k < 0.1: sc.append(("s", None))
            elif k < 0.13: sc.append(("r", None))
            else: sc.extend([("a", (rnd.choice([1/60, 1/30, 0.04, 0.06, 0.1, 0.0, 1/120]), rnd.random() < 0.55))] * rnd.randint(1, 40))
        c = C(); r = Ref(); mm = run(c, r, sc)
        if mm: nbad += 1; first = first or mm
    check("random_traces_300", nbad == 0, f"{nbad}/300 diverged; first={json.dumps(first, default=str)[:300]}" if nbad else "")
    # purity: no panda3d import
    src = open(os.path.join(snap, "python_game", "controller.py")).read()
    check("controller_has_no_engine_imports", "panda3d" not in src and "direct." not in src)
except Exception:
    res["error"] = traceback.format_exc()[-600:]
res["passed"] = sum(1 for v in res["checks"].values() if v["ok"]); res["total"] = len(res["checks"])
print(json.dumps(res, default=str))
