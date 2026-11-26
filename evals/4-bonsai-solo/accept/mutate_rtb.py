"""Mutation check: copy the worktree's pi-k2-rtb, put one bug back, run the suite; a test suite that stays green cannot guard that rule."""
import shutil, subprocess, sys, os, tempfile
SRC = os.path.abspath(sys.argv[1]); PY = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/python3"
M = [
 ("M1 shutdown(wait=True) (waits for hung partner)", "rtb/exchange.py", "pool.shutdown(wait=False)", "pool.shutdown(wait=True)"),
 ("M2 no deadline timeout (waits for all partners)", "rtb/exchange.py", "as_completed(futures, timeout=deadline - time.monotonic())", "as_completed(futures)"),
 ("M3 floor-first removed", "rtb/auction.py", "qualifying = [b for b in qualifying if b.price >= imp.bidfloor]", "pass"),
 ("M4 single bid pays its bid, not the floor", "rtb/auction.py", "clearing = imp.bidfloor\n    else:", "clearing = winner.price\n    else:"),
 ("M5 deal does not beat open on a tie", "rtb/auction.py", "return (-b.price, 0 if b.dealid else 1)", "return (-b.price, 1)"),
 ("M6 deal_floor not capped at own bid", "rtb/auction.py", "clearing = min(clearing, winner.price)", "pass"),
 ("M7 deal_floor ignored", "rtb/auction.py", "clearing = max(clearing, winner.deal_floor)", "pass"),
 ("M8 seat is a constant", "rtb/exchange.py", "SeatBid(seat=winner.partner, bid=[winner])", "SeatBid(seat='seat', bid=[winner])"),
 ("M9 no 10 ms headroom", "rtb/exchange.py", "HEADROOM_MS = 10", "HEADROOM_MS = 0"),
 ("M10 non-positive price accepted", "rtb/models.py", "return self.price > 0.0", "return True"),
 ("M11 ${AUCTION_PRICE} not substituted", "rtb/auction.py", 'nurl = winner.nurl.replace("${AUCTION_PRICE}", f"{clearing:.4f}")', "nurl = winner.nurl"),
 ("M12 partners called one after another", "rtb/exchange.py", "futures[pool.submit(self._fetch, imp, partner)] = (imp, partner)", "f = pool.submit(self._fetch, imp, partner); futures[f] = (imp, partner); f.result()"),
 ("M13 unknown impid accepted", "rtb/models.py", "return self.price > 0.0", "return self.price > 0.0 or True"),
 ("M14 late bids accepted (deadline +100 ms)", "rtb/exchange.py", "deadline = start + max(0.0, (req.tmax - HEADROOM_MS) / 1000.0)", "deadline = start + max(0.0, (req.tmax - HEADROOM_MS) / 1000.0) + 0.4"),
 ("N1 wait for every partner (join without timeout)", "rtb/exchange.py", "t.join(timeout=remaining)", "t.join()"),
 ("N2 non-daemon partner threads (exit hang)", "rtb/exchange.py", "daemon=True,", "daemon=False,"),
 ("N3 partners called one after another (join right after start)", "rtb/exchange.py", "t.start()\n                threads.append(t)", "t.start()\n                t.join()\n                threads.append(t)"),
 ("N5 arrival filter bypassed (late bids kept)", "rtb/exchange.py", "qualified_by_imp = self._filter_by_deadline(bids_by_imp, deadline)", "qualified_by_imp = {k: [b for (b, a) in v] for k, v in bids_by_imp.items()}"),
 ("N6 arrival time stamped after joining (filter always passes)", "rtb/exchange.py", "arrived = time.monotonic()", "arrived = 0.0"),
 ("N6b arrival time forced to 0.0 (patchable-clock version)", "rtb/exchange.py", "arrived = _now()", "arrived = 0.0"),
 ("N7 deadline 6 ms later (headroom shrunk)", "rtb/exchange.py", "deadline = start + max(0.0, (req.tmax - HEADROOM_MS) / 1000.0)", "deadline = start + max(0.0, (req.tmax - HEADROOM_MS) / 1000.0) + 0.006"),
 ("N4 no deadline wait at all (auction immediately)", "rtb/exchange.py", "if remaining > 0:", "if False:"),
]
def run(d):
    try:
        p = subprocess.run([PY, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=d, capture_output=True, text=True, timeout=90)
        names = frozenset(l.split(" ",1)[1].strip() for l in p.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:")))
        return p.returncode, names
    except subprocess.TimeoutExpired: return 124, frozenset(["TIMEOUT/hang"])
base = tempfile.mkdtemp(); d0 = os.path.join(base, "base"); shutil.copytree(SRC, d0, ignore=shutil.ignore_patterns("__pycache__")); B0 = run(d0)[1]; print("baseline failing tests:", sorted(B0))
for name, f, a, b in M:
    d = os.path.join(base, "m"); shutil.rmtree(d, ignore_errors=True); shutil.copytree(SRC, d, ignore=shutil.ignore_patterns("__pycache__"))
    s = open(os.path.join(d, f)).read()
    if a not in s: print(f"SKIP {name}: pattern not found"); continue
    open(os.path.join(d, f), "w").write(s.replace(a, b, 1)); rc, names = run(d)
    new = sorted(names - B0)
    print(f"{'CAUGHT  ' if new else 'SURVIVED'} {name}  (new failing: {', '.join(n.split()[0] for n in new)[:90] or 'none'})")
shutil.rmtree(base, ignore_errors=True)
