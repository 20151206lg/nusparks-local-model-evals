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

**Local model servers and settings (eval 4)**
15. launchd keeps the job definition it loaded: editing a LaunchAgent plist and running `launchctl kickstart -k` restarts the OLD command line, so a flag test can silently test nothing. Use `launchctl bootout` then `bootstrap`, and check the live arguments with `ps -o args= -p <pid>`.
16. Check the thinking mode on the live server with a bare request (reasoning characters should be 0 when you meant it off). Bonsai thinks by default (`xhigh`); `chat_template_kwargs {"enable_thinking": false}` turns it off; we started one run at `medium` by mistake; a quick count of completed reasoning blocks was misleading because unfinished reasoning was still streaming, so verify with the full output, not a partial count.
17. Multi-token prediction (MTP) is not automatically faster: on stock llama.cpp b12387 with Metal it was about 21% slower for this model (24.1 against about 19 tok/s), and the model card's gain is for another file type on the maker's own fork. Measure on and off with the live server flags verified (item 15).
18. A rewrite that fixes one defect can regress what the previous fix guarded: moving the fan-out from a thread pool to threads fixed the exit hang and let late bids a few milliseconds past the deadline win. Re-run the earlier boundary probes after every rewrite.
19. A test of a helper function in isolation does not guard that the helper is used: bypass the call in a copy (keep every bid) and see whether any test fails.
20. Timing probes that sleep: `sleep(80 ms)` in a thread arrives at about 87 ms on this Mac. Probe with margins of at least 10 ms, or give the code a patchable clock and test the deadline rule with a fake one (the only approach that guarded the 10 ms headroom rule).

**Harness and settings (eval 5)**
21. `echo $$ > pidfile` inside a `( )` subshell writes the PARENT shell's pid, so a cap kills your harness script instead of the agent (it happened twice). Write the pid from `sh -c 'echo $$ > "$0"; exec "$@"'` so it is the pid of the process that becomes the agent. The same line was in eval 4's `round.sh` and is fixed there. macOS bash 3.2 has no `$BASHPID`. Also send SIGKILL ten seconds after SIGTERM: Pi once kept running after a cap.
22. A continued agent session carries all earlier context: Pi's round 2 continued from a round 1 that had read the same file 195 times, started at 108K tokens, and each turn took 9-13 minutes. Start a fresh session for each repair round (`FRESH=1`) and put what matters in the prompt.
23. Never source two run-settings files in one shell command: one arm's `W` stayed exported and a round ran in the other arm's worktree. Source one, run, then the next.
24. "Thinking off" may not be fully off. Inkling's model card says reasoning cannot be switched off completely, and in the "off" agent runs a minority of turns still carried reasoning (75,026 characters over 688 calls). Count reasoning characters from the full output of the run you are scoring. Also do not assume off is cheaper: in our one run per arm, medium effort used about twice the reasoning characters but 74 calls and 49 minutes against 688 calls and about 105 minutes.
25. A server that daemonizes (Strata's `strata launch` starts a detached engine and returns) is not a long-running launchd job: a LaunchAgent that only runs the command exits at once and nothing keeps the Mac awake. We run a wrapper that starts the engine, then holds `caffeinate -s -w <engine pid>`. We tested this by bootstrapping the agent, not by rebooting. If you want one of two models that cannot share the GPU to start at login, disable the other's LaunchAgent with `launchctl disable` (a loaded job keeps running until booted out).
26. Panda3D: `ShowBase` has no `setTitle`; set the window title through `WindowProperties`. The Inkling Python run crashed at start on exactly this call, and its own tests passed because they tested only the pure controller: run the real entry point (`python app.py --frames N`) before calling an app done. In our Godot probe, one of the 11 checks ("the round stops after a win") runs only if a policy can win, so an untouched project scores 3 of 10 and a working game 11 of 11.
27. OpenCode 2.x (not the 1.x format): `opencode run --standalone` starts a private server, and only then do `XDG_CONFIG_HOME` or `OPENCODE_CONFIG` redirect the config (without `--standalone` a background service that already loaded the old config answers). A project's own `opencode.json` and `.opencode/tools` are loaded too: the rocket project shipped asset-generation tools that no other cell had, so set `OPENCODE_DISABLE_PROJECT_CONFIG=1`. Permissions are an ordered list, the last match wins and a `deny` is always enforced; `execute` ("Code Mode") should be denied if you cap tool calls from outside, and `--auto` approves every `ask` that is not explicitly denied. Shell checks do not stop reads outside the worktree (`cat /etc/hosts` worked despite an `external_directory` deny).

