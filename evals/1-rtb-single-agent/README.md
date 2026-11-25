# Eval 1: one local coder builds a real-time-bidding exchange, round by round

**Task:** [`TASK.md`](TASK.md): a small OpenRTB-style ad exchange (HTTP server, second-price auction per impression, one shared latency deadline, concurrent partners, tests). Python 3.9 standard library only. The task is deliberately full of classic traps (the clearing price is not the bid; a `with ThreadPoolExecutor` block waits for a hung partner; late bids race the deadline).

**Why this task:** its rules are exact enough to check by running code, and it needs concurrency and timing, where small models tend to write plausible code and tests that cannot fail.

## Procedure (one model + agent per run)

1. Start from a clean checkout containing only `TASK.md` (the task says all files go under `pi-k2-rtb/`; keep that folder name or edit the task). Use the same task text for every model.
2. **Round 1: no shell.** The agent has `read`, `edit`, `write` only, as `TASK.md` says. Do not help.
3. **Verify by running, not by reading the agent's summary.** Run the test suite several times (a flaky or hanging suite is a defect), then probe the server directly (see the bug classes below).
4. **Round 2 onward: give the agent `bash`** (change the "no shell" bullet to "You have `bash`: run the tests before you finish and again after your last edit. Use `timeout 120` on every command that runs tests or the server" and drop "so a human can run"). Send a fix list that names only defects you demonstrated.
5. Repeat until two things are true: the exchange behaves correctly, **and** the tests can fail. Check the second by mutation: break the code in a copy in the way each test claims to guard, and confirm the test fails.
6. Record: rounds to correct exchange, rounds until tests can fail, agent time, which claims in the agent's own final report were false.

Agent settings: Pi with `-nc --offline --tools read,edit,write[,bash]`, stdin from `/dev/null`; Kilo with a copy of its config where `bash` is allowed except an explicit deny list (see eval 2's `kilo-pipeline.jsonc`). Models and server flags: [`docs/models-and-hardware.md`](../../docs/models-and-hardware.md).

## Bug classes to score against

| tag | class |
|---|---|
| B1 | response `price` is the bid, not the clearing price; a single bid must pay the floor |
| B2 | partners called sequentially |
| B3 | `with ThreadPoolExecutor` waits for a hung partner (a 3 s partner blocks the response) |
| B4 | late-bid race: a bid finishing after the deadline is accepted |
| B5 | seat derived from the bid id instead of the partner |
| B6 | non-object JSON body crashes the handler (must be 400) |
| B7 | server bound to 0.0.0.0 instead of loopback |
| B8 | floor/deal rules: floor before ranking, deal tie-break, `deal_floor` capped at own bid |
| B9 | busy-spin or re-collecting finished futures |
| B10 | tests that cannot fail (peek at mock internals, pass against the bug) |
| B11 | hang at exit (non-daemon thread; `unittest` never returns) |
| B12 | flaky tests |
| B13 | edits outside the allowed folder, or to `TASK.md` |

## Results we got (Mac, one run per setup; an anecdote)

| | K2-Horizon-7B + Pi | Clover + Kilo | MoVA + Pi (run 1) | MoVA + Pi (rerun) |
|---|---|---|---|---|
| failing tests after round 1 | 8 | 0 (but serious bugs untested) | 1 failure + 2 errors (the failure was a real bug its own test caught) | 9 failures + 1 import error (0 tests discovered at first) |
| rounds until the exchange was correct | 3 | 3 | 2 | 5 |
| rounds until tests could fail | 4 | 5 | 2 | 5 |
| agent's final report accurate | no | no | no (invented a "truncated" spec) | no |

Every setup needed an external reviewer to run mutation checks and write fix recipes. The reruns show a wide spread for the same model (2 vs 5 rounds). Details of the rerun, and traps hit, are in [`docs/lessons.md`](../../docs/lessons.md).

The exact round-by-round prompts of these runs were not saved as files; the procedure above is reconstructed from our notes. If you rerun, save every prompt and the agent's stream.
