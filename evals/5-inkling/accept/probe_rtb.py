"""Direct and HTTP probes of an RTB exchange written by Inkling 2 Mini (its API: rtb.auction.resolve_impression, rtb.exchange.process_request,
rtb.partners.DemandPartner.bid(request)). Usage: cd <worktree>/pi-k2-rtb && python3 probe_rtb.py. Tied to this model's code; adapt for another."""
import sys, os, time, json, subprocess, textwrap, urllib.request, urllib.error, socket
sys.path.insert(0, os.getcwd())
from rtb.models import Bid, Imp, BidRequest
from rtb.auction import resolve_impression
from rtb.exchange import process_request
from rtb.partners import DemandPartner, MockPartner
R = []
def rec(name, ok, detail=""): R.append(ok); print(("PASS " if ok else "FAIL ") + name + (("  - " + detail) if detail else ""))
def bid(p, price, impid="1", deal=None, dfloor=0.0, seq=0): return Bid(id=p + "-b", impid=impid, price=price, adm="a", nurl="https://x/${AUCTION_PRICE}", dealid=deal, deal_floor=dfloor, partner=p, answer_seq=seq)
def req(n=1, tmax=100, floor=0.5): return BidRequest(id="r", imp=[Imp(id=str(i + 1), bidfloor=floor) for i in range(n)], tmax=tmax)
# --- pure auction
w, c = resolve_impression([bid("a", 1.0), bid("b", 0.8), bid("c", 0.6)], 0.5); rec("B1 3 bids: highest wins, pays second", w.partner == "a" and abs(c - 0.8) < 1e-9 and abs(w.price - 0.8) < 1e-9, f"{c}")
w, c = resolve_impression([bid("a", 1.0)], 0.5); rec("B1 single bid pays floor", abs(c - 0.5) < 1e-9, f"{c}")
w, c = resolve_impression([bid("a", 1.0), bid("b", 0.6)], 0.7); rec("floor drop does not set second price", abs(c - 0.7) < 1e-9, f"{c}")
w, c = resolve_impression([bid("a", 0.9, seq=0), bid("d", 0.9, deal="D", seq=1)], 0.5); rec("B8 tie: deal beats open", w.partner == "d")
w, c = resolve_impression([bid("d", 1.0, deal="D", dfloor=0.95), bid("b", 0.6)], 0.5); rec("B8 deal charged >= deal_floor", abs(c - 0.95) < 1e-9, f"{c}")
w, c = resolve_impression([bid("d", 0.9, deal="D", dfloor=2.0), bid("b", 0.6)], 0.5); rec("B8 deal_floor capped at own bid", abs(c - 0.9) < 1e-9, f"{c}")
w, c = resolve_impression([bid("a", 0.9, seq=1), bid("b", 0.9, seq=0)], 0.5); rec("tie: earlier arrival (answer_seq) wins", w.partner == "b")
rec("non-positive price ignored", resolve_impression([bid("a", 0.0), bid("b", -1.0)], 0.0) is None)
w, c = resolve_impression([bid("a", 1.0), bid("b", 0.8)], 0.5); rec("nurl ${AUCTION_PRICE} substituted", "0.8000" in w.nurl, w.nurl)
w, c = resolve_impression([bid("a", 1.0), bid("b", 0.8)], 0.5); rec("round to 4 decimals", resolve_impression([bid("a", 1.0), bid("b", 0.123456)], 0.0)[1] == 0.1235)
# --- exchange
class P(DemandPartner):
    def __init__(s, name, price, lat, fail=False, deal=None, dfloor=0.0): s.name, s.price, s.lat, s.fail, s.deal, s.dfloor = name, price, lat, fail, deal, dfloor
    def bid(s, request):
        if s.fail: raise RuntimeError("x")
        time.sleep(s.lat / 1000.0)
        return [Bid(id=s.name + "-" + i.id, impid=i.id, price=s.price, adm="a", nurl="n", dealid=s.deal, deal_floor=s.dfloor, partner=s.name) for i in request.imp]
