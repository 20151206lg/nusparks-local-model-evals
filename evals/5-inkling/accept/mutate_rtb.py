"""Mutation check for the exchange written by Inkling 2 Mini: copy the worktree's pi-k2-rtb, put one bug back, run the suite (discover -s tests);
a suite that does not gain a failing test cannot guard that rule. Tied to this model's code (patched source lines); adapt for another model."""
import shutil, subprocess, sys, os, tempfile
SRC = os.path.abspath(sys.argv[1]); PY = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/python3"
M = [
 ("M1 shutdown(wait=True) (waits for hung partner)", "rtb/exchange.py", "pool.shutdown(wait=False)", "pool.shutdown(wait=True)"),
 ("M2 no deadline timeout (waits for all partners)", "rtb/exchange.py", "timeout=remaining,", "timeout=None,"),
 ("M3 floor-first removed", "rtb/auction.py", "if b.price < bidfloor:", "if False:"),
 ("M4 single bid pays its bid, not the floor", "rtb/auction.py", "    else:\n        clearing = bidfloor", "    else:\n        clearing = ranked[0].price"),
 ("M5 deal does not beat open on a tie", "rtb/auction.py", "is_deal = 0 if bid.dealid else 1", "is_deal = 1"),
 ("M6 deal_floor not capped at own bid", "rtb/auction.py", "clearing = min(clearing, winner.price)", "pass"),
 ("M7 deal_floor ignored", "rtb/auction.py", "clearing = max(clearing, winner.deal_floor)", "pass"),
 ("M8 seat is a constant", "rtb/exchange.py", 'seat = bid.partner or "unknown"', 'seat = "seat"'),
 ("M9 no 10 ms headroom", "rtb/exchange.py", "HEADROOM_MS = 10", "HEADROOM_MS = 0"),
 ("M10 non-positive price accepted", "rtb/auction.py", "if b.price <= 0:", "if False:"),
 ("M11 ${AUCTION_PRICE} not substituted", "rtb/auction.py", 'winning.nurl = winning.nurl.replace("${AUCTION_PRICE}", "{:.4f}".format(clearing))', "pass"),
 ("M12 partners called one after another", "rtb/exchange.py", "futures[pool.submit(p.bid, request)] = p", "_f = pool.submit(p.bid, request); _f.exception(); futures[_f] = p"),
 ("M13 unknown impid accepted", "rtb/auction.py", "if b.impid not in valid_ids:", "if False:"),
 ("M14 late bids accepted (deadline +400 ms)", "rtb/exchange.py", "deadline = start + max(0.0, (request.tmax - headroom_ms)) / 1000.0", "deadline = start + max(0.0, (request.tmax - headroom_ms)) / 1000.0 + 0.4"),
 ("M15 arrival order ignored (ties by list order)", "rtb/auction.py", "return (-bid.price, is_deal, bid.answer_seq)", "return (-bid.price, is_deal, 0)"),
 ("M16 arrival order never recorded", "rtb/exchange.py", "b.answer_seq = answer_seq", "b.answer_seq = 0"),
 ("N1 deadline never checked (waits for every partner)", "rtb/exchange.py", "        if remaining <= 0:\n            break", "        if False:\n            break"),
 ("N2 non-daemon partner threads (exit hang)", "rtb/exchange.py", "daemon=True)", "daemon=False)"),
 ("N3 partners called one after another (join right after start)", "rtb/exchange.py", "        t.start()\n", "        t.start()\n        t.join()\n"),
 ("N4 arrival order: consume in list order, not by finish time", "rtb/exchange.py", 'h["finished_at"] < best_time', "False"),
 ("N5 a failing partner breaks the request", "rtb/exchange.py", "            holder[\"bids\"] = None", "            raise"),
]
def run(d):
    try:
        p = subprocess.run([PY, "-m", "unittest", "discover", "-s", "tests"], cwd=d, capture_output=True, text=True, timeout=90)
        return p.returncode, frozenset(l.split(" ", 1)[1].strip() for l in p.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:")))
    except subprocess.TimeoutExpired: return 124, frozenset(["TIMEOUT/hang"])
base = tempfile.mkdtemp(); d0 = os.path.join(base, "base"); shutil.copytree(SRC, d0, ignore=shutil.ignore_patterns("__pycache__")); B0 = run(d0)[1]; print("baseline failing tests:", sorted(B0))
ran = caught = 0
for name, f, a, b in M:
    d = os.path.join(base, "m"); shutil.rmtree(d, ignore_errors=True); shutil.copytree(SRC, d, ignore=shutil.ignore_patterns("__pycache__"))
    s = open(os.path.join(d, f)).read()
    if a not in s: print(f"SKIP {name}: pattern not found"); continue
    open(os.path.join(d, f), "w").write(s.replace(a, b, 1)); rc, names = run(d); new = sorted(names - B0); ran += 1; caught += bool(new)
    print(f"{'CAUGHT  ' if new else 'SURVIVED'} {name}  (new failing: {', '.join(n.split()[0] for n in new)[:90] or 'none'})")
print(f"{caught} caught of {ran} run"); shutil.rmtree(base, ignore_errors=True)
