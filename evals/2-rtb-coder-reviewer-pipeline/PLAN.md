# Pipeline test: Clover codes, MoVA reviews, Claude orchestrates + final review

Status: PLAN, not started. Written 2026-11-23. Nothing below has been run.

## Question

Does a local reviewer (K2-Horizon-MoVA-36B-A4B) make a local coder (Clover-35B-A3B) converge
faster and more reliably than the solo runs did, and how much of Claude's review work does it
replace? Baselines (same RTB task, `rtb-spec` = `28d018a`): K2-7B 3 rounds to correct exchange /
4 until tests can fail; Clover+Kilo 3 / 5; MoVA+Pi 2 / 2, rerun 5 / 5. Every baseline needed Claude
to write the fix recipes. One task, one run: the result is an anecdote, not a ranking.

## Preflight findings (checked 2026-11-23, read-only)

| item | found | consequence |
|---|---|---|
| running server | **MoVA** on :8001 (pid 1100, up 1 h), healthy; Clover **not loaded** | start state is MoVA, not Clover |
| LaunchAgents | `com.llamacpp.server` **disabled**, `com.k2horizon.server` enabled | a swap must enable/disable, not just load/unload |
| GPU / RAM | in-use 1.3 GB (idle reading, see AGENTS.md), 88% free | fine |
| both ports | only :8001 listening, nothing on :8000 | no stale listener (trap 4) |
| tools | kilo 7.8.32, pi 1.5.2 | both have JSON event output (`kilo run --format json`, `pi --mode json`) |
| `TASK.md` @ rtb-spec | says "**no shell**" and "All files under `pi-k2-rtb/`" | must edit the shell line (decision 1: bash from round 1); path stays |
| `AGENTS.md` @ rtb-spec | old MTPLX-era file, no RTB content | harmless; same tree Clover used before. Pi runs use `-nc` |
| `.venv` | not in worktrees | task is Python 3.9 stdlib, so use `/usr/bin/python3` |
| Kilo bash permission | global config allows only `python3 *`, `timeout`, `head`, `grep`, `seq`, `echo`, `tail`, `true`; everything else `ask` | `kilo run` without `--auto` auto-rejects the rest. Smoke test decides whether the allowlist needs `ls`/`cat`/`wc` |

No `openScreen` skill exists in this session; logging is file-based (below).

## Layout

Run dir `<repo>/evals/2-rtb-coder-reviewer-pipeline/runs/<timestamp>/` (not committed):

| path | content |
|---|---|
| `timeline.log` | one line per event: `t+mm:ss phase event` (swaps, starts, ends, exit codes, durations) |
| `live.log` | condensed tool-call stream from the JSON events (`tail -f` this) |
| `kilo-cN.jsonl`, `pi-cN-{a,b}.jsonl` | raw event streams |
| `REVIEW-cN.md` | MoVA's review, concatenated from pass A and B, passed to Clover **verbatim** |
| `CLAUDE-cN.md` | my independent review of the same snapshot. **Never shown to Clover or MoVA** |
| `snap/cN-code/` | snapshot of the worktree after each coder phase |
| `score.md` | final scoring |

Worktree: `git worktree add "$RUN/work" -b "rtb-pipeline-$(basename "$RUN")" rtb-spec`, outside the repo
and outside any parent that has an `AGENTS.md`/`kilo.jsonc` (verified in smoke test). Commit after each coder
phase so every cycle is a diff.

## Server swap (never two models resident: Clover ~21 GB + MoVA ~24 GB > 36 GB)

`swap.sh clover|mova`, sequence, aborting loudly on any failed step:
1. `launchctl disable` + `bootout` the **other** service; wait until its port is closed.
2. Wait until `ioreg ... "In use system memory"` < 2 GB (trap 3: 15-30 s) and `lsof` shows nothing on 8000/8001.
3. `launchctl enable` + `bootstrap` the target; poll `/health` for exactly `{"status":"ok"}`, and confirm `lsof` shows only llama-server on the target port.
4. One generation of 8 tokens as a liveness check (the model loads lazily enough that `/health` can lie).

Each swap leaves exactly one service enabled, so a reboot mid-run cannot start both.
**End state = state found: MoVA enabled and running, Clover disabled.** I will ask before restoring Clover as the default.

## Loop (max 3 cycles)

```
for N in 1..3:
  A. swap clover; Clover coder phase (kilo run, --format json, 45 min cap)
       N=1: C1 prompt.  N>1: continue the same Kilo session with the Cn prompt + REVIEW-(N-1).md
  B. commit snapshot; copy to snap/cN-code and to a throwaway review copy
  C. swap mova; reviewer pass A then pass B in the copy (fresh Pi session each, 40 min cap)
       stop the loop if both passes say VERDICT: PASS
  D. I write CLAUDE-cN.md (no sharing). Then loop.
after loop:
  E. my final review of the last snapshot. Defects found = escalation rounds: I write the recipe,
     Clover fixes, max 2, each counted separately.
```

Why two reviewer passes: MoVA's window is 48K, and a full-repo read plus thinking plus mutation output
risks the auto-compaction failure (trap 6). Pass A = implementation vs spec + black-box behavior. Pass B = test validity
(mutation checks). Each starts fresh; I concatenate mechanically.

