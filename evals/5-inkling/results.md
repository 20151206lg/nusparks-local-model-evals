# Results: Inkling 2 Mini SQ-20 on Strata 0.2.22, Pi, 2026-11-25 and 2026-11-26

One run per arm or cell. Times are agent time on the Mac. "Rounds" count the first attempt.

## Ad exchange (eval 1), thinking off against medium effort

Same model, server (128K context, Strata's draft decoding off), harness and task spec; the only difference is Pi's thinking level (`off`: `enable_thinking` false; `medium`: `reasoning_effort` medium). Fix lists name only demonstrated defects.

| | thinking OFF | MEDIUM |
|---|---|---|
| round 1 (no shell) | 320 calls, never finished: 195 were reads of `rtb/exchange.py` (180 of the whole file; 305 reads in all). Our call cap (250) fired at call 251 but did not stop Pi (the pid bug below); the round was stopped by hand at 320. The task's own test command found 0 tests; one wrong test; the process hung at exit | 28 calls, 17.4 min, finished with a report; 17 tests via the task's own command; one latency defect (always waits the full deadline) |
| round 2 | 24 calls, 6.5 min, in a fresh session (the first attempt, in the 108K-token session carried over from round 1, was aborted); direct probes 31/31, tests catch 11 of 17 re-introduced bugs | 35 calls, 27.2 min: probes 34/34, tests catch 15 of 17 |
| round 3 | no change in 294 calls (it spent them digging through the history of one test file); the cap did not stop it (the same harness bug) and it was stopped by hand | 11 calls, 4.6 min: 25 tests, probes 34/34, mutations 17/17 in the standard batch |
| round 4 | rerun after a first attempt that ran in the wrong worktree (discarded): 50 calls, 15.2 min, 21 tests, probes 31/31, mutations 16 of 18 in the standard batch (one of the two survivors is equivalent to the original code); the separate check that the 10 ms headroom is actually used is still missed (the test checks only the constant). The valid round 4 used the same fix-list text as round 3 (`prompts/R3.txt`), because round 3 had made no change | not needed |
| exchange behaves correctly after | round 2 | round 2 |
| tests able to fail after | round 4 (one failed round and one invalid attempt in between); the headroom guard is weak | round 3: 17 of 17 in the standard batch plus the separate "headroom is used" check (18 in all) |
| agent time / tool calls | about 105 min (43:10 + 6:31 + 39:49 + 15:11 = 104:41 from the timeline) / 688 | 49:11 / 74 |
| reasoning characters emitted | 75,026 over 688 calls, in 36 of 688 replies (13 of 320, 8 of 25, 8 of 292, 7 of 51) | 144,783 over 74 calls, in 62 of 77 replies (27 of 29, 28 of 36, 7 of 12) |

Prompts: the exact prompts used are in `prompts/` (`C1.txt` for round 1 of both arms; `R2.txt` and `R3.txt` for the off arm, with its round 4 repeating `R3.txt`; `R2m.txt` and `R3m.txt` for the medium arm). An earlier copy of this folder held a leftover `R4.txt` written for another model's code; it was removed.

Probes and mutation checks: `accept/probe_rtb.py` and `mutate_rtb.py` (the off arm's API), `probe_rtb_medium.py` and `mutate_rtb_medium.py` (the medium arm's API); both are tied to the code each arm wrote.

Same task, earlier solo runs (exchange correct / tests able to fail): K2-Horizon-7B 3/4, Clover 3/5, MoVA 2/2 in its first run (in its rerun 2/5), Bonsai 3/4. Different tools and fix lists, single runs: do not rank. The medium arm's reasoning output was about twice the off arm's per run but fewer calls and far less wall time; we have one run of each, so we cannot say how much of the difference is thinking and how much is chance.

## Rocket game, Godot (cell G-inkling, medium effort)

- **Finished** in 41 min and 63 tool calls, exit 0. Our probe: **11 of 11** (the probe has 10 checks plus an 11th, "the round stops after a win", that runs only when a policy wins; the untouched project scores 3 of 10; the reference game scores 11 of 11). Space alone does not start the game, Enter starts a 3 s countdown (liftoff at frame 185), continuous thrust overheats and loses at 83.5 m, a pulse policy reaches 150 m (17 of 25 pulse policies win, best 150.8 m), the round stops after a win, a ground impact and the 30 s limit are terminal, and reset works in the countdown and in flight, after which a second round counts down again.
- Its own checks: the project's `npm test` (18 of 18) and `npm run godot:check` pass; `godot:check` now also runs its two new test scripts (a 248-line simulation test and an 87-line scene test), which parse and run under Godot 4.7.2. It also wrote a policy-check script and used `godot:capture` with a new `--state` option; the edit to `scripts/godot.mjs` only added those two test scripts to `check` and the capture option.
- Its final report matched the code (controls Enter, Space and R; a 150 m target relative to the stand; the tuning values; a documented winning policy "hold about 2.0 s, coast about 1.5 s, hold again"). It said visual and play acceptance were pending a human, because the agent connection could not look at images.
- We rendered frames with the probe's screenshot mode (on a copy): HUD with phase, altitude, velocity, fuel, heat, time, objective and controls; Start and Retry buttons; flight with a flame and camera follow; a "LAUNCH FAILED, engine overheated" overlay at 2.9 s under continuous thrust. One visual oddity: at the start two rockets are visible, one on the pad beside the tower and one on a disc to the right. The disc rocket is the one that flies; the pad rocket disappears at the first launch and does not return after a reset.
- Reasoning: 112,034 thinking characters, in 41 of 58 assistant turns.

## Rocket game, Python and Panda3D (cell P-inkling, medium effort)

- Ended on the **wall cap** (90 min, exit 124), 166 tool calls, no final answer.
- `controller.py` (118 lines) and 11 tests of its own took about 3.5 minutes according to its log. Our controller probe: **14 of 14 checks match the reference** (11 scenario comparisons, countdown timing, 300 random traces, no engine imports in the controller).
- The remaining calls went into the app: `app.py` was written five times (calls 49, 54, 65, 120 and 149), with long detours into Panda3D internals (vertex-data formats, camera lens and matrix maths, `CommonFilters` and `FilterManager`, light classes, then `renderFrame` and the task loop). It deleted `app.py` twice, at calls 64 and 119, each time followed by a rewrite. Pi's automatic compaction ran once, at call 116 (reason "threshold", a summary was written and the run continued), so only the second deletion followed it, by three calls. We did not establish that the compaction caused that rewrite.
- The final `app.py` **crashes on start**: `LaunchApp.__init__` calls `self.base.setTitle(...)`, which `ShowBase` does not have (`AttributeError`). We reproduced it by running the file on a copy. Our app probe therefore fails every scenario (0 of 9). The last 14 calls were still debugging how to step the render loop. Its `experiment-log.md` still says milestone 2 (the application) is "Not started".
- Reasoning: 168,273 thinking characters, in 97 of 162 assistant turns. The session had grown to about 115K of the 131K-token window when Pi summarized it. (We saw single reasoning-heavy turns take minutes in Strata's monitor in both rocket cells, but those readings were not saved and are not reported.)
- Not playable.

## Rocket game, Python and Panda3D, second run through OpenCode (cell P-inkling-oc, medium effort)

Why: we asked for a second Python run as a tie-break for the rating, with the criterion written down beforehand: it counts as a pass only if our app probe passes (the app starts and the game can be won). It did not pass.

Setup: the same model, server, prompt (`prompts/P.txt` of eval 3), base project and caps (90 min wall, 400 tool calls, 1200 s idle), but the agent is **OpenCode 2.4.1 instead of Pi**, so the two Python runs differ in the agent as well as in the run. OpenCode ran with its own config folder ([`server/opencode-rocket/`](server/opencode-rocket/opencode/opencode.jsonc), loaded through `XDG_CONFIG_HOME`; medium effort set with `body.reasoning_effort`), `OPENCODE_DISABLE_PROJECT_CONFIG=1` (the base project ships its own `opencode.json` and `.opencode/tools` with custom asset-generation tools that the other cells never saw; ignoring them also cut OpenCode's baseline prompt from about 14.1K to about 12.7K tokens), and an ordered deny list like the Kilo run's. We tested the denies first (`curl` and `kill` were refused, `echo` ran). Reads outside the worktree through the shell are not blocked, as with Pi. OpenCode's baseline prompt is about 12.7K tokens (Kilo about 17K, Pi about 1K).

- Ended on the **wall cap** (90 min, exit 124), 113 tool calls (110 shell, 3 file writes), no final report; the last message was "I have all the API reconnaissance I need. Now let me write the application."
- `controller.py` (132 lines) and 13 tests of its own, written by call 12; its log gives about 6.8 minutes for that milestone. Our controller probe: **14 of 14** checks match the reference, as in the Pi run.
- `app.py` (406 lines) was written once, at call 24, and **never run by the agent in 113 calls** (no command ran it). Our app probe: **0 of 9**: the file fails at its first import (`cannot import name 'CDFNode' from 'panda3d.core'`), so no ShowBase app can be built from it. The Pi run's app failed on a different call (`setTitle`); both ended as an app that cannot start.
- After writing the app, about 90 calls went on reading and probing Panda3D (event and message managers, `ShowBase` internals, mouse-wheel and motion handling, camera, lights, `OnscreenText`).
- OpenCode's automatic summary: the prompt fell from 112,175 to 28,221 tokens between calls 64 and 65 (the event stream has no summary event; we infer it from the size drop). In the 48 calls after it the agent neither ran nor rewrote the app, and its last message speaks as if the app did not exist yet. We did not establish that the summary caused this; the Pi run's session also went wrong after its summary, in a different way (it deleted and rewrote its app).
- Reasoning: 53,304 reasoning tokens over 110 steps (OpenCode's own count; the Pi cells above count characters, so the two are not comparable). Its `experiment-log.md` says milestone 2 is "Not started".
- Deviation: at minute 68 we ran the unit tests and `app.py --help` in the live worktree to check progress (this created bytecode caches only).

## Rocket game, Python with pygfx instead of Panda3D, through OpenCode (cell PG-inkling-oc, medium effort)

Why: all five earlier Python/Panda3D cells (evals 3-5) ended with an app that did not start, each on a Panda3D API fact, and the owner suspected the engine. Ursina, a simpler layer on Panda3D, was ruled out first: its stock shaders need GLSL 1.30/1.40, which macOS OpenGL rejects, so it draws black or blank frames and no HUD text (lesson 30). pygfx renders through Metal and loaded the project's GLBs with correct colors, so we built a pygfx variant of the task ([`pygfx-track/`](pygfx-track/README.md)) and a new black-box probe, validated on a reference app (9 of 9) and on the untouched project (0 of 9). Same model, server, medium effort, caps (90 min wall, 400 tool calls, 1200 s idle) and **OpenCode 2.4.1**, with the same run config as the OpenCode Panda3D run plus a text-only model declaration (below). Pass criterion, set before the run: our app probe passes.

- Ended on the **wall cap** (90 min, exit 124), 135 tool calls (133 shell, 2 read), 0 errors, no final report; the last message was mid-polish ("The overheat flow works, but the rocket mesh doesn't reset until the next frame. Let me make the key handlers refresh visuals immediately").
- Controller: 14 of 14 matches the reference, 13 tests of its own pass; its log gives about 4 minutes for that milestone.
- **App probe: 9 of 9, the first Python app in these evals to pass**, with the same numbers as our reference (liftoff at frame 185, 83.48 m under continuous thrust, reset works in flight and in the countdown, a burn/coast pulse reaches 150.6 m). It loads both GLBs with `gfx.load_gltf`, names the player's rocket node `OrbitalRocket`, and runs its own app repeatedly from call 77 on.
- We looked at 3 of the 8 rendered frames: a title and controls panel, phase, fuel, heat, altitude and speed, a "YOUR ROCKET" label (the launch complex has its own prop rocket), a camera that follows the rocket in flight, and an "Engine overheated. Press Enter to reset." result overlay. The numbers in the flight frame (fuel 76.3, heat 41.4 at 14.3 m) match the Godot game's.
- **Not done:** milestone 3. The project has only the controller tests (no integration test, no saved frames), and its `experiment-log.md` still says milestones 2 and 3 are "Not started". OpenCode summarized the conversation once, at call 89 (prompt 111,374 to 35,321 tokens); unlike the Panda3D OpenCode run, the agent kept working normally for the next 46 calls. 57,594 reasoning tokens over 131 steps.
- **Invalid first attempt (not counted).** At call 60 of its first start the agent read a PNG of its own text test; OpenCode sent the image to Strata, which we had launched with vision off, and Strata answered HTTP 400, ending the run (exit 1, 24 min). The model entry was not declared text-only. We declared it (`capabilities.input: ["text"]`), checked that an image read now returns a "does not support image input" message instead of an error, renamed the folder and ran the cell again from scratch. The rerun is the result above.
- **Also not counted:** a Pi cell for this track was started by mistake (the owner had settled on OpenCode) and stopped after about 94 s and 10 calls.

All three Python cells for this model (the engines are not the only difference between them: the first used Pi):

| engine, agent | controller probe | app probe | ended | calls |
|---|---|---|---|---|
| Panda3D, Pi | 14/14 | 0/9 (`setTitle` crash) | wall cap | 166 |
| Panda3D, OpenCode | 14/14 | 0/9 (bad import, never run) | wall cap | 113 |
| **pygfx, OpenCode** | 14/14 | **9/9** | wall cap | 135 |

What this does and does not show: one run per engine, so a chance difference is possible. The pygfx variant also differs in setup: the project README states pygfx's Y-up convention and the offscreen switch, and the contract above makes the app importable, which the Panda3D probe did not need. The comparison that is cleanest is the two OpenCode cells (same agent, config and prompt apart from the engine words); the Pi cell differs in agent too. It does suggest that for this model on this Mac the Panda3D API, not the rules code or the workflow, was the sticking point.

Same cells, other setups (probe results): Godot — Clover 3 of 10, MoVA 3 of 10, Bonsai 3 of 10. Python controller — Clover 4 of 14, MoVA 13 of 14, Bonsai 14 of 14; app — Clover cannot start, MoVA frozen, Bonsai none.

## Our own mistakes (kept in the record)

1. **The pid file held the wrong pid.** In the RTB harness `echo $$ > pidfile` ran inside a `( )` subshell, where `$$` is the parent shell's pid; when a cap fired it killed the harness script, not Pi (twice). The fix is `sh -c 'echo $$ > "$0"; exec "$@"'`. The same line was in the published eval 4 `round.sh`; it is fixed there too (macOS bash 3.2 has no `$BASHPID`). `capwatch.py` now also sends SIGKILL ten seconds after SIGTERM, because Pi once kept running after the cap.
2. Continuing round 1's Pi session carried about 108K tokens of re-reading into round 2 (9 to 13 minutes per turn), so round 2 of the off arm was restarted fresh and every later round used a fresh session (`FRESH=1`). The Bonsai run continued sessions, so the two are not identical in that respect.
3. The off arm's first round 4 ran in the medium arm's worktree because we sourced both settings files in one shell command; we reset it and reran it. The medium arm's scores were computed before the mix-up and re-verified after the reset.
4. A wait loop returned early on a stale "committed" line; one of our probes assumed another implementation's default partner prices (the code was right).
5. The rocket Python cell was started with `a && b && nohup c &`, which backgrounds the whole chain; harmless here, but use `(nohup c > file 2>&1 &)`.
6. The Godot probe has 10 checks plus one that runs only if a game can be won, and we first wrote "the probe has 11 checks"; the untouched project scores 3 of 10.
7. Our first write-up said the thinking-off round 1 "re-read `exchange.py` 116 times". A recount from the agent log (done after an outside review) gives 195 reads of that file (180 of the whole file). The same write-up said the call cap stopped the round; it fired but did not stop Pi (item 1).
8. The first copy of this folder contained a leftover `prompts/R4.txt` written for another model's code instead of the prompt the off arm's round 4 used (the `R3.txt` text again). Removed.
9. We first wrote that the Python run's compaction was followed by "the" app deletion. The log shows two deletions (calls 64 and 119); only the second followed the summary (call 116).
10. We first attached a 286-second turn to the Python run; it came from the Godot cell's monitor reading, and none of those latency readings were saved, so they are not reported.
12. We started the pygfx cell through Pi without asking, although OpenCode was the agreed tool; stopped after about 94 s.
13. Our OpenCode config did not declare the model text-only, which killed the first pygfx attempt with an HTTP 400 when the agent read an image (item above). Our global OpenCode config had the same flaw.
14. The shared `live.log` mixes attempts that use the same cell name, so a call count read from it was inflated; counts here come from each attempt's own event file.
15. We ran the unit tests inside a live worktree a second time (during the pygfx rerun), after noting item 11; it added only bytecode caches.
11. At minute 68 of the OpenCode Python run we ran the unit tests and an import of the app inside the live worktree to check progress. It only added bytecode caches and did not change the result, but a running cell should be left alone.
