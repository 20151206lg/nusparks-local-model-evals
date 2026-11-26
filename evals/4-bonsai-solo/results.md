# Results: Ternary Bonsai 2.5 27B (Q2_0-mtp), Pi, thinking off, MTP off, 2026-11-25

One run per task. Times are agent time on the Mac. "Rounds" count the first attempt.

## Ad exchange (eval 1), solo

| Round | Time / tool calls | What we found |
|---|---|---|
| 1 (no shell) | 14.7 min / 24 | 20 tests written, 2 fail (both in `test_server`, stable over 3 runs). The exchange core was right: second price, floor first, deal tie-break, deal floor capped at the bid, clearing price in the response, a hung 3-second partner answered in 94 ms (no `with ThreadPoolExecutor` trap), partners concurrent (35 ms for three 30 ms partners), late bids rejected. **D1: every valid request got HTTP 400** (`Imp.from_dict` and `BidRequest.from_dict` were written as instance methods and called on the class). **D2: the process hung at exit until a still-sleeping partner finished** (non-daemon pool threads: 20.1 s with a 20 s partner). Its tests already guarded 12 of 13 distinct re-introduced bugs (the 14th mutation duplicated another; only the 10 ms headroom rule was unguarded). Its report said it had traced the code by hand; its three "least sure" rules did not include D1. |
| 2 (+ shell, fix list D1, D2) | 6.8 min / 11 | Both fixed (20 of 20 tests pass 5 times on Python 3.9 and 3.14; real HTTP gives 200, 204 and 400 correctly; exit 0.15 s). **New regression D3**: after rewriting the fan-out to daemon threads with `join(timeout)`, a bid arriving up to about 7 ms after the deadline still won (3 of 30 trials at 95 ms and 3 of 30 at 97 ms (a partner 5 ms and 7 ms past the 90 ms deadline)); the old code rejected 30 of 30. Its report checked exit time and the suite, not the deadline boundary. The daemon fix had no test (mutation survived). |
| 3 (D3, test for D2) | 11.3 min / 20 | Arrival time stamped in the worker thread and filtered against the deadline: 95/97/105 ms partners rejected 30 of 30. A daemon-thread test was added. The late-bid filter was only unit-tested in isolation: bypassing it, or forcing the arrival time to 0, left all tests green. |
| 4 (filter on the real path) | 11.1 min / 8 | Made the clock patchable and wrote a deterministic test through `Exchange.handle` with a fake thread-local clock (fast partner at 5 ms, late partner at 95 ms with the higher price). **All 17 distinct mutations are now caught (18 runs; one duplicates another), including the 10 ms headroom rule**, which no earlier run's tests could guard. Suite OK 8 times on 3.9 and on 3.14. |

Totals: 4 rounds, exchange correct after round 3, tests able to fail after round 4, 43.9 min, 63 tool calls, 22 tests. Same task earlier (exchange correct / tests can fail): K2-Horizon-7B 3/4, Clover 3/5, MoVA 2/2 in its first run; in its rerun the exchange first behaved correctly after round 2 and the final checks passed in round 5. Single runs, different tools: do not rank.
Minor, not scored: the seat is taken from the bid's own `partner` field, so a partner whose bid omits it gets an empty seat.

## Rocket game, Godot (cell G-bonsai)

- Ended on the **wall cap** (90 min, exit 124), 54 tool calls (14 reads, 34 bash, 3 writes, 3 edits, one of them failed), no final answer.
- Its first file write was call 47, about 70 minutes in (call 46 created a Git branch). The calls before it were mostly reading files and inspecting the rocket model with ad-hoc `node` scripts; the code was written in the last ~20 minutes (the controller was written twice) and never run.
- Acceptance: our probe **3 of 10** (the untouched project also scores 3); the project's own 18 tests and `godot:check` pass (they are the original tests and an asset check; the model added none). Its two new files (`rocket_launch_game.gd`, `rocket_launch_controller.gd`) do **not parse in Godot 4.7.2**: one uses Godot 3's `export` keyword, the other has an assignment inside an expression. Nothing references them; the scene is unchanged.
- Decode fell from 24 to about 10 tok/s as the context grew.

## Rocket game, Python and Panda3D (cell P-bonsai)

- Ended on the **wall cap** (90 min), 146 tool calls, no final answer (its last message was mid-bug-fix).
- It wrote `python_game/controller.py` (147 lines) and 16 passing tests within about 10 minutes (call 35). Our controller probe: **14 of 14 checks match the reference** (11 scenario comparisons, countdown timing, 300 random traces, no engine imports in the controller).
- The remaining ~110 calls went into getting on-screen text to work: after Arial would not load it searched system fonts, parsed TrueType tables and wrote a 253-line TrueType font generator (`_make_font.py`, 18 of its 25 writes and edits). **No app was written**: the app probe fails every scenario with "no instantiable ShowBase subclass". We do not think the detour was forced by the environment: when checked afterwards ([`accept/p_default_font_check.py`](accept/p_default_font_check.py), run with the rocket project's Python), a plain `TextNode` with Panda3D's built-in font laid out text without errors in the same install (`Panda3D 1.10.16 | TextNode with the default font, text 'hello': width 2.162 | lays out text: True`; this measures the text, nothing is drawn). What failed in its runs was loading a system font file, plus some errors from using the text functions.
- Not playable.

## Our own mistakes (kept in the record)

1. The first RTB round was started at medium reasoning effort by mistake and stopped after a few minutes, then restarted with thinking off. A quick count of completed reasoning blocks showed 34 characters, but unfinished reasoning was still streaming, so the log does not settle how much it thought; do not rely on that count. The aborted run's log is kept.
2. launchd keeps the job definition it loaded: our first "MTP off" test was really MTP on (and the thinking default had not applied). After `bootout` and `bootstrap`: decode 24.1 tok/s with MTP off against about 19 with it on, prefill 148-152 against 145 tok/s. The model card's gain from MTP is for the PQ2_0 file on PrismML's own llama.cpp fork, not stock b12387.
3. Our probes expected an 80 ms partner and a 95 ms partner to be "on time" against a 90 ms deadline. `sleep(80 ms)` in a thread arrives at about 87 ms on this Mac (14 of 60 after 90 ms), so the code was right and the probe was wrong. One mutation (M13) duplicated another.
4. The rocket acceptance watcher still listed the Clover cells and waited for them, so acceptance started about 15 minutes late (no effect on results).
