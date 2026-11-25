#!/usr/bin/env python3
"""Condense a Pi (--mode json) or Kilo (--format json) event stream on stdin to one line per step."""
import sys, json, time
def short(v, n=110):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"
t0 = time.time()
def out(s): print(f"{int(time.time()-t0)//60:02d}:{int(time.time()-t0)%60:02d} {s}", flush=True)
for line in sys.stdin:
    try: d = json.loads(line)
    except Exception: continue
    t = d.get("type")
    if t == "tool_execution_start":      # Pi
        a = d.get("args", {})
        out(f"TOOL {d.get('toolName')} {short(a.get('command') or a.get('path') or a)}")
    elif t == "tool_execution_end":
        r = d.get("result", {}); txt = ""
        c = r.get("content") if isinstance(r, dict) else None
        if c: txt = c[0].get("text", "")
        out(f"  -> {'ERR' if d.get('isError') else 'ok'} {d.get('durationMs')}ms {short(txt, 90)}")
    elif t == "turn_end":
        m = d.get("message", {}); u = m.get("usage", {}) or {}
        out(f"turn end (out={u.get('output')}, total={u.get('totalTokens')}, stop={m.get('stopReason')})")
    elif t == "agent_settled":
        out(f"AGENT SETTLED aborted={d.get('aborted')}")
    elif t == "tool_use":                 # Kilo
        p = d.get("part", {}); st = p.get("state", {}); i = st.get("input", {}) or {}
        arg = i.get("command") or i.get("filePath") or i.get("path") or i
        res = (st.get("output") or st.get("error") or "")
        out(f"TOOL {p.get('tool')} {short(arg)}  -> {st.get('status')} {short(res, 70)}")
    elif t == "step_finish":
        p = d.get("part", {}); k = p.get("tokens", {})
        out(f"step end (prompt={k.get('input')}, out={k.get('output')}, {p.get('reason')}, {p.get('time',{}).get('elapsed')}ms)")
    elif t == "text":
        out("TEXT " + short(d.get("part", {}).get("text", ""), 160))
    elif t == "error":
        out("ERROR " + short(d.get("error", d), 200))
