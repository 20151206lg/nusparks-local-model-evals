#!/usr/bin/env python3
"""pg_app_scenario.py SNAPSHOT SCENARIO [ARG] : run ONE scenario against the pygfx app found in SNAPSHOT/python_game (a copy; cwd=SNAPSHOT).
Black-box: sets RENDERCANVAS_BACKEND=offscreen, replaces time.perf_counter/time/monotonic with a fake 60 Hz clock and loop.run with a no-op, imports
python_game/*.py (not controller/environment_check/tests) until one creates a rendercanvas canvas, then drives that canvas the way a window would:
canvas.submit_event key_down/key_up (Enter, " ", r, f) + a flush, then the app's own draw function once per 1/60 s frame. Tracks the lowest point of the
world object named like *rocket* (height 15-40) along Y. Non-screenshot scenarios skip GPU rendering (renderer.render is a no-op); `shots` renders.
Prints one JSON line `SCEN {...}`."""
import sys, os, json, importlib, traceback, time as _time
snap = os.path.abspath(sys.argv[1]); scen = sys.argv[2]; arg = sys.argv[3] if len(sys.argv) > 3 else ""
os.environ["RENDERCANVAS_BACKEND"] = "offscreen"
os.chdir(snap); sys.path.insert(0, snap); sys.path.insert(0, os.path.join(snap, "python_game"))
T = [1000.0]
for _n in ("perf_counter", "time", "monotonic"): setattr(_time, _n, lambda: T[0])
_time.sleep = lambda *_a, **_k: None
res = {"scenario": scen}
def done(**kw):
    res.update(kw); print("SCEN " + json.dumps(res, default=str)); sys.stdout.flush(); os._exit(0)
import pygfx as gfx
from rendercanvas.auto import RenderCanvas, loop
loop.run = lambda *a, **k: None
canvases = []; renders = []; real_render = gfx.renderers.WgpuRenderer.render
_init = RenderCanvas.__init__
def _canvas_init(self, *a, **k): _init(self, *a, **k); canvases.append(self)
RenderCanvas.__init__ = _canvas_init
GPU = {"on": scen == "shots"}
def _render(self, scene, camera, **k):
    if scene not in renders: renders.append(scene)
    if GPU["on"]: return real_render(self, scene, camera, **k)
gfx.renderers.WgpuRenderer.render = _render
errs = []; mod_name = None
try:
    d = os.path.join(snap, "python_game")
    cands = [f[:-3] for f in sorted(os.listdir(d)) if f.endswith(".py") and f[:-3] not in ("controller", "environment_check", "__init__") and not f.startswith("test")]
    if os.path.isdir(os.path.join(d, "app")): cands += ["app"]
    cands.sort(key=lambda c: (c != "app", c))
    for c in cands:
        try:
            m = importlib.import_module("python_game." + c)
        except BaseException as e:
            errs.append(f"{c}: import {type(e).__name__}: {e}"[:260]); continue
        if canvases: mod_name = c; break
        for fn in ("main", "run", "create_app", "build", "start", "run_game"):   # fall back: an entry function that builds the app
            f = getattr(m, fn, None)
            if callable(f):
                try:
                    f()
                except BaseException as e:
                    errs.append(f"{c}.{fn}(): {type(e).__name__}: {e}"[:260])
                if canvases: mod_name = c + "." + fn; break
        if canvases: break
    if not canvases: done(error="no rendercanvas canvas was created by importing python_game/*.py", tried=errs)
except BaseException:
    done(error="discovery failed: " + traceback.format_exc()[-400:])
cv = canvases[0]; res["app"] = mod_name
def draw_fn():
    f = getattr(cv, "_draw_frame", None)
    if f is None: done(error="the canvas has no draw function (request_draw(fn) was never called)")
    return f
def step(n=1):
    for _ in range(n):
        T[0] += 1 / 60.0; cv._events.flush(); draw_fn()()
def send(t, key): cv.submit_event({"event_type": t, "key": key, "modifiers": ()})
def tap(key): send("key_down", key); send("key_up", key)
step(3)
def find_rocket():
    best = None
    for sc in renders[::-1]:
        for o in sc.iter():
            n = (getattr(o, "name", "") or "").lower()
            if "rocket" in n and "complex" not in n and "launch" not in n.replace("rocket", ""):
                try: bb = o.get_world_bounding_box()
                except Exception: continue
                if bb is None: continue
                h = float(bb[1][1] - bb[0][1])
                if 15 < h < 40 and (best is None or h > best[0]): best = (h, o)
    return best[1] if best else None
