"""Probes for the exchange written in the MEDIUM-effort arm (API: rtb.auction.settle_impression/run_auction, rtb.exchange.Exchange.handle,
partner.bid(request)->List[Bid], Bid.deal_id). Usage: cd <worktree>/pi-k2-rtb && python3 probe_rtb_medium.py. Tied to this code; adapt for another."""
import sys, os, time, json, subprocess, textwrap, urllib.request, urllib.error
sys.path.insert(0, os.getcwd())
from rtb.models import Bid, Imp, BidRequest
from rtb.auction import settle_impression, run_auction
from rtb.exchange import Exchange
from rtb.partners import DemandPartner, MockPartner
R = []
def rec(name, ok, detail=""): R.append(ok); print(("PASS " if ok else "FAIL ") + name + (("  - " + detail) if detail else ""))
def bid(p, price, impid="1", deal=None, dfloor=0.0, bid_id=None): return Bid(id=bid_id or (p + "-b"), impid=impid, price=price, adm="a", nurl="https://x/${AUCTION_PRICE}", deal_id=deal, deal_floor=dfloor, cur="USD")
def req(n=1, tmax=100, floor=0.5): return BidRequest(id="r", imp=[Imp(id=str(i + 1), bidfloor=floor) for i in range(n)], tmax=tmax)
imp = Imp(id="1", bidfloor=0.5)
w = settle_impression(imp, [bid("a", 1.0), bid("b", 0.8), bid("c", 0.6)]); rec("B1 3 bids: highest wins, pays second", w.id == "a-b" and abs(w.price - 0.8) < 1e-9, f"{w.price}")
w = settle_impression(imp, [bid("a", 1.0)]); rec("B1 single bid pays floor", abs(w.price - 0.5) < 1e-9, f"{w.price}")
w = settle_impression(Imp(id="1", bidfloor=0.7), [bid("a", 1.0), bid("b", 0.6)]); rec("floor drop does not set second price", abs(w.price - 0.7) < 1e-9, f"{w.price}")
w = settle_impression(imp, [bid("a", 0.9), bid("d", 0.9, deal="D")]); rec("B8 tie: deal beats open", w.id == "d-b")
w = settle_impression(imp, [bid("d", 1.0, deal="D", dfloor=0.95), bid("b", 0.6)]); rec("B8 deal charged >= deal_floor", abs(w.price - 0.95) < 1e-9, f"{w.price}")
w = settle_impression(imp, [bid("d", 0.9, deal="D", dfloor=2.0), bid("b", 0.6)]); rec("B8 deal_floor capped at own bid", abs(w.price - 0.9) < 1e-9, f"{w.price}")
w = settle_impression(imp, [bid("a", 0.9), bid("b", 0.9)]); rec("tie: earlier in list wins", w.id == "a-b")
rec("non-positive price ignored", settle_impression(Imp(id="1", bidfloor=0.0), [bid("a", 0.0), bid("b", -1.0)]) is None)
rec("unknown impid ignored", settle_impression(imp, [bid("a", 0.9, impid="zzz")]) is None)
w = settle_impression(imp, [bid("a", 1.0), bid("b", 0.8)]); rec("nurl ${AUCTION_PRICE} substituted", "0.8" in w.nurl and "${" not in w.nurl, w.nurl)
rec("round to 4 decimals", abs(settle_impression(Imp(id="1", bidfloor=0.0), [bid("a", 1.0), bid("b", 0.123456)]).price - 0.1235) < 1e-9)
class P(DemandPartner):
    def __init__(s, name, price, lat, fail=False, deal=None, dfloor=0.0, bid_id=None): s.name, s.price, s.lat, s.fail, s.deal, s.dfloor, s.bid_id = name, price, lat, fail, deal, dfloor, bid_id
    def bid(s, request):
        if s.fail: raise RuntimeError("x")
        time.sleep(s.lat / 1000.0)
        return [Bid(id=s.bid_id or (s.name + "-" + i.id), impid=i.id, price=s.price, adm="a", nurl="n", deal_id=s.deal, deal_floor=s.dfloor, cur="USD") for i in request.imp]
