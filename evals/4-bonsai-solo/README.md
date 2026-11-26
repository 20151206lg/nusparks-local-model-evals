# Eval 4: Ternary Bonsai 2.5 27B, one model on two tasks (three runs)

> **Read the safety section first.** These scripts run an autonomous coding agent with a shell and run code it wrote; use a disposable environment. The rocket harness (eval 3, patched here) can **enable, disable and restart your macOS LaunchAgents** (`com.llamacpp.server`, `com.k2horizon.server`, `com.bonsai.server`) and refuses to run unless you set `EVAL_ALLOW_SERVICE_CHANGES=1`; read `swap.sh` first. See [Safety](#safety).

**Question:** how does a 7.9 GB ternary 27B model (PrismML's Ternary Bonsai 2.5 27B, `Q2_0` file with the MTP head, run on stock llama.cpp b12387) do on the tasks from evals 1 and 3: the ad-exchange task, round by round, and the rocket game in Godot and in Python with Panda3D? One run per task, one Mac, so these are anecdotes, not a ranking.

## Setup

- Model: [`prism-ml/Ternary-Bonsai-2.5-27B-GGUF`](https://huggingface.co/prism-ml/Ternary-Bonsai-2.5-27B-GGUF), file `Ternary-Bonsai-2.5-27B-Q2_0-mtp.gguf` (7.91 GB, sha256 `b0f83de8481c3200c529aef5fb495dbfedf2a4a3f017f7a3ea0a69c67be1d306`). Apache 2.0 per the Hugging Face page when we checked (2026-11-25); the exact revision was not recorded.
- Server: stock `llama-server` build b12387 (`Q2_0` needs b11556 or newer; older builds load it silently and produce garbage), flags in [`server/com.bonsai.server.plist.example`](server/com.bonsai.server.plist.example). **Thinking off** (`--chat-template-kwargs '{"enable_thinking":false}'`, and Pi's thinking level `off`) and **MTP off**: on this Mac, with this stock build, MTP made decode slower (see below).
- Agent: Pi 1.5.2, `-nc` (no context files), model config `contextWindow` 131072, `maxTokens` 16384, temperature 1.0 and top_p 0.95 (top_k 20 and min_p 0 on the server).
- Hardware: Apple M3 Max, 30-core GPU, 36 GB. Measured with thinking off: decode **24.1 tok/s** at the start of a conversation and about 10 tok/s after tens of thousands of tokens of context; prefill 112-152 tok/s (a 13K-token prompt took 88 s); server RSS 17.4 GB at `-c 131072`; needle retrieval correct at 13K, 26K and 53K tokens; 30 of 30 tool calls parsed at medium reasoning effort.
- Hosted assistant (Claude Code): wrote the fix lists, probes and mutation checks, audited every round, and decided what counted as correct. The local model made every repair.

## Procedure

1. **Eval 1 (ad exchange), solo.** [`bin/init_run.sh`](bin/init_run.sh) makes a worktree from a branch holding only [eval 1's `TASK.md`](../1-rtb-single-agent/TASK.md). Round 1: [`prompts/C1.txt`](prompts/C1.txt), tools `read,edit,write` only (no shell, as the task says). After each round the assistant ran the suite repeatedly, [`accept/probe_rtb.py`](accept/probe_rtb.py) (direct probes of the rules) and [`accept/mutate_rtb.py`](accept/mutate_rtb.py) (put each bug back in a copy; a test suite that stays green cannot guard that rule), read the code and Pi's report, then sent a fix list naming only demonstrated defects ([`prompts/R2.txt`](prompts/R2.txt) to `R4.txt`) with `bash` enabled. [`bin/round.sh`](bin/round.sh) runs a round with wall, tool-call and idle caps enforced from outside.
2. **Eval 3 (rocket game), Godot and Python.** Same harness as eval 3 with a `bonsai` target instead of `mova`: [`rocket-bonsai.patch`](rocket-bonsai.patch) is the small change to `swap.sh` and `run_cell.sh` (apply from the repository root with `patch -p1 < evals/4-bonsai-solo/rocket-bonsai.patch`). Each cell: wall cap 90 min, tool-call cap 400, idle cap 1200 s, same prompts and acceptance probes as eval 3. Run `run_cell.sh G bonsai 90 400` then `run_cell.sh P bonsai 90 400`, and `run_accept.sh <cell>` for each.

The probes and mutation checks in `accept/` are tied to the exchange this model wrote (its class names and module layout, and the exact source lines the mutations patch), so they need adapting for another model's code. The mutation list marks each mutation as caught or survived by comparing failing test names with the unmutated baseline.

## Result in one screen

| Task | Result | Time, calls |
|---|---|---|
| Ad exchange (eval 1) | Exchange correct after round 3, tests able to fail after round 4; all 17 distinct mutation checks caught | 43.9 min agent time over 4 rounds, 63 calls |
| Rocket game, Godot | No playable game: probe 3 of 10 (the untouched project also scores 3 of 10); its two new scripts do not parse in Godot 4.7.2 and nothing references them | wall cap (90 min), 54 calls |
| Rocket game, Python/Panda3D | Rules code matches the reference on 14 of 14 checks; no app was written, so not playable | wall cap (90 min), 146 calls |

Details, per-round tables and our own mistakes: [`results.md`](results.md). Traps for anyone rerunning this: [`../../docs/lessons.md`](../../docs/lessons.md) items 15-20.

## Safety

Same warnings as the other evals: no sandbox here. Pi has no permission system, the shims block commands by name only, and the probes execute code the model wrote. Use a disposable environment. `server/` contains an example LaunchAgent only; `bin/round.sh` does not change services.
