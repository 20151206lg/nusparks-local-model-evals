# nusparks local-model evaluation procedures

How we test whether a **local** AI coding model can do real work, and how we check the result without trusting the model's own report. Companion to the posts on [nusparks.fyi](https://nusparks.fyi/): [Four local AI coding runs, zero playable rocket games](https://nusparks.fyi/posts/mac-local-models-rocket-game/) and its predecessor [We tried building a rocket game with local AI](https://nusparks.fyi/posts/local-models-rocket-game-godot-panda3d/). The procedures in this repository were run on one Apple M3 Max Mac (36 GB unified memory) with open-weight models served by `llama.cpp`. The scripts and server management are written for macOS (bash 3.2, LaunchAgents); on Linux you would need to adapt them, and we have not tested that.

> Each test below is **one or two runs per setup, on one machine**: individual observations that show where a setup got stuck, not a ranking of models. Eval 2, 3 and 4 are *historical procedures*: they document what we ran and the scripts we used, and need adapting (see each folder) before you can rerun them.

## The four evaluations

| # | Folder | Question | Order to run |
|---|---|---|---|
| 1 | [`evals/1-rtb-single-agent`](evals/1-rtb-single-agent/) | Can one local coder + agent build a latency-bounded second-price ad exchange from a spec, and how many rounds of expert review does it need? | first, one model at a time |
| 2 | [`evals/2-rtb-coder-reviewer-pipeline`](evals/2-rtb-coder-reviewer-pipeline/) | Does adding a second local model as reviewer (one coder, one reviewer, a hosted assistant orchestrating) make the loop converge faster? | after #1 |
| 3 | [`evals/3-rocket-game`](evals/3-rocket-game/) | Two local coder/agent pairs on a small 3D game, with and without Godot, judged by independent black-box checks | any time; needs Godot and Panda3D |
| 4 | [`evals/4-bonsai-solo`](evals/4-bonsai-solo/) | One small ternary model (7.9 GB) on evals 1 and 3 with thinking off | after #1 and #3 |

Shared notes: [`docs/models-and-hardware.md`](docs/models-and-hardware.md) (exact models, quantizations, server flags), [`docs/lessons.md`](docs/lessons.md) (traps that cost us time, so they do not cost you).

## What the procedures have in common

1. A written task spec that does not name any known bug.
2. A fixed agent harness: tool allow/deny lists, command shims, caps on time, tool calls and idleness enforced from outside the agent.
3. **Independent acceptance.** We never score from the agent's report or its own tests. We run black-box probes and mutation checks ourselves.
4. Honest bookkeeping: a timeline of every event, and every wrong turn of our own recorded.

## Read this before running anything: safety

These scripts drive autonomous coding agents and local servers. **There is no sandbox here.** Command shims and deny lists reduce what an agent tends to do; they do not contain it (Pi has no permission system, and eval 2 gives it an unrestricted `bash`). The acceptance probes execute code the agents wrote, and the Panda3D probes open an offscreen graphics context.

- Run agents and candidate code in a **disposable environment**: a separate user account, a VM, or a container, with nothing you care about reachable.
- `bin/swap.sh` enables and disables macOS LaunchAgents and restarts them; it refuses to run unless you set `EVAL_ALLOW_SERVICE_CHANGES=1`. Read it first and adapt the labels, ports and paths to your own servers.
- `reap()` in `bin/env.sh` kills Python/Godot/Node processes of your user whose working directory is inside the current run directory. It refuses to run unless `RUN` is an existing directory of the form `<path under your home>/runs/<id>`.
- Setup downloads packages (npm, PyPI) and, in the rocket eval, a Godot release. A hosted assistant (Claude Code) read the project files, the agents' logs and the game code to orchestrate and judge; if you do the same, that content goes to that service.

## Requirements

macOS or Linux with bash, git, Python 3.9+ and `llama.cpp`; the coding agents Kilo CLI (npm `@kilocode/cli`) and Pi (npm `@earendil-works/pi-coding-agent`), versions in `docs/models-and-hardware.md`; for the rocket game, Godot 4.7 and Panda3D. Scripts were written for macOS (bash 3.2) and assume GNU `timeout` on the PATH (install `coreutils` and add its `gnubin` to PATH) and some paths under `~/local-llm`. `init_run.sh` writes the run directory to `runs/CURRENT.env`; `source` that file in each shell (`export RUN=...`), because a script cannot export a variable to its caller.

## What is not here

- The rocket game itself (a private project with its own assets): the handoff documents named in the prompts are not included. The Godot and Panda3D probes need such a project to run against. See `evals/3-rocket-game/README.md`.
- Model weights and raw per-run logs.

## Licence

- Code (scripts, probes, shims; `*.sh`, `*.py`, `*.gd`, `*.jsonc`): [MIT](LICENSE).
- Content (documents, prompts, task specs, results and notes, including result files such as `*.json` and `results-*.md`): [CC BY 4.0](LICENSE-CC-BY-4.0.txt). Credit "Luna (nusparks)" with a link to the repository. The licence text is the verbatim `legalcode.txt` from creativecommons.org.

The models, tools and Godot/Panda3D have their own licences; check them before reuse.
