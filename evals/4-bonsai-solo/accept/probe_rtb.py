"""Direct probes of an RTB exchange implementation (Bonsai solo run). Usage: cd <worktree>/pi-k2-rtb && python3 probe_rtb.py
Bypasses the HTTP/JSON layer where it is broken: builds BidRequest/Imp objects directly."""
import sys, time, threading, subprocess, textwrap, os
sys.path.insert(0, os.getcwd())
from rtb.models import BidRequest, Imp, Bid
from rtb.exchange import Exchange
from rtb.partners import MockPartner, DemandPartner
from rtb.auction import run_auction
R = []
def rec(name, ok, detail=""): R.append((name, ok)); print(("PASS " if ok else "FAIL ") + name + (("  - " + detail) if detail else ""))
def req(imps, tmax=100): return BidRequest(id="r", imp=imps, tmax=tmax)
def imp(i="1", floor=0.5): return Imp(id=i, bidfloor=floor)
def bid(p, price, impid="1", deal=None, dfloor=0.0, name=None): return Bid(id=(name or p)+"-b", impid=impid, price=price, adm="a", nurl="https://x/${AUCTION_PRICE}", dealid=deal, deal_floor=dfloor, partner=p)
# --- auction rules (pure)
w = run_auction(imp(), [bid("a", 1.0), bid("b", 0.8), bid("c", 0.6)]); rec("B1 3 bids: highest wins, pays second", w.partner == "a" and abs(w.price - 0.8) < 1e-9, str(w.price))
w = run_auction(imp(), [bid("a", 1.0)]); rec("B1 single bid pays floor", abs(w.price - 0.5) < 1e-9, str(w.price))
w = run_auction(imp(floor=0.7), [bid("a", 1.0), bid("b", 0.6)]); rec("floor drop does not set second price", abs(w.price - 0.7) < 1e-9, str(w.price))
w = run_auction(imp(), [bid("a", 0.9), bid("d", 0.9, deal="D")]); rec("B8 tie: deal beats open", w.partner == "d")
w = run_auction(imp(), [bid("d", 1.0, deal="D", dfloor=0.95), bid("b", 0.6)]); rec("B8 deal charged >= deal_floor, <= own bid", abs(w.price - 0.95) < 1e-9, str(w.price))
w = run_auction(imp(), [bid("d", 0.9, deal="D", dfloor=2.0), bid("b", 0.6)]); rec("B8 deal_floor capped at own bid", abs(w.price - 0.9) < 1e-9, str(w.price))
w = run_auction(imp(), [bid("a", 0.9), bid("b", 0.9)]); rec("tie: earlier in list wins", w.partner == "a")
w = run_auction(imp(), [bid("a", 0.0), bid("b", -1.0)]); rec("non-positive price ignored", w is None)
w = run_auction(imp(), [bid("a", 0.9, impid="zzz")]); rec("unknown impid ignored", w is None)
# --- exchange behaviour
class P(DemandPartner):
    def __init__(s, name, price, lat, fail=False, deal=None, dfloor=0.0): s.name, s.price, s.lat, s.fail, s.deal, s.dfloor = name, price, lat, fail, deal, dfloor
    def get_bid(s, imp_id, imp=None):
        if s.fail: raise RuntimeError("x")
        time.sleep(s.lat / 1000.0)
        return Bid(id=s.name + "-b", impid=imp_id, price=s.price, adm="a", nurl="n", dealid=s.deal, deal_floor=s.dfloor, partner=s.name)
