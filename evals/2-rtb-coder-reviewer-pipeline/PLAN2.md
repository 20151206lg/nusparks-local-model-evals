# Pipeline test, run 2: same task, fixed reviewer protocol (2026-11-24)

Run 1 (see `runs/20261123-2045/score.md`, AGENTS.md section "Pipeline test") failed at the reviewer: 5 passes, 1 usable, recall 29%,
one false "all correct". Run 2 changes ONLY the reviewer protocol; coder side, task, swap, caps for the coder, honesty rules are unchanged
from PLAN.md. Frozen run-1 reviewer files: `v1/`.

## What changes (reviewer only)
| run 1 | run 2 | targets |
|---|---|---|
| REVIEW.md written once at the very end | each finding appended to REVIEW.md the moment it is demonstrated; each passed item appended to CHECKED.md with its command | a timeout/cap lost everything (3 of 5 passes) |
| two broad passes (A, B) | four narrow passes: A1 auction rules, A2 API+server+constraints, A3 latency/concurrency/partners, B test mutation; scopes follow TASK.md section headings, **no bug named, no input shape hinted** | 16K-token turns, 48K window |
| "ok" claims free-form (false certification of ranking/deal_floor) | `ok:` line only with the command that was run; I audit CHECKED.md against my probes | false certification |
| 40-min cap per pass | hard cap per pass: tool calls A1 45, A2 45, A3 55, B 90; minutes 20/20/25/35. `capwatch.py` SIGTERMs pi at the cap; partial files kept; no retry | runaway turns, retry after timeout |
| "short reasoning steps, one command, record, move on" instruction | added | very long single turns |
| last action: final answer text | last action: append `VERDICT:` line by bash, then reply `done` | trap 5 (last tool call lost as text) |
Findings get pass-prefixed IDs (A1-1 ...) so the concatenated REVIEW.md has no ID clashes; Clover receives only findings, never CHECKED.md.

## Unchanged
Loop cap 3 cycles; coder 45 min; Clover bash from round 1 with the deny list (incl. `kill`); fresh worktree from `rtb-spec` + the same TASK.md edit
(patch 0001 of run 1); blind order; reviewer never sees the coder's self-report; I relay, add no hints; escalation rounds by me max 2, counted separately;
stop the loop when all four passes say `VERDICT: PASS`; abort rules as in PLAN.md.

## Comparability caveats (written before the run)
- Clover is not deterministic: cycle-1 code will differ from run 1's. Recall is measured against defects I demonstrate in THIS run's snapshot (probe_c1.py P1-P12 + mutate.py, extended as needed).
- Scopes are derived from spec headings only, so recall may be lower than run 1's checklist-assisted 29% for input-shape bugs; that is the honest number.
- Protocol smoke test: pass A1 on run 1's c1 snapshot (7 known defects) in `runs/20261124-0835` (smoke, not part of the result).

## Scoring (same as PLAN.md, plus)
Per pass: finished / CAPPED / TIMEOUT, tool calls, findings, ok lines, findings that are real vs false, ok lines that are false (audited), time.
Headline: usable passes of 4 per cycle (run 1: 1 of 5 in total), recall/precision on demonstrated defects, false-ok count, escalation rounds needed.

## End state
Run 2 ends by restoring Clover as default (user decision 2026-11-24): `swap.sh clover` -> `com.llamacpp.server` enabled + running on :8000,
`com.k2horizon.server` disabled. Verify with health, one listener, a liveness generation. Then remove worktree/branch of run 2 only on the user's word.
