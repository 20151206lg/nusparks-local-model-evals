# Models, servers and agents used

Hardware: Apple M3 Max (30-core GPU), 36 GB unified memory, macOS. Two large models do not fit at once (about 21 GB + 24 GB), so tests that use both **swap** the server (`evals/2-rtb-coder-reviewer-pipeline/bin/swap.sh`, about 12 s per swap).

| Role | Model | Quantization / file | Server | Agent |
|---|---|---|---|---|
| Coder | Clover-35B-A3B Preview (DiffuSpace; run as an ordinary autoregressive model) | IQ4_XS GGUF, 18.9 GB, from [`maternion/Clover-35B-A3B-Preview-GGUF`](https://huggingface.co/maternion/Clover-35B-A3B-Preview-GGUF); chat template: the GGUF has none embedded, so we used the `chat_template.jinja` published by DiffuSpace for this model (exact source URL was not recorded: take it from the DiffuSpace model page) | `llama.cpp` b12063 | Kilo CLI 7.8.32 |
| Coder or reviewer | K2-Horizon-MoVA-36B-A4B (IFM) | IQ4_XS GGUF, 20.4 GB, by [`bartowski`](https://huggingface.co/bartowski/K2-Horizon-MoVA-36B-A4B-GGUF) | `llama.cpp` b12387 in the rocket game and in the second RTB pipeline run; b12063 in the first solo RTB run (with `--reasoning-format none`) | Pi 1.5.2 |
| Coder (test 1 only) | K2-Horizon-7B (IFM) | Q8_0 GGUF, 9.6 GB (official [`IFM/K2-Horizon-7B-GGUF`](https://huggingface.co/IFM/K2-Horizon-7B-GGUF)) | `llama.cpp` b12063 | Pi 1.5.2 |
| Coder (eval 4) | Ternary Bonsai 2.5 27B (PrismML; Qwen3.8-27B base, ternary weights) | `Ternary-Bonsai-2.5-27B-Q2_0-mtp.gguf`, 7.91 GB, from [`prism-ml/Ternary-Bonsai-2.5-27B-GGUF`](https://huggingface.co/prism-ml/Ternary-Bonsai-2.5-27B-GGUF), Apache 2.0 | stock `llama.cpp` b12387 (needs b11556 or newer for `Q2_0`) | Pi 1.5.2 |
| Orchestrator and acceptance checker | a hosted assistant (Claude Code) | n/a | hosted | n/a |

Server flags used for Clover and for MoVA in the rocket-game and pipeline runs (MoVA's first solo RTB run used b12063; its rerun used b12387 with default reasoning parsing before `--reasoning-format none` was added), with paths shortened (paths shortened, `$MODELS` is where you keep the GGUF files):

```bash
# Clover (port 8000): 126,976-token context = 108K input + 16K output; thinking off
llama-server -m $MODELS/Diffuspace-Clover-35B-A3B-Preview-IQ4_XS.gguf \
  -ngl 99 -c 126976 -fa on -np 1 --repeat-penalty 1.0 --cache-ram 0 \
  --jinja --chat-template-file $MODELS/chat_template.jinja \
  --chat-template-kwargs '{"enable_thinking":false}' --host 127.0.0.1 --port 8000

# MoVA (port 8001): 49,152 context, q8 KV cache, thinking kept inside the reply
llama-server -m $MODELS/K2-Horizon-MoVA-36B-A4B-IQ4_XS.gguf \
  -c 49152 -fa on -ctk q8_0 -ctv q8_0 --cache-ram 0 -np 1 --jinja \
  --reasoning-format none --host 127.0.0.1 --port 8001
```

Notes that matter for reproduction:

- Clover needs a `llama.cpp` build from after its architecture support merged (b12063 or newer); Homebrew's older build cannot load it.
- MoVA's chat template has no switch to turn thinking off. Medium reasoning effort fits an agent loop; high effort spent a whole 16K-token output budget thinking. `--reasoning-format none` avoids turns lost when the model never closes its thinking block.
- MoVA's weights plus a 48K window leave almost no GPU headroom on 36 GB: do not start anything else that uses the GPU while it runs.
- Run Pi with `-nc` (no context files) so a large `AGENTS.md` in a parent folder does not eat the window; give it `</dev/null` in headless mode or it waits on stdin forever.
- Sampling for MoVA via Pi: temperature 1.0, top_p 0.95 (the vendor's recommendation).

Server flags for Bonsai (eval 4), thinking off and MTP off (see `evals/4-bonsai-solo/server/com.bonsai.server.plist.example`):

```bash
# Bonsai (port 8001): 131,072-token context, thinking off, no MTP
llama-server -m $MODELS/Ternary-Bonsai-2.5-27B-Q2_0-mtp.gguf -ngl 99 -c 131072 -fa on -np 1 --jinja \
  --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0 --chat-template-kwargs '{"enable_thinking":false}' \
  --host 127.0.0.1 --port 8001
```

`--min-p 0` overrides llama.cpp's default of 0.05 (the model card asks for it). MoVA is no longer run on the Mac that produced these results (its file was deleted on 2026-11-25); the MoVA rows above are history.