def seats(r): return [s.seat for s in r.seatbid]
def top(r): return r.seatbid[0].bids[0].price
t = time.monotonic(); r = Exchange([P("a", 1.0, 30), P("b", 0.8, 30), P("c", 0.6, 30)]).handle(req()); dt = (time.monotonic() - t) * 1000
rec("B2 partners concurrent (3 x 30 ms)", dt < 120, f"{dt:.0f} ms"); rec("  response price is the clearing price", abs(top(r) - 0.8) < 1e-9, str(top(r)))
t = time.monotonic(); r = Exchange([P("a", 1.0, 5), P("b", 0.8, 10)]).handle(req(tmax=100)); dt = (time.monotonic() - t) * 1000
rec("BW returns once every partner has answered (5 and 10 ms partners, tmax 100)", dt < 50, f"{dt:.0f} ms (deadline is 90 ms)")
t = time.monotonic(); r = Exchange([P("a", 1.0, 10), P("hung", 9.0, 3000)]).handle(req()); dt = (time.monotonic() - t) * 1000
rec("B3 hung 3 s partner does not block", dt < 110 and "a" in seats(r), f"{dt:.0f} ms")
for lat in (60, 95, 97, 105):
    acc = 0
    for _ in range(30):
        r = Exchange([P("a", 0.6, 5), P("late", 1.0, lat)]).handle(req())
        if "late" in seats(r): acc += 1
    late = lat > 90
    rec(f"B4 partner at {lat} ms (deadline 90) {'rejected' if late else 'accepted'}", (acc == 0) if late else (acc == 30), f"late-winner {acc}/30")
r = Exchange([P("a", 1.0, 5), P("boom", 9.0, 0, fail=True)]).handle(req()); rec("raising partner = no-bid", "a" in seats(r))
r = Exchange([P("a", 1.0, 40), P("b", 0.8, 40)]).handle(req(3)); rec("multi-imp: 3 independent auctions", sum(len(s.bids) for s in r.seatbid) == 3)
t = time.monotonic(); Exchange([P("a", 1.0, 40), P("b", 0.8, 40)]).handle(req(4)); dt = (time.monotonic() - t) * 1000; rec("multi-imp not serialized (4 x 40 ms)", dt < 120, f"{dt:.0f} ms")
r = Exchange([P("my-partner", 1.0, 5), P("x", 0.5, 5)]).handle(req()); rec("B5 seat = partner name (hyphenated)", seats(r) == ["my-partner"], str(seats(r)))
r = Exchange([P("alpha", 1.0, 5, bid_id="same"), P("beta", 0.5, 5, bid_id="same")]).handle(req()); rec("B5c seat correct when two partners reuse a bid id", seats(r) == ["alpha"], str(seats(r)))
rr = [seats(Exchange([P("slowtie", 0.9, 25), P("fasttie", 0.9, 5)]).handle(req()))[0] for _ in range(6)]; rec("tie via exchange -> partner that answered first", rr.count("fasttie") == 6, f"{rr.count('fasttie')}/6")
code = textwrap.dedent('''
import sys, os
sys.path.insert(0, os.getcwd())
from rtb.models import BidRequest, Imp
from rtb.exchange import Exchange
from rtb.partners import MockPartner
r = Exchange([MockPartner("a", 1.0, 5), MockPartner("hung", 9.0, 20000)]).handle(BidRequest(id="r", imp=[Imp(id="1", bidfloor=0.5)], tmax=100))
print("done", flush=True)
''')
t = time.monotonic(); subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60); dt = time.monotonic() - t
rec("B11 process exits promptly with a 20 s partner still running", dt < 3, f"{dt:.1f} s")
srv = subprocess.Popen([sys.executable, "-m", "rtb.server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5); port = 8080
def post(body, raw=False):
    data = body if raw else json.dumps(body).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/openrtb2/auction", data, {"Content-Type": "application/json"}), timeout=10); return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
try:
    s, b = post({"id": "req-1", "imp": [{"id": "1", "banner": {"w": 300, "h": 250}, "bidfloor": 0.5}], "tmax": 100}); rec("HTTP valid request -> 200", s == 200, str(s))
    if s == 200:
        j = json.loads(b); price = j["seatbid"][0]["bid"][0]["price"]; rec("HTTP response price is the deal winner paying its deal floor (1.50 bid, floor 1.40, default partners)", abs(price - 1.4) < 1e-9, str(price))
    rec("HTTP all bids below floor -> 204", post({"id": "r", "imp": [{"id": "1", "bidfloor": 9.0}]})[0] == 204)
    rec("HTTP malformed JSON -> 400", post(b"{bad", raw=True)[0] == 400)
    rec("HTTP non-object JSON (list) -> 400", post(b"[1,2]", raw=True)[0] == 400)
    rec("HTTP no imp -> 400", post({"id": "r"})[0] == 400)
    rec("HTTP no id -> 400", post({"imp": [{"id": "1"}]})[0] == 400)
    out = subprocess.run(f"lsof -nP -iTCP:{port} -sTCP:LISTEN", shell=True, capture_output=True, text=True).stdout
    rec("HTTP bound to loopback only", "127.0.0.1" in out and "*:" not in out, out.strip().splitlines()[-1][-30:] if out.strip() else "no listener")
finally: srv.terminate()
print(f"\n{sum(R)}/{len(R)} probes pass")
