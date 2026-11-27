"""Reference pygfx app (probe validation only; written by Claude, not by a model)."""
import os, time
import pygfx as gfx
from rendercanvas.auto import RenderCanvas, loop
from controller import LaunchController
ASSETS = os.path.join(os.path.dirname(__file__), "..", "game", "assets")
canvas = RenderCanvas(size=(1280, 800), title="Rocket launch")
renderer = gfx.renderers.WgpuRenderer(canvas)
scene = gfx.Scene(); scene.add(gfx.Background.from_color("#6a7f93"))
pad = gfx.load_gltf(os.path.join(ASSETS, "launch-complex.glb"), quiet=True).scene; pad.local.x = -18; scene.add(pad)
rocket = gfx.load_gltf(os.path.join(ASSETS, "orbital-rocket.glb"), quiet=True).scene; rocket.name = "rocket"; rocket.local.x = 20; scene.add(rocket)
scene.add(gfx.AmbientLight(intensity=1.0)); sun = gfx.DirectionalLight(); sun.local.position = (10, 40, -20); scene.add(sun)
camera = gfx.PerspectiveCamera(50, 1280 / 800)
hud_scene = gfx.Scene(); hud_camera = gfx.ScreenCoordsCamera()
hud = gfx.Text(text="", font_size=26, anchor="top-left", material=gfx.TextMaterial(color="#ffffff")); hud.local.position = (20, 780, 0); hud_scene.add(hud)
big = gfx.Text(text="", font_size=64, anchor="middle-center", material=gfx.TextMaterial(color="#ffd24a")); big.local.position = (640, 400, 0); hud_scene.add(big)
game = LaunchController(); thrust = {"held": False}; clock = {"last": time.perf_counter(), "acc": 0.0}; follow = {"y": 12.0}
@canvas.add_event_handler("key_down", "key_up")
def on_key(e):
    k, down = e["key"], e["event_type"] == "key_down"
    if k == " ": thrust["held"] = down
    elif down and k == "Enter":
        if game.phase == "ready": game.start_countdown()
        elif game.phase == "result": game.reset()
    elif down and k.lower() == "r": game.reset()
    elif down and k.lower() == "f": follow["y"] = 12.0
def animate():
    now = time.perf_counter(); dt = min(now - clock["last"], 0.25); clock["last"] = now; clock["acc"] += dt
    while clock["acc"] >= 1 / 60: game.advance(1 / 60, thrust["held"]); clock["acc"] -= 1 / 60
    rocket.local.y = game.altitude
    follow["y"] = 12.0 + max(0.0, game.altitude)
    camera.local.position = (0, follow["y"] + 2, -60); camera.look_at((0, follow["y"], 0))
    hud.set_text(f"{game.phase.upper()}  ALT {game.altitude:6.1f} m  SPEED {game.vertical_speed:6.1f} m/s  FUEL {game.fuel:5.1f}  HEAT {game.heat:5.1f}")
    big.set_text(f"{game.result_reason}" if game.phase == "result" else (f"{game.countdown_left:.0f}" if game.phase == "countdown" else ""))
    renderer.render(scene, camera, flush=False); renderer.render(hud_scene, hud_camera)
    canvas.request_draw()
canvas.request_draw(animate)
if __name__ == "__main__":
    loop.run()
