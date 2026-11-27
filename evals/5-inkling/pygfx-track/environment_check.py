"""Check the Python renderer and existing GLBs, without implementing a game."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pygfx as gfx

ROOT = Path(__file__).resolve().parents[1]


def mesh_count(obj) -> int:
    return sum(1 for o in obj.iter() if isinstance(o, gfx.Mesh))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    world = gfx.Group(name="AssetEnvironmentCheck")
    models = {}
    statistics = {}
    for name, x in [("launch-complex", -18.0), ("orbital-rocket", 20.0)]:
        path = ROOT / "game/assets" / (name + ".glb")
        model = gfx.load_gltf(str(path), quiet=True).scene
        model.local.x = x
        world.add(model)
        meshes = mesh_count(model)
        bounds = model.get_world_bounding_box()
        if meshes == 0 or bounds is None:
            raise RuntimeError("No imported mesh geometry: " + name)
        height = float(bounds[1][1] - bounds[0][1])
        if height < 15:
            raise RuntimeError("Unexpected asset height or axis: " + name)
        models[name] = model
        statistics[name] = {"meshes": meshes, "height_m": height}

    # A moving model root must also move its visible descendants.
    rocket = models["orbital-rocket"]
    before = float(rocket.get_world_bounding_box()[0][1])
    rocket.local.y += 10
    after = float(rocket.get_world_bounding_box()[0][1])
    if abs(after - before - 10) > 1e-4:
        raise RuntimeError("Imported mesh does not follow its parent")
    rocket.local.y -= 10

    result = {"ok": True, "assets": statistics, "coordinate_system": "pygfx Y-up; load_gltf keeps glTF Y-up"}
    if args.render:
        from rendercanvas.offscreen import OffscreenRenderCanvas
        from PIL import Image

        canvas = OffscreenRenderCanvas(size=(1280, 800), pixel_ratio=1)
        renderer = gfx.renderers.WgpuRenderer(canvas)
        scene = gfx.Scene()
        scene.add(gfx.Background.from_color("#6a7f93"))
        scene.add(world)
        scene.add(gfx.AmbientLight(intensity=1.0))
        sun = gfx.DirectionalLight()
        sun.local.position = (10, 40, -20)
        scene.add(sun)
        camera = gfx.PerspectiveCamera(50, 1280 / 800)
        camera.local.position = (0, 14, -60)
        camera.look_at((0, 10, 0))
        canvas.request_draw(lambda: renderer.render(scene, camera))
        image = np.asarray(canvas.draw())
        if image.shape[:2] != (800, 1280):
            raise RuntimeError(f"Unexpected render size {image.shape}")
        background = np.array([0x6A, 0x7F, 0x93])
        different = int((np.abs(image[..., :3].astype(int) - background).sum(axis=2) > 30).sum())
        if different < 20000:
            raise RuntimeError(f"Render looks empty ({different} non-background pixels)")
        out = ROOT / "python_game/artifacts"
        out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(image).save(out / "environment.png")
        result["render"] = {"size": [1280, 800], "non_background_pixels": different, "image": "python_game/artifacts/environment.png"}
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(error)}))
        sys.exit(1)
