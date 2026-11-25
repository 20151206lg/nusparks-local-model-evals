# Eval 2: one coder, one reviewer, an orchestrator

**Question:** if a second local model reviews the coder's work, does the loop converge faster than the solo runs in eval 1, and how much of the hosted assistant's review work does it replace?

**Setup:** coder = Clover via Kilo; reviewer = MoVA via Pi; a hosted assistant (Claude Code) orchestrates, relays the reviewer's findings to the coder **verbatim**, writes its own independent review that is never shown to either model, and runs the final acceptance. The two models never run at once; `bin/swap.sh` swaps the server (about 12 s).

## Files

- `PLAN.md`: run 1 plan and rules ("I relay, I do not coach"; blind order; reviewer never sees the coder's self-report).
- `PLAN2.md`: run 2 with a **fixed reviewer protocol** (findings appended as found, narrow passes by spec section, tool-call caps, last action a `VERDICT:` line).
- `prompts/`: coder (`C1`, `Cn`), reviewer (`R-common`, `R-A1..A3`, `R-B`), escalation recipes (`E1`, `E2`). `v1/` holds run 1's reviewer prompts.
- `bin/`: `swap.sh`, `phase_code.sh`, `phase_review.sh`, `phase_esc.sh`, `capwatch.py` (caps on time, tool calls, idleness), `summarize.py` (JSON event stream to one line per event), `collect_review.sh`, `tl.sh` (timeline log).
- `kilo-pipeline.jsonc`: Kilo config used (bash allowed with an explicit deny list; webfetch and external directories denied).
- `results-run1.md`, `results-run2.md`: scoring of both runs.

## Procedure in one screen

```
for cycle in 1..3:
  swap clover; coder phase (cap 45 min, tool-call cap)    # C1 first, then Cn + the review file
  commit snapshot
  swap mova; reviewer passes (A1, A2, A3 spec sections; B test mutation), each with its own cap
  orchestrator writes its own review of the same snapshot (not shared)
after the loop: up to 2 escalation rounds written by the orchestrator (E1, E2)
score: reviewer recall/precision against the defects the orchestrator demonstrated, rounds to correct, wall time
```

## What we found (two runs; anecdotes)

- Run 1: 5 reviewer passes, 1 usable; recall 2 of 7 real defects, plus a false "all auction rules verified". The coder's second cycle was worse than its first. Correct only after 2 orchestrator-written escalation rounds. About 5 h 20 min.
- Run 2 (fixed reviewer protocol): 10 of 12 reviewer reports usable (appending findings as found survives timeouts). Initial recall rose (2 of 7 to 4 of 7 in the first cycle), but some defects (the constant seat, the tie order) were never reported in any cycle, and every spec-rules pass certified a wrong rule as correct. Still needed the 2-round escalation cap.
- Neither run was clearly better than the solo runs in eval 1 on this task (counts of orchestrator-written rounds are only loosely comparable). In these two runs the protocol fixed reviewer *reporting*, not reviewer *judgement*.

## Caveats

- In the plans and results, `rtb-spec` means a git branch that holds only the original task file, here [`../1-rtb-single-agent/TASK.md`](../1-rtb-single-agent/TASK.md); the first line of `PLAN.md` step edits the "no shell" bullet as described in eval 1.
- Historical procedure. `PLAN.md` expects a branch `rtb-spec` with the original task and `PLAN2.md` names acceptance scripts (`probe_c1.py`, `mutate.py`) that are not included; you must write your own probes for the task's bug classes (see eval 1).
- Run 1 and run 2 used different reviewer protocols and escalation recipes written by the orchestrator knowing earlier bug classes; compare their counts with care, and do not read the ~5 h wall times as a speed comparison between protocols.
- Tool-call caps are enforced from outside by `capwatch.py` for the reviewer, plus an external wall-clock limit; the coder phase uses a wall limit only.
- The reviewer (Pi) has an unrestricted `bash`. Run this in a disposable environment.

## Reproducing

The scripts expect the task checkout (a git worktree of the task repo) in `$RUN/work` (see `bin/env.sh`; `W` must stay inside `RUN`) and LaunchAgents for the two servers on macOS (`swap.sh` documents what it expects). On Linux you would replace `swap.sh` with your own server management. Read `PLAN.md` first.
