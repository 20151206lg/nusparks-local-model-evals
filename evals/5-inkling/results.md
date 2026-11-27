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

