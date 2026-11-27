# Python/pygfx track (a third engine for the rocket game)

Added after every Python/Panda3D cell in evals 3-5 ended with an app that did not start, each time on a Panda3D API fact the model got wrong. Ursina (an easier layer on top of Panda3D) was tried first and ruled out on macOS (lesson 30), so the same task was set up with **pygfx 0.18.0** (a Python render engine on wgpu, Metal on a Mac) and **rendercanvas 3.0.1**, with the same assets, the same controller spec and the same milestones.

What is here (the rocket project itself, its assets and its docs stay private; see [`../../3-rocket-game/README.md`](../../3-rocket-game/README.md)):

| File | What it is |
|---|---|
| [`requirements.txt`](requirements.txt), [`environment_check.py`](environment_check.py) | the pinned packages and the environment check that replaced the Panda3D ones in the project's `python_game/` folder |
| [`prompts/PG.txt`](prompts/PG.txt) | the prompt (`P.txt` with the engine-specific words changed; same placeholders) |
| [`accept/pg_app_probe.py`](accept/pg_app_probe.py), [`accept/pg_app_scenario.py`](accept/pg_app_scenario.py) | the black-box app probe (9 checks) |
| [`pg_reference/`](pg_reference/python_game/app.py) | a small reference pygfx app (on eval 3's `rules_oracle.py`) used to validate the probe |

To use it: copy `accept/*` into `evals/3-rocket-game/accept/` and `prompts/PG.txt` into its `prompts/`, apply [`../rocket-inkling.patch`](../rocket-inkling.patch) (adds the `PG` track to `run_cell.sh` and `run_accept.sh`), and make a `base-pygfx` project: a copy of the Python project with `python_game/requirements.txt` and `environment_check.py` from here, a fresh `.venv`, and its Panda3D text (README, environment notes, challenge document, handoff, agent notes) changed to pygfx. The changes we made to those documents: pygfx and rendercanvas versions, "Y-up, `load_gltf` keeps glTF's Y-up, do not rotate the rocket", "pygfx renders through wgpu", the references (docs.pygfx.org and rendercanvas docs), and the contract below.

**Contract (a testing requirement, written into the project README).** `python_game/app.py` creates its window with `rendercanvas.auto.RenderCanvas`, and the renderer, scene and camera, **when it is imported**, and starts the event loop only under `if __name__ == "__main__":`. The Panda3D probe finds a `ShowBase` subclass; a pygfx script has no class to find, so the probe needs this to import and drive the app. The prompt only adds the sentence "for checks use `OffscreenRenderCanvas` or `RENDERCANVAS_BACKEND=offscreen`", comparable to the Panda3D prompt's "use `window-type offscreen`".

## How the probe works

`pg_app_scenario.py` runs one scenario in its own process on a copy of the project: it sets `RENDERCANVAS_BACKEND=offscreen`, replaces `time.perf_counter`, `time.time` and `time.monotonic` with a fake 60 Hz clock and `time.sleep` with a no-op, makes `loop.run` a no-op, imports `python_game/*.py` until one creates a canvas, then per frame: advances the clock by 1/60 s, calls `canvas.submit_event({"event_type": "key_down"|"key_up", "key": ...})` for Enter, `" "` (space), `r` and `f`, flushes the canvas's events, and calls the app's own draw function (`canvas._draw_frame`). It measures the lowest point of the world object whose name contains "rocket" (15-40 m tall) from its world bounding box. Scenarios: Space alone does nothing; Enter then Space lifts off after about 3 s (frame 185); continuous thrust overheats before 149.5 m; reset in flight and in the countdown; a ground impact is terminal; a pad sit followed by thrust lifts within 4 s; the 30 s limit is terminal; and some burn/coast pulse pattern reaches 149.5 m. GPU rendering is skipped except in the `shots` scenario.

Validation (lesson 11): the reference app scores **9 of 9** (liftoff at frame 185, 83.48 m under continuous thrust, a 1.0 s burn with 0.5 s coast reaches 150.6 m), and an untouched project scores **0 of 9** with the error "no rendercanvas canvas was created".

Limits: it assumes the app draws through `canvas.request_draw(fn)` (apps driven by their own timers are not stepped), uses key names as rendercanvas reports them (`" "`, `"Enter"`, `"r"`, `"f"`), and finds the rocket by name and size. A real window with a different key mapping, or an app that renders the rocket under another name, would be scored as failing.
