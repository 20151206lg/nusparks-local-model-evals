# Traps that cost us time

Each item was hit during a real run.

**Agents and harness**
1. Pi has no permission prompts at all; restrict it from outside (PATH shims, a throwaway directory). `bash` is not enabled by default.
2. `kilo run` ends on any permission it auto-rejects (`ask`). Use `deny` for what you want blocked so the call just returns an error.
3. A coder can kill your inference server (it found the process listening on its task's default port and ran `kill`). Deny `kill`, `pkill`, `killall`, `launchctl`, and do not let the task default to a port a local server uses.
4. Leftover servers started by an agent keep ports busy. After every phase, check `lsof -iTCP:<port> -sTCP:LISTEN`. macOS names Python processes `Python`: match case-insensitively (`pgrep -if`).
5. macOS bash 3.2: expanding an empty array under `set -u` fails; use `${ARR[@]+"${ARR[@]}"}`.
6. Enforce caps (wall time, tool calls, idle time) outside the agent, and record **why** a run stopped. A stop on the model's output limit is not "finished".
7. A reviewer that writes its report only at the end loses everything on a timeout. Make it append findings the moment they are demonstrated.

**Judging results**
8. Never score from the agent's own report or tests. Where agents wrote tests, the tests passed in the RTB runs and in the rocket runs that had any, while real defects remained, because they tested internals rather than real behaviour or the real input path.
9. Tables of "mutation proofs" in an agent's reply were repeatedly wrong. Mutate a copy and run the suite yourself.
10. A fix can be a refactor that keeps the bug (the "seat" in the RTB task moved from a constant to parsing an id). Say where the value must come from and test with inputs that would expose the shortcut.
11. Your own probes have bugs. Run them first on a known-good reference, and again whenever they report a failure you did not expect. Ours miscounted multi-impression responses, timed out on a game that cannot be won, and failed to import code in a different layout.
12. Timing tests on a laptop: `sleep` and `wait` overshoot by 5-10 ms, so a 10 ms rule cannot be tested; use margins of at least 6 ms. Thirty simultaneous connections to a stdlib `HTTPServer` overflow its listen backlog on correct code, so test concurrency with direct threaded calls.

**Engine specifics (rocket game)**
13. Panda3D: Enter is the `enter` event, not `return`; `task.dt` is the task's own run time, not the frame time (use `globalClock.getDt()`); test with a non-real-time clock for determinism.
14. Godot headless: `--headless --fixed-fps 60 --script` plus `Input.parse_input_event` drives a game deterministically; give any probe that searches a policy grid a very long game-time watchdog.