def seats(r): return [s.seat for s in r.seatbid] if r else []
t = time.monotonic(); r = process_request(req(), [P("a", 1.0, 30), P("b", 0.8, 30), P("c", 0.6, 30)]); dt = (time.monotonic() - t) * 1000
rec("B2 partners concurrent (3 x 30 ms)", dt < 60, f"{dt:.0f} ms"); rec("  response price is the clearing price", r is not None and abs(r.seatbid[0].bids[0].price - 0.8) < 1e-9, str(r.seatbid[0].bids[0].price if r else None))
t = time.monotonic(); r = process_request(req(), [P("a", 1.0, 10), P("hung", 9.0, 3000)]); dt = (time.monotonic() - t) * 1000
rec("B3 hung 3 s partner does not block", dt < 110 and "a" in seats(r), f"{dt:.0f} ms")
for lat in (60, 95, 97, 105):
    acc = 0
    for _ in range(30):
        r = process_request(req(), [P("a", 0.6, 5), P("late", 1.0, lat)])
        if "late" in seats(r): acc += 1
    late = lat > 90
    rec(f"B4 partner at {lat} ms (deadline 90) {'rejected' if late else 'accepted'}", (acc == 0) if late else (acc == 30), f"late-winner {acc}/30")
r = process_request(req(), [P("a", 1.0, 5), P("boom", 9.0, 0, fail=True)]); rec("raising partner = no-bid", "a" in seats(r))
r = process_request(req(3), [P("a", 1.0, 40), P("b", 0.8, 40)]); n = sum(len(s.bids) for s in r.seatbid) if r else 0; rec("multi-imp: 3 independent auctions", n == 3, str(n))
t = time.monotonic(); process_request(req(4), [P("a", 1.0, 40), P("b", 0.8, 40)]); dt = (time.monotonic() - t) * 1000; rec("multi-imp not serialized (4 x 40 ms)", dt < 85, f"{dt:.0f} ms")
r = process_request(req(), [P("my-partner", 1.0, 5), P("x", 0.5, 5)]); rec("B5 seat = partner name (hyphenated)", seats(r) == ["my-partner"], str(seats(r)))
rr = [seats(process_request(req(), [P("slowtie", 0.9, 25), P("fasttie", 0.9, 5)]))[0] for _ in range(10)]; rec("tie via exchange -> partner that answered first", rr.count("fasttie") == 10, f"{rr.count('fasttie')}/10")
# --- process exit with a hung partner
code = textwrap.dedent('''
import sys, os
sys.path.insert(0, os.getcwd())
from rtb.models import BidRequest, Imp
from rtb.exchange import process_request
from rtb.partners import MockPartner
r = process_request(BidRequest(id="r", imp=[Imp(id="1", bidfloor=0.5)], tmax=100), [MockPartner("a", 1.0, 5), MockPartner("hung", 9.0, 20000)])
print("done", r is not None, flush=True)
''')
t = time.monotonic(); p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60); dt = time.monotonic() - t
rec("B11 process exits promptly with a 20 s partner still running", dt < 3, f"{dt:.1f} s")
# --- real HTTP server
def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
port = free_port(); srv = subprocess.Popen([sys.executable, "-m", "rtb.server", str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5)
def post(body, raw=False):
    data = body if raw else json.dumps(body).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/openrtb2/auction", data, {"Content-Type": "application/json"}), timeout=10); return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
try:
    s, b = post({"id": "req-1", "imp": [{"id": "1", "banner": {"w": 300, "h": 250}, "bidfloor": 0.5}], "tmax": 100})
    j = json.loads(b) if s == 200 else {}
    rec("HTTP valid request -> 200", s == 200, str(s))
    price = (j.get("seatbid") or [{}])[0].get("bid", [{}])[0].get("price") if s == 200 else None
    rec("HTTP response price is a clearing price (0.5 <= price < top bid)", price is not None and 0.5 <= price <= 1.0, str(price))
    rec("HTTP all bids below floor -> 204", post({"id": "r", "imp": [{"id": "1", "bidfloor": 9.0}]})[0] == 204)
    rec("HTTP malformed JSON -> 400", post(b"{bad", raw=True)[0] == 400)
    rec("HTTP non-object JSON (list) -> 400", post(b"[1,2]", raw=True)[0] == 400)
    rec("HTTP no imp -> 400", post({"id": "r"})[0] == 400)
    rec("HTTP no id -> 400", post({"imp": [{"id": "1"}]})[0] == 400)
    out = subprocess.run(f"lsof -nP -iTCP:{port} -sTCP:LISTEN", shell=True, capture_output=True, text=True).stdout
    rec("HTTP bound to loopback only", "127.0.0.1" in out and "*:" not in out, out.strip().splitlines()[-1][-30:] if out.strip() else "no listener")
finally: srv.terminate()
print(f"\n{sum(R)}/{len(R)} probes pass")
