# Rocket-game test on the Mac, 2026-11-24 (run dir `~/local-llm/rocket/runs/20261124-1617`)

Four cells, one run each: {Clover + Kilo, MoVA + Pi} x {Godot track, Python/Panda3D track}.
Acceptance is my own black-box probes, not the agents' reports. One run per cell: an anecdote.

| cell | agent time | tool calls | ended | own tests | my probe | what is actually wrong |
|---|---|---|---|---|---|---|
| G-clover | 52 min | 248 | finished | 13/13 + npm test + godot:check pass | 3/10 | Nothing moves the rocket node; Space and Enter are the same `ui_accept` (also resets); target 170 m, not 150 |
| P-clover | 36 min | 138 | finished | 37 pass | app: rocket never moves | Binds key `return`, which Panda3D never fires (Enter is `enter`), so the game cannot start. Injecting `return` makes it run, but overheats at ~67 m (reference 83.5 m) and the countdown ends one frame late; controller matches the reference in only 4 of 14 checks (the countdown ends a frame late, so most traces diverge) |
| G-mova | 10 min | 14 | stopped on output cap (3 turns hit 16K tokens while thinking); harness said "finished" | none written | 3/10 (= untouched repo) | Made no changes at all |
| P-mova | 120 min | 165 | WALL cap | 16 pass | app: rocket never moves | Controller is the best of the four (13 of 14 differential checks; 2 of 300 random traces differ in fuel at dt=0.1). App uses `task.dt` as frame time, which in Panda3D is the task's own run time (~0.0002 s), so the game never advances; `run()` is only a scripted smoke test, no interactive loop. Milestone 3 never started. Its log says "User confirmed milestone 1 complete" twice: nobody did |

## Findings
- Same pattern as the RTB runs: agents' own tests pass while the real behaviour is broken, because tests cover the pure state library and never the scene/input wiring.
- No cell produced a playable game. The Godot probe passes the project's reference game 11/11 (raw result in `reference-probe-11of11.json`); the Python controller probe uses an executable form of `RULES.md` (checked against the project reference on 3000 random traces), and the two Python app findings were also confirmed by separate real-time runs, not against a reference Panda3D app.
- Outcomes by model: MoVA produced nothing on Godot (output-cap stops while thinking) and, on Python, a rules controller closer to the reference but an app that never advanced, after twice the wall time; Clover produced code that ran in both tracks but no playable game. One run each: no ranking.
- The P-mova log fabricated user confirmations; P-clover's did not.
- Not measured: screenshots (visual check) because the rocket never moves in any cell; Pi/Kilo forbidden-command attempts only grepped (mentions are doc text; shims are not isolation; a command that bypasses them would not be blocked).

## Caveats
- Different hardware tier from the laptop runs (36 GB unified vs 8 GB VRAM), prompt for P composes all three milestones into one, single run per cell.
- Probes are black-box and heuristic (rocket node found by name; Panda3D input injected through the messenger). Two probe bugs were found and fixed during the run (Godot watchdog too short; Panda3D module paths and wrapped-ShowBase apps); the supplementary real-time checks confirm the P-clover and P-mova findings independently.
- Deviations from a pristine setup: `npm ci --ignore-scripts` for the Godot base, and a Mac edit of the project's `environment_check.py` (it demanded a Linux software renderer).

## End state
Clover restored as default (`com.llamacpp.server` enabled on :8000, `com.k2horizon.server` disabled), no leftover agent/godot processes. 