## Rules that keep the result honest

1. **I relay, I do not coach.** During the loop I add no technical hints. Anything I type beyond the fixed prompts is logged in `timeline.log` as `CLAUDE-INTERVENTION`.
2. **Blind order.** I read no code before MoVA's review of that cycle exists.
3. **Reviewer never sees the coder's self-report**, only TASK.md and the files.
4. Prompts are fixed (below), reused unchanged each cycle, and do not name any known bug.
5. Abort and report (do not improvise) on: failed swap, GPU memory error, coder/reviewer silent for 10 min with a live process, `Insufficient Memory` in server logs, or a runaway loop (> 100 tool calls with no file change).
6. Pi has no permission gate and Kilo is run without `--auto`. Both work only inside throwaway directories; I will check `git status` of the main repo and `~/` afterwards for stray writes.

## Prompts (fixed)

**TASK.md edit** (only change vs baseline): replace the "no shell" bullet with *"You have `bash`: run the tests before you finish and again after your last edit. Use `timeout 120` on every command that runs tests or the server."* and drop "so a human can run".

**C1 (coder, cycle 1):** "Read pi-k2-rtb/TASK.md completely and do everything it asks. Work from the current directory. Follow the 'When you finish' section."

**Cn (coder, cycle N>1):** "An independent reviewer inspected your code; the findings are in REVIEW.md (path given). For each finding: reproduce it, fix it, make sure a test exists that fails without the fix, then run the whole suite 5 times. Reply with a table: finding id, what you changed, command and output proving it. Change nothing not covered by a finding. If you think a finding is wrong, say so with evidence."

**R (reviewer, passes A and B):** same preamble: *You are reviewing code you did not write, in a throwaway copy you may modify (restore after each experiment). The spec is pi-k2-rtb/TASK.md. Use `timeout 120` on every command. Report only defects you demonstrated: each needs an ID, severity, the spec rule, the exact command and its output, and where the fix goes. No style comments. Write REVIEW.md and end with `VERDICT: PASS` or `VERDICT: FAIL`.*
- **A:** check every numbered auction and latency rule against the code and against real behavior (run the server, curl it, hostile partners: hanging, raising, slow-by-a-few-ms). Run the suite 5 times and report flakiness or hangs.
- **B:** for every test, change the code so the behavior the test claims to check is broken, run that test, and confirm it fails. A test that still passes is a defect. Also check that the suite exits promptly.

## Ground truth and scoring

Known bug classes from earlier runs (`AGENTS.md`), tagged for scoring:

| tag | class |
|---|---|
| B1 | response `price` is the bid, not the clearing price; single bid must pay the floor |
| B2 | partners called sequentially (fan-out not concurrent) |
| B3 | `with ThreadPoolExecutor` waits for a hung partner (3 s partner blocks the response) |
| B4 | late-bid race: bid finishing after the deadline accepted (per-future timeouts, snapshot after deadline) |
| B5 | seat derived from bid id instead of the partner name |
| B6 | non-object JSON body crashes the handler (must be 400) |
| B7 | server bound to 0.0.0.0 instead of loopback |
| B8 | floor/deal rules: floor before ranking, deal tie-break, `deal_floor` capped at own bid |
| B9 | busy-spin / re-collecting finished futures |
| B10 | tests that cannot fail (peek at mock internals, pass against the bug) |
| B11 | hang at exit (non-daemon thread, `unittest` never returns) |
| B12 | flaky tests (needs N/N stable) |
| B13 | edits outside the allowed folder, or edits to TASK.md |

Per cycle I record: MoVA findings that are real (tagged), false positives, misses (bugs I find that MoVA did not), whether Clover's claimed fix was real (verified by running, not by its table), wall time per phase including swaps.

Headline numbers vs baseline: cycles until exchange correct, cycles until tests can fail, my escalation rounds needed after the loop (baselines: 3-5 rounds of Claude recipes), MoVA recall / precision against the bug list, total wall time.

Pre-registered expectation: MoVA catches the spec-compliance classes (B1, B5-B8) and misses at least one of B3/B4/B9/B10. If it catches all, the pipeline is better than my prior.

## Smoke tests before the real run (each trivial, ~minutes)

1. MoVA is already up: `pi -nc --mode json --session-dir ... -p "read hello.py and list its functions"` in a scratch dir. Learn the event schema, write `summarize.py` for `live.log`. Run `tail -f` to confirm it streams.
2. `swap.sh clover`, then `kilo run --dir <scratch> --format json` on the same trivial task. Confirm: no `kilo.jsonc` override, correct model reported, bash allowlist behavior (does `ls` get rejected?). Decide on an extended allowlist via a copied config only if needed.
3. `swap.sh mova`, back to the found state; confirm end state matches the table above.
4. Dry-run the full timeline logger with a fake phase.

## Open items for you

1. Approve the plan as is, or change anything (cycle cap of 3, 45/40-min caps, two-pass reviewer).
2. Is it OK for the Clover LaunchAgent to be enabled/disabled repeatedly during the run, and for me to leave it disabled at the end (as found)?
