#!/usr/bin/env python3
"""capwatch.py CAP PIDFILE : pass a Pi json stream through; SIGTERM the pid in PIDFILE once more than CAP tool calls started.
Writes PIDFILE.count (tool calls seen) and PIDFILE.capped (only if the cap fired)."""
import sys, json, os, signal
cap = int(sys.argv[1]); pf = sys.argv[2]; n = 0; fired = False
for line in sys.stdin:
    sys.stdout.write(line); sys.stdout.flush()
    try: d = json.loads(line)
    except Exception: continue
    if d.get("type") == "tool_execution_start":
        n += 1
        if n > cap and not fired:
            fired = True
            open(pf + ".capped", "w").write(str(n))
            try: os.kill(int(open(pf).read().strip()), signal.SIGTERM)
            except Exception as e: sys.stderr.write(f"capwatch: kill failed: {e}\n")
open(pf + ".count", "w").write(str(n))