t = time.monotonic(); r = Exchange([P("a", 1.0, 30), P("b", 0.8, 30), P("c", 0.6, 30)]).handle(req([imp()])); dt = (time.monotonic() - t) * 1000
rec("B2 partners concurrent (3 x 30 ms)", dt < 60, f"{dt:.0f} ms"); rec("  response price is clearing price", r is not None and abs(r.seatbid[0].bid[0].price - 0.8) < 1e-9, str(r.seatbid[0].bid[0].price if r else None))
t = time.monotonic(); r = Exchange([P("a", 1.0, 10), P("hung", 9.0, 3000)]).handle(req([imp()])); dt = (time.monotonic() - t) * 1000
rec("B3 hung 3 s partner does not block", dt < 110 and r is not None and r.seatbid[0].seat == "a", f"{dt:.0f} ms")
for lat in (60, 95, 97, 105):   # NOT 80: sleep(80 ms) in a thread arrives at ~87 ms (mean), 14/60 after the 90 ms deadline on this Mac
    acc = 0
    for _ in range(30):
        r = Exchange([P("a", 0.6, 5), P("late", 1.0, lat)]).handle(req([imp()]))
        if r is not None and r.seatbid[0].seat == "late": acc += 1
    exp_late = lat > 90   # deadline = tmax-10 = 90 ms; latencies within ~5 ms of it are unreliable on macOS (timer overshoot), 95 ms is only a sanity point
    rec(f"B4 partner at {lat} ms (deadline 90) {'rejected' if exp_late else 'accepted'}", (acc == 0) if exp_late else (acc == 30), f"late-winner {acc}/30")
r = Exchange([P("a", 1.0, 5), P("boom", 9.0, 0, fail=True)]).handle(req([imp()])); rec("raising partner = no-bid", r is not None and r.seatbid[0].seat == "a")
r = Exchange([P("a", 1.0, 40), P("b", 0.8, 40)]).handle(req([imp("1"), imp("2"), imp("3")]))
rec("multi-imp: 3 independent auctions", r is not None and len(r.seatbid) == 3 and sorted(b.impid for s in r.seatbid for b in s.bid) == ["1", "2", "3"], str(len(r.seatbid) if r else None))
t = time.monotonic(); r = Exchange([P("a", 1.0, 40), P("b", 0.8, 40)]).handle(req([imp("1"), imp("2"), imp("3"), imp("4")])); dt = (time.monotonic() - t) * 1000
rec("multi-imp not serialized (4 imps x 40 ms)", dt < 85, f"{dt:.0f} ms")
r = Exchange([P("my-partner", 1.0, 5), P("x", 0.5, 5)]).handle(req([imp()])); rec("B5 seat = partner name (hyphenated)", r is not None and r.seatbid[0].seat == "my-partner", str(r.seatbid[0].seat if r else None))
class Q(DemandPartner):
    name = "alpha"
    def get_bid(s, i, imp=None): return Bid(id="alpha-b", impid=i, price=1.0, adm="a", nurl="n", dealid=None, deal_floor=0.0, partner="")
r = Exchange([Q(), P("x", 0.5, 5)]).handle(req([imp()])); rec("B5b seat comes from the partner object (partner whose Bid omits it)", r is not None and r.seatbid[0].seat == "alpha", repr(r.seatbid[0].seat if r else None))
rec("deal tie via exchange", (lambda r: r is not None and r.seatbid[0].seat == "d")(Exchange([P("o", 0.9, 5), P("d", 0.9, 5, deal="D")]).handle(req([imp()]))))
# tie by arrival: faster partner wins an exact tie
rr = [Exchange([P("slowtie", 0.9, 25), P("fasttie", 0.9, 5)]).handle(req([imp()])).seatbid[0].seat for _ in range(10)]
rec("tie -> partner that answered first", rr.count("fasttie") == 10, str(rr.count("fasttie")) + "/10")
# --- process exit with a forever-hung partner
code = textwrap.dedent('''
import sys, time, os
sys.path.insert(0, os.getcwd())
from rtb.models import BidRequest, Imp
from rtb.exchange import Exchange
from rtb.partners import MockPartner
r = Exchange([MockPartner("a", 1.0, 5), MockPartner("hung", 9.0, 20000)]).handle(BidRequest(id="r", imp=[Imp(id="1", bidfloor=0.5)], tmax=100))
print("done", r is not None, flush=True)
''')
t = time.monotonic(); p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60); dt = time.monotonic() - t
rec("B11 process exits promptly with a 20 s partner still running", dt < 3, f"{dt:.1f} s")
print(f"\n{sum(1 for _, ok in R if ok)}/{len(R)} probes pass")