rocket = find_rocket()
if rocket is None: done(error="no world object named like *rocket* with a 15-40 m tall bounding box found in the scenes the app rendered")
def low(): return float(rocket.get_world_bounding_box()[0][1])
step(2); z0 = low()
def alt(): return low() - z0
def enter(): tap("Enter")
def space_down(): send("key_down", " ")
def space_up(): send("key_up", " ")
def reset_key(): tap("r")
def shot(name, outdir):
    from PIL import Image
    import numpy as np
    GPU["on"] = True; T[0] += 1 / 60.0; cv._events.flush(); img = cv.draw(); GPU["on"] = False
    os.makedirs(outdir, exist_ok=True); Image.fromarray(np.asarray(img)).save(os.path.join(outdir, name + ".png"))
try:
    if scen == "space_alone":
        space_down(); step(150); done(ok=abs(alt()) < 0.01, alt=alt())
    elif scen == "countdown_liftoff":
        enter(); space_down(); lift = -1
        for i in range(400):
            step()
            if alt() > 0.05 and lift < 0: lift = i + 1
        done(ok=170 <= lift <= 205, liftoff_frame_after_enter=lift)
    elif scen == "continuous_thrust":
        enter(); space_down(); mx = 0.0
        for _ in range(36 * 60): step(); mx = max(mx, alt())
        done(ok=5 < mx < 149.5, max_altitude=mx)
    elif scen == "pulse":
        burn, coast = [float(x) for x in arg.split(",")]
        enter(); step(195); mx = alt(); t = 0; won = -1.0
        while t < 31 * 60 and won < 0:
            space_down()
            for _ in range(int(round(burn * 60))):
                step(); t += 1; mx = max(mx, alt()); won = alt() if (alt() >= 149.5 and won < 0) else won
            space_up()
            for _ in range(int(round(coast * 60))):
                step(); t += 1; mx = max(mx, alt()); won = alt() if (alt() >= 149.5 and won < 0) else won
        after = -1.0
        if won > 0: step(120); after = alt()
        done(burn=burn, coast=coast, max=mx, won_alt=won, alt_2s_after=after)
    elif scen == "reset_in_flight":
        enter(); space_down(); step(300); mid = alt(); reset_key(); space_up(); step(3); back = alt()
        enter(); space_down(); lift = -1
        for i in range(400):
            step()
            if alt() > 0.05 and lift < 0: lift = i + 1
        done(ok=mid > 1 and abs(back) < 0.05 and 170 <= lift <= 205, before=mid, after=back, second_liftoff=lift)
    elif scen == "reset_in_countdown":
        enter(); step(60); reset_key(); space_down(); step(420); done(ok=abs(alt()) < 0.05, alt=alt())
    elif scen == "ground_impact_terminal":
        enter(); step(195); space_down(); step(36); space_up(); peak = 0.0
        for _ in range(600): step(); peak = max(peak, alt())
        landed = alt(); space_down(); step(120)
        done(ok=peak > 0.5 and abs(landed) < 0.05 and abs(alt()) < 0.05, peak=peak, landed=landed, after_space=alt())
    elif scen == "pad_sit":
        enter(); step(195 + 300); space_down(); step(240); done(ok=alt() > 1.0, alt=alt())
    elif scen == "time_limit":
        enter(); step(195 + 31 * 60); space_down(); step(90); done(ok=abs(alt()) < 0.05, alt=alt())
    elif scen == "shots":
        out = arg; step(30); shot("1-ready", out)
        enter(); step(60); shot("2-countdown", out)
        space_down(); step(190); shot("3-flight", out); step(120); shot("4-flight-later", out)
        space_up(); step(60); shot("5-coast", out)
        space_down(); step(600); shot("6-after-continuous-thrust", out)
        space_up(); reset_key(); step(30); shot("7-after-reset", out)
        tap("f"); step(10); shot("8-after-f", out)
        done(ok=True, shots=out)
    else: done(error="unknown scenario")
except SystemExit:
    raise
except BaseException:
    done(error="scenario crashed: " + traceback.format_exc()[-500:])
