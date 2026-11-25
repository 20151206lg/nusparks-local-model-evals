# Pipeline test, run 2: Clover (Kilo) codes, MoVA (Pi) reviews with the fixed protocol, Claude orchestrates + final review
Run 2026-11-24, 08:46 start, ~6 h 02 min on the run clock (t+362 at the end of E2), same RTB task (`rtb-spec` 28d018a + bash TASK.md edit) as run 1. One task, two runs: anecdotes. Only the reviewer protocol changed (PLAN2.md).

## Outcome
Loop cap (3 cycles) reached without MoVA/Clover convergence; **2 escalation rounds** (E1, E2, Claude-written recipes) were used, the cap. Final snapshot `snap/e2-code` (worktree branch `rtb-pipeline`, commit 7013147): every behavioural probe correct on Python 3.9 and 3.14, suite 46/46 x5 in 0.85 s, process exit 0.14 s with a hung partner. Not clean: **2 untested rules** (non-object JSON -> 400 over HTTP; process exit with a hung partner, subprocess test) although Clover's reply table claimed both; one minor edge (colliding bid ids give the wrong seat); 10 ms headroom untestable (macOS sleep overshoot). Run 1 ended correct after 2 rounds with fewer residuals, but the E rounds of run 1 were written knowing more bug classes (and one of them contained my errors).

## Per phase (run clock minutes)
| phase | wall | tool calls | result |
|---|---|---|---|
| c1 Clover coder | 13 | 66 | claimed all done; 7 behavioural defects (D1 hung/late partner awaited, D2 deal_floor dead, D3 seat constant, D4 non-object JSON, D5 multi-imp queueing, D6 tie order, D7 exit hang) + 4 test gaps |
| c1 MoVA A1/A2/A3/B | 20 (cap) / 8.5 / 16 / 11 | 35/28/36/75 | 4 of 4 usable, 12 findings (11 real) |
| c2 Clover coder | 20 | 53 | fixed D1, D2, D4; **new regression** (per-future 50 ms: default partners 113-120 ms, in-time 60 ms partner dropped); wrote no test that fails without its fixes |
| c2 MoVA | 10 / 9 / 23 / 35 (cap) | 33/29/49/82 | 4 of 4 usable, 4 findings (4 real) |
| c3 Clover coder | 12 | 32 | fixed D5 and the regression; again no test for its fixes |
| c3 MoVA | 7 / 20 (timeout) / 25 (timeout) / 22 (capped at 91 calls) | 24/42/29/91 | **2 of 4 usable**: A2, A3 timed out with nothing written; B 3 findings (1 useful, 2 narrow) |
| E1 Clover (my recipe, 7 items) | 30 | 123 | exit hang and tie order fixed; seat still parsed from bid id; new "always waits for the deadline" regression; 5 of 7 requested tests could not fail; stray file outside pi-k2-rtb/ |
| E2 Clover (my recipe, last) | 25 | 111 | seat + grouping + early return fixed; 4 new tests catch their mutation, 2 do not (non-object JSON, subprocess exit) |
Swaps: 12 s each, 14 total (incl. the failed one), none failed on its own; one swap blocked 4 min by a leaked reviewer process (below).
MoVA time: 55 + 77 + 74 = 206 min of 362; Clover coder 45 min; escalations 55 min; the rest swaps, gaps and my audits (and ~42 min between E1's end and E2's start while I was not polling).

## MoVA as reviewer, run 2 vs run 1
| | Run 1 | Run 2 c1 | c2 | c3 |
|---|---|---|---|---|
| passes usable | 1 of 5 | 4 of 4 | 4 of 4 | 2 of 4 |
| open behavioural root causes found | 2/7 (29%) | 4/7 (57%) | 3/5 (60%) | 0/3 |
| precision | 2/2 | 11/12 | 4/4 | 1 useful + 2 narrow of 3 |
| false certification in an A1 pass | 1 | 1 (deal_floor) | 1 (tie = arrival order) | 1 (+ an ok line "0.133 s < tmax 100 ms") |
- Protocol changes worked on their stated purpose: 10 of 12 passes produced a usable report (run 1: 1 of 5), because findings were appended the moment they were found and passes were narrow with hard caps. Reports survive a timeout.
- It did not turn MoVA into a gate: **seat (D3) and tie order (D6) were never reported in any of the 3 cycles**; every A1 pass certified "auction rules correct" while a rule was wrong (3 of 3 false certifications); in c3 two of four passes timed out with 0 output.
- It never reported, at any cycle, that Clover's fixes lacked tests, and it never ran a regression check of the previous cycle's fixes (pass B's scope was existing tests). Its ok lines needed auditing (one false, several resting on compound mutations).
- Clover with MoVA's findings: fixed 7 of 10 in c2 and 2 more in c3, but every cycle added or kept a defect and wrote no failing-able tests for its own fixes (Cn demands them). Clover's claims in reply tables were wrong on tests in E1 and E2 (mutation proofs claimed, not true).
- So Claude was again the gate: every cycle and escalation needed my probes and mutation checks to know the real state.

## Baseline comparison (same task; Claude wrote recipes in all of them)
| | Claude recipe rounds | note |
|---|---|---|
| K2-7B + Pi | 3-4 | |
| Clover + Kilo solo | 5 | |
| MoVA + Pi solo | 2, rerun 5 | |
| Pipeline run 1 | 2 | clean-ish end state, 35/35 |
| Pipeline run 2 | 2 (cap) | end state with 2 untested rules and 1 edge |
Not an improvement over the best baselines on this task: 3 loop cycles (~3 h of model time) bought roughly what one recipe round would have, and the end state did not reach clean.

## My own errors and harness incidents (kept in the record)
1. I mis-read P5/P17 as a multi-impression regression in E1 because my probe only counted `seatbid[0]`; fixed the probe before writing the recipe, recorded in CLAUDE-e1.md.
2. My E1 recipe asked for "one SeatBid per partner" while the prior behaviour (one per impression) was not specified by TASK.md; Clover did the minimal thing and I corrected it in E2.
3. Harness: reviewer pass A1 of c3 left `python -m rtb.server --port 8123` running (the server ignores `--port` and bound to :8000, Clover's port); `reap` missed it because macOS names the process `Python` (case-sensitive pgrep). The swap to Clover failed after 240 s; I killed the process and fixed `reap` (`pgrep -if`). No model results affected.
4. Earlier in the run: A2's files landed in `pi-k2-rtb/` (merged verbatim by `collect_review.sh`), as in the logs.
5. Comparability: MoVA reviewed different code in run 2 than in run 1 (different Clover draft), so the recall numbers are not like-for-like.
