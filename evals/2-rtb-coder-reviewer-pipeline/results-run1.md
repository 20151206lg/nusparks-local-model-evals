# Pipeline test: Clover-35B-A3B codes (Kilo), MoVA-36B-A4B reviews (Pi), Claude orchestrates + final review
Run 2026-11-23/24, ~5 h 20 min wall, RTB task from `rtb-spec` (28d018a) + one TASK.md edit (bash allowed). One task, one run: an anecdote.

## Outcome
Exchange correct after **2 Claude-written escalation rounds** (E1: 9 items, E2: 5 items), not inside the Clover<->MoVA loop. Final snapshot `snap/e2-code`
(worktree branch `rtb-pipeline`, commit a95bc73): every demonstrated behavioural defect fixed on Python 3.9 and 3.14, suite 35/35 in 21 s x3, exits 0.
Open: the 10 ms headroom rule has no discriminating test (a 10 ms window is below macOS sleep overshoot; my E2 recipe also asked for a 97 ms partner, only
3 ms inside the no-headroom deadline). Cosmetic: nothing else found.

## Per phase
| phase | wall | tool calls | result |
|---|---|---|---|
| c1 Clover coder | 18 min | 88 | claimed 20/20 pass; real defects: B8 deal ranking, B8 deal_floor dead + peeking test, B5 seat constant, B6 non-object JSON, multi-imp queueing, exit hang, no `__main__` |
| c1 MoVA pass A | 23 min | 69 | VERDICT FAIL, 2 findings (no `__main__`, exit hang): both real. Certified "all auction rules correct" while deal ranking and deal_floor were wrong |
| c1 MoVA pass B | 12.5 + 40 min | 59 + ~60 | attempt 1 lost its last tool call as plain text in the final message (no report); retry hit the 40-min cap (no report) |
| c2 Clover coder | 3 attempts, ~78 min | 19 + 43 + 74 | attempt 1 ended on an auto-rejected `external_directory` permission; attempt 2: coder **killed the llama-server** (see below); attempt 3 completed. Net effect: **worse than c1** (F2 fix = private-API copy, every process exit hangs, suite hangs after OK, crashes on 3.14) |
| c2 MoVA pass A, B | 40 + 40 min | 42 + 17 | both hit the cap, no report (first turn alone generated 16,116 tokens) |
| E1 Clover (Claude recipe) | 19 min | 45 | fixed 6 of 8 real items; seat still parsed from bid id; 3 tests could not fail |
| E2 Clover (Claude recipe) | 20 min | 59 | seat from partner name, tests that fail under mutation for seat / non-object JSON / non-daemon threads; headroom test not discriminating |
Server swaps: 12 s each, 8 total, no failures; one forced restart after the coder killed the server.

## MoVA as reviewer: scoreboard
- Passes attempted: 5 (c1 A, c1 B, c1 B retry, c2 A, c2 B); **usable: 1** (c1 A). [Corrected 2026-11-24: an earlier draft said 7.]
- c1 pass A vs my list of 7 demonstrated defects: recall 2/7 (29%), precision 2/2, 0 false positives, 1 false certification.
- Pre-registered expectation ("catches the spec-compliance classes, misses some concurrency/test-validity") was wrong in the first half: it missed B5, B6 and B8.
- Failure mechanisms observed: 48K window plus very long single thinking turns (16K tokens) leave no time for a report; trap 5 (last tool call emitted as text);
  a reviewer that only writes REVIEW.md at the very end loses everything on a timeout (pass B's mutation results were in its stream but never reported).

## Baseline comparison (same task, solo, Claude wrote recipes every round)
| | rounds of Claude recipes | agent time | note |
|---|---|---|---|
| K2-7B + Pi | 3-4 | ~hours | |
| Clover + Kilo | 5 | | |
| MoVA + Pi | 2, rerun 5 | 42 min, rerun ~3.5 h | |
| **Clover + MoVA pipeline** | **2** (E1, E2) | ~5 h 20 min incl. incidents and my polling | MoVA contributed 2 correct findings (of 7), then nothing. The 2 rounds are comparable to the best baselines, but E1/E2 were written by me knowing all earlier bug classes |

## My own errors (kept in the record)
1. Probe P9 (30 simultaneous POSTs) measured the listen backlog, not a defect; I reported it as "shared `self._pool` breaks concurrency" and put it into E1 as D2. Retracted in CLAUDE-c2.md.
2. E2's 97 ms headroom example was inside macOS sleep overshoot of the alternative deadline, so Clover's test cannot discriminate.
3. The reviewer prompt's checklist items ("malformed input of different shapes", "hostile partners", "network exposure") were written by someone who knew the earlier bugs, so MoVA's recall is an upper bound.
4. Harness bugs cost time, none cost model results: bash 3.2 empty-array (restarted before any model call), Pi blocking on stdin without `</dev/null`, `kilo run` ending on any auto-rejected permission (twice), no `kill` deny.
