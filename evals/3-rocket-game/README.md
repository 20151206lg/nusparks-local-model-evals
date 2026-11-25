# Eval 3: a small 3D rocket game, two local coder/agent pairs, with and without Godot

**Task:** a one-button arcade rocket launch game (our project was a small Godot game with a matching Python/Panda3D port). Press Enter for a 3-second countdown; hold Space to burn fuel and climb; let go to coast; reach 150 m before the engine overheats, the rocket hits the ground, or 30 s pass; R resets. Rules: gravity 9.8, thrust acceleration 30, fuel 100 (burn 20/s), heat 0-100 (heating 35/s, cooling 30/s; 25/s in one handoff doc), fixed 1/60 s step, frame delta clamped to [0, 0.05]; result priority overheat > ground impact (once airborne) > time limit > success.

Four cells: {Clover + Kilo, MoVA + Pi} x {Godot 4.7.2 / GDScript, Python 3.14 + Panda3D 1.10.16}. One run each, 2-hour cap, 400-tool-call cap, 20-minute idle cap.

**Read [`RESULTS.md`](RESULTS.md) first.** Short version: none of the four produced a playable game; own tests passed where they existed; the independent probes caught what the tests did not.

## What is in this folder

| Path | What |
|---|---|
| `bin/` | `init_run.sh`, `run_cell.sh G\|P clover\|mova` (fresh clone, preflight on the untouched repo, swap server, agent under caps, snapshot, harness commit), `run_all.sh`, `accept_watch.sh`, `run_accept.sh`, `capwatch.py`, `swap.sh`, `summarize.py` |
| `shims/` | command wrappers that make Pi (no deny list of its own) refuse the commands Kilo's config denies: downloads, installs, window-opening `npm` commands. They are a convenience, **not isolation** |
| `kilo-rocket.jsonc` | Kilo config (explicit deny list) |
| `prompts/G.txt`, `P.txt` | the prompt templates we used (placeholders for three project documents; see `prompts/README.md`). The Python prompt asks for all three milestones in one go |
| `accept/` | **independent black-box acceptance**: `g_probe.gd`/`g_probe.sh` (Godot, headless, key events injected, 10-11 checks), `p_controller_probe.py` (differential test of the rules code against `rules_oracle.py`), `p_app_scenario.py` + `p_app_probe.py` (Panda3D app driven through its event system, deterministic 1/60 clock) |
| `reference-probe-11of11.json` | the Godot probe's result on the reference game (11/11; one check only exists once a round is won, so candidates report out of 10) |

## Not included (and why)

- **The game project.** The prompts are templates: `{{GODOT_HANDOFF_DOC}}`, `{{AGENT_NOTES}}` and `{{PYTHON_CHALLENGE_DOC}}` stand for documents of a private project (assets and code have no distribution licence yet). This eval is a **historical procedure**: to rerun it you need your own project with equivalent documents (a rules spec such as [`RULES.md`](RULES.md), a starter scene or assets, a test command that passes on the untouched repo) and set those three environment variables, for example `export GODOT_HANDOFF_DOC="docs/handoff.md" AGENT_NOTES="AGENTS.md" PYTHON_CHALLENGE_DOC="docs/python-challenge.md"`. The probes assume the file layout in `accept/` (`python_game/controller.py` exposing `LaunchController`; a Godot project whose main scene contains a `Node3D` whose name you pass in `ROCKET_NODE`) and some hard-coded `~/local-llm/rocket` paths.
- `accept/rules_oracle.py` is an executable form of [`RULES.md`](RULES.md), a behaviour specification written for this repository. It was checked against the project's own reference controller on 3000 random traces (no divergence), but contains no code of that project.

## Procedure

1. Build a base checkout of each track (Godot: project plus `npm ci --ignore-scripts`; Python: venv with Panda3D, panda3d-gltf, simplepbr). Run each track's own checks on the **untouched** repo; they must pass before you start any agent.
2. `bin/init_run.sh`, then `bin/run_all.sh` (four cells in sequence; `accept_watch.sh` in a second terminal scores each cell as it ends. It skips screenshots, but the Python app probe still opens an offscreen graphics context, so on a memory-tight machine run it after the models have finished).
3. Score from `accept.json`, not from the agent's report. Read the agent's final message and notes **against** the probes: false claims are part of the result.
4. To run the Godot probe by hand: `ROCKET_NODE=<node name> GODOT_BIN=/path/to/godot bash accept/g_probe.sh SNAPSHOT probe` (SNAPSHOT must contain the project in `SNAPSHOT/game`). Run the probes on the reference game first. If the reference does not pass, fix the probe, not the candidate.

## Known limits of the probes

Black-box and heuristic: the rocket node is found by name; Panda3D input is injected through its event system, not real key presses; Godot input through `Input.parse_input_event`. Prior exposure: `accept/rules_oracle.py` was written by someone who had seen the project's reference controller; it was written from `RULES.md` and tested for equivalence, not in isolation. Two probe bugs were found during our run (a watchdog too short for a game with no winning policy; Python module paths and apps that wrap `ShowBase` instead of subclassing it); both are fixed here.
