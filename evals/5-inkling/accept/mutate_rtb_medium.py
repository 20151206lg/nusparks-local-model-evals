"""Mutation check for the exchange written in the MEDIUM-effort arm (patches its source lines; tied to that code)."""
import shutil, subprocess, sys, os, tempfile
SRC = os.path.abspath(sys.argv[1]); PY = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/python3"
M = [
 ("N2 non-daemon partner threads (exit hang)", "rtb/exchange.py", "daemon=True).start()", "daemon=False).start()"),
 ("M14 late bids accepted (wait +400 ms)", "rtb/exchange.py", "all_answered.wait(timeout=remaining_budget)", "all_answered.wait(timeout=remaining_budget + 0.4)"),
 ("M9 no 10 ms headroom", "rtb/exchange.py", "HEADROOM_MS = 10", "HEADROOM_MS = 0"),
 ("BW always waits out the full deadline (never returns early)", "rtb/exchange.py", "                    if remaining[0] <= 0:\n                        all_answered.set()", "                    if remaining[0] <= 0:\n                        pass"),
 ("M17 seat is a constant", "rtb/exchange.py", 'seat = winner.seat if winner.seat else "unknown"', 'seat = "seat"'),
 ("M19 seat taken from the first bid that arrived (id/partner mix-up)", "rtb/exchange.py", "b.seat = partner.name", "b.seat = arrived[0].seat if arrived else partner.name"),
 ("M12 partners called one after another", "rtb/exchange.py", "threading.Thread(target=collect, args=(partner,), daemon=True).start()", "_t = threading.Thread(target=collect, args=(partner,), daemon=True); _t.start(); _t.join()"),
 ("M16 arrival index never recorded", "rtb/exchange.py", "b.arrival = next(arrival_counter)", "b.arrival = 0"),
 ("M15 arrival index ignored in the tie-break", "rtb/auction.py", "0 if t[1].deal_id else 1, t[0]),", "0 if t[1].deal_id else 1, 0),"),
 ("M3 floor-first removed", "rtb/auction.py", "if float(bid.price) < floor:", "if False:"),
 ("M4 single bid pays its bid, not the floor", "rtb/auction.py", "    else:\n        clearing = floor", "    else:\n        clearing = float(ranked[0][1].price)"),
 ("M5 deal does not beat open on a tie", "rtb/auction.py", "0 if t[1].deal_id else 1", "1"),
 ("M6 deal_floor not capped at own bid", "rtb/auction.py", "clearing = min(clearing, float(winner_bid.price))", "pass"),
 ("M7 deal_floor ignored", "rtb/auction.py", "clearing = max(clearing, deal_floor)", "pass"),
 ("M10 non-positive price accepted", "rtb/auction.py", "if not _is_usable_price(bid.price):", "if False:"),
 ("M11 ${AUCTION_PRICE} not substituted", "rtb/auction.py", "nurl = winner_bid.nurl.replace(AUCTION_PRICE_TOKEN, price_str)", "nurl = winner_bid.nurl"),
 ("M13 unknown impid accepted", "rtb/auction.py", "if bid.impid != imp.id:", "if False:"),
]
def run(d):
    try:
        p = subprocess.run([PY, "-m", "unittest"], cwd=d, capture_output=True, text=True, timeout=90)
        return p.returncode, frozenset(l.split(" ", 1)[1].strip() for l in p.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))), p.stderr.strip().splitlines()[-3:]
    except subprocess.TimeoutExpired: return 124, frozenset(["TIMEOUT/hang"]), []
base = tempfile.mkdtemp(); d0 = os.path.join(base, "base"); shutil.copytree(SRC, d0, ignore=shutil.ignore_patterns("__pycache__")); B0 = run(d0)[1]; print("baseline failing tests:", sorted(B0))
ran = caught = 0
for name, f, a, b in M:
    d = os.path.join(base, "m"); shutil.rmtree(d, ignore_errors=True); shutil.copytree(SRC, d, ignore=shutil.ignore_patterns("__pycache__"))
    s = open(os.path.join(d, f)).read()
    if a not in s: print(f"SKIP {name}: pattern not found"); continue
    open(os.path.join(d, f), "w").write(s.replace(a, b, 1)); rc, names, _ = run(d); new = sorted(names - B0); ran += 1; caught += bool(new)
    print(f"{'CAUGHT  ' if new else 'SURVIVED'} {name}  (new failing: {', '.join(n.split()[0] for n in new)[:90] or 'none'})")
print(f"{caught} caught of {ran} run"); shutil.rmtree(base, ignore_errors=True)
