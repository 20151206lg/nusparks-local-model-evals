#!/usr/bin/env python3
"""capwatch.py CAP IDLE_SECS PIDFILE KIND : pass a Pi/Kilo json stream through; SIGTERM the pid in PIDFILE when
(a) more than CAP tool calls started (KIND pi: tool_execution_start, kilo: tool_use) or (b) no stream line for IDLE_SECS.
Writes PIDFILE.count and PIDFILE.capped / PIDFILE.idle (only if that stop fired)."""
import sys, json, os, signal, threading, time
cap = int(sys.argv[1]); idle = int(sys.argv[2]); pf = sys.argv[3]; kind = sys.argv[4]
ev = "tool_execution_start" if kind == "pi" else "tool_use"
n = 0; fired = False; last = time.time(); done = False
def stop(tag, val):
    global fired
    if fired: return
    fired = True; open(pf + "." + tag, "w").write(str(val))
    try:
        pid = int(open(pf).read().strip()); os.kill(pid, signal.SIGTERM)
        def hard():  # a round that ignores SIGTERM (seen once: Pi kept running after the cap) gets SIGKILL after 10 s, children first
            time.sleep(10)
            try:
                import subprocess; subprocess.run(["pkill", "-KILL", "-P", str(pid)]); os.kill(pid, signal.SIGKILL)
            except Exception: pass
        threading.Thread(target=hard, daemon=True).start()
    except Exception as e: sys.stderr.write(f"capwatch: kill failed: {e}\n")
def watch():
    while not done:
        time.sleep(5)
        if time.time() - last > idle: stop("idle", int(time.time() - last))
threading.Thread(target=watch, daemon=True).start()
for line in sys.stdin:
    last = time.time(); sys.stdout.write(line); sys.stdout.flush()
    try: d = json.loads(line)
    except Exception: continue
    if d.get("type") == ev:
        n += 1
        if n > cap: stop("capped", n)
done = True
open(pf + ".count", "w").write(str(n))
