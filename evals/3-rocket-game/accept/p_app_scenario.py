#!/usr/bin/env python3
"""p_app_scenario.py SNAPSHOT SCENARIO [ARG] : run ONE scenario against the Panda3D app found in SNAPSHOT/python_game (a copy; cwd=SNAPSHOT).
Discovers the first ShowBase subclass in python_game/*.py (not controller/environment_check/tests), runs it offscreen with a deterministic
60 Hz clock, drives it with the Panda3D messenger (enter, space, space-up, r, f) and tracks the lowest point of the node named like *rocket*.
Prints one JSON line `SCEN {...}`."""
import sys, os, json, importlib, importlib.util, inspect, traceback, math
snap = os.path.abspath(sys.argv[1]); scen = sys.argv[2]; arg = sys.argv[3] if len(sys.argv) > 3 else ""
os.chdir(snap); sys.path.insert(0, snap); sys.path.insert(0, os.path.join(snap, "python_game"))
from panda3d.core import loadPrcFileData, ClockObject, Filename
loadPrcFileData("", "window-type offscreen\nwin-size 1280 800\naudio-library-name null\nsync-video false\nnotify-level warning\nframebuffer-srgb true")
res = {"scenario": scen}
def done(**kw):
    res.update(kw); print("SCEN " + json.dumps(res, default=str)); sys.stdout.flush(); os._exit(0)
from direct.showbase.ShowBase import ShowBase
app = None; mod_name = None; wrapper = None
try:
    d = os.path.join(snap, "python_game")
    cands = [f[:-3] for f in sorted(os.listdir(d)) if f.endswith(".py") and f[:-3] not in ("controller", "environment_check", "__init__") and not f.startswith("test")]
    if os.path.isdir(os.path.join(d, "app")): cands += ["app"]
    errs = []
    for c in cands:
        try:
            m = importlib.import_module("python_game." + c)
        except BaseException as e:
            errs.append(f"{c}: import {type(e).__name__}: {e}"[:200]); continue
        classes = [k for _, k in inspect.getmembers(m, inspect.isclass) if issubclass(k, ShowBase) and k is not ShowBase and k.__module__ == m.__name__]
        for k in classes:
            try:
                app = k(); mod_name = c + "." + k.__name__; break
            except BaseException as e:
                errs.append(f"{c}.{k.__name__}(): {type(e).__name__}: {e}"[:250]); app = None
        if not app:
            # composition: a class that builds its own ShowBase and keeps it in an attribute
            for _, k in inspect.getmembers(m, inspect.isclass):
                if k.__module__ != m.__name__ or issubclass(k, ShowBase): continue
                try:
                    w = k()
                    sb = next((v for v in vars(w).values() if isinstance(v, ShowBase)), None)
                    if sb is not None: wrapper = w; app = sb; mod_name = c + "." + k.__name__ + "(wrapped)"; break
                except BaseException as e:
                    errs.append(f"{c}.{k.__name__}(): {type(e).__name__}: {e}"[:250])
        if app: break
    if app is None: done(error="no instantiable ShowBase subclass in python_game/*.py", tried=errs)
except BaseException:
    done(error="discovery failed: " + traceback.format_exc()[-400:])
res["app"] = mod_name
clock = ClockObject.getGlobalClock(); clock.setMode(ClockObject.MNonRealTime); clock.setDt(1 / 60.0)
if scen != "shots": app.taskMgr.remove("igLoop")     # skip rendering for speed (screenshots render explicitly)
def find_rocket():
    best = None
    for np_ in app.render.findAllMatches("**"):
        n = np_.getName().lower()
        if "rocket" in n and "complex" not in n and "launch" not in n.replace("rocket", ""):
            b = np_.getTightBounds()
            if b is None: continue
            h = b[1].z - b[0].z
            if 15 < h < 40 and (best is None or h > best[0]): best = (h, np_)
    return best[1] if best else None
rocket = find_rocket()
if rocket is None and wrapper is not None:
    from panda3d.core import NodePath as _NP
    for k_, v_ in vars(wrapper).items():
        if "rocket" in k_.lower() and isinstance(v_, _NP) and not v_.isEmpty() and v_.getTightBounds() is not None: rocket = v_; break
if rocket is None:
    # fall back: any node with a name containing 'rocket'
    for np_ in app.render.findAllMatches("**"):
        if "rocket" in np_.getName().lower() and np_.getTightBounds() is not None: rocket = np_; break
if rocket is None: done(error="no node named like *rocket* with geometry found under render")
def low(): return rocket.getTightBounds()[0].z
def step(n=1):
    for _ in range(n): app.taskMgr.step()
step(5); z0 = low(); def_alt = lambda: low() - z0
def send(name): app.messenger.send(name)
def enter(): send("enter")
def space_down(): send("space")
def space_up(): send("space-up")
def reset_key(): send("r")
def shot(name, outdir):
    app.graphicsEngine.renderFrame(); app.graphicsEngine.renderFrame()
    os.makedirs(outdir, exist_ok=True); app.win.saveScreenshot(Filename.fromOsSpecific(os.path.join(outdir, name + ".png")))
def alt(): return def_alt()
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
        send("f"); step(10); shot("8-after-f", out)
        done(ok=True, shots=out)
    else: done(error="unknown scenario")
except SystemExit:
    raise
except BaseException:
    done(error="scenario crashed: " + traceback.format_exc()[-500:])
