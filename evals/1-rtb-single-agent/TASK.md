# Task: build a real-time bidding (RTB) ad exchange server

You are building a small but correct OpenRTB 2.x-style **ad exchange**. A supply-side
platform (SSP) sends a bid request, and the exchange runs a sealed-bid **second-price
auction** across several demand partners (DSPs), all within a strict latency budget.

## Hard constraints

- **All files go under `pi-k2-rtb/`** (the folder this TASK.md is in). Every path below is
  relative to that folder. Do not create or edit anything outside it.
- **Python 3.9, standard library only.** No pip installs. Run as `python3 -m rtb.server`.
  Python 3.9 means: no `match`, no `X | None` annotations (use `Optional[X]`).
- You have `read`, `edit` and `write` tools but **no shell**: you cannot run code. Write
  carefully, keep the modules small, and make the tests deterministic so a human can run
  `python3 -m unittest -v` and get a clean pass on the first try.
- Work incrementally: write one file, re-read it if unsure, then move on.

## Layout to produce

```
rtb/
  __init__.py
  models.py      # dataclasses: BidRequest, Imp, BidResponse, SeatBid, Bid + from_json/to_json
  auction.py     # pure function: run the second-price auction (no I/O, no clock)
  partners.py    # DemandPartner interface + MockPartner (configurable latency, price, deal)
  exchange.py    # orchestrates one request: fan-out under a shared deadline, then auction
  server.py      # HTTP server: POST /openrtb2/auction
tests/
  test_auction.py
  test_exchange.py
  test_server.py
README.md        # how to run, design notes, known limitations
```

## API

`POST /openrtb2/auction` with an OpenRTB-style JSON body:

```json
{"id": "req-1",
 "imp": [{"id": "1", "banner": {"w": 300, "h": 250}, "bidfloor": 0.50, "bidfloorcur": "USD"}],
 "site": {"domain": "example.com"}, "device": {"ua": "...", "ip": "..."}, "tmax": 100}
```

- **200** with a `BidResponse` (`id`, `seatbid[].seat`, `seatbid[].bid[]` with `id`, `impid`,
  `price`, `adm`, `nurl`, optional `dealid`, and `cur`) when at least one impression fills.
  `price` in the response is the **clearing price** (what the winner is charged).
- **204 No Content** with an empty body when nothing fills. A no-fill is never an error.
- **400** for malformed JSON or a request with no `id` or no `imp`.
- `tmax` (milliseconds) is optional. Default 100. The exchange keeps 10 ms of headroom, so
  partners get `tmax - 10` ms.

## Auction rules (get these exactly right)

Run one independent auction **per impression**.

1. **Floor first.** Drop any bid with `price < bidfloor` *before* ranking. A dropped bid can
   never set the second price.
2. **Rank** remaining bids by price, highest first. On an exact tie, a **deal** bid
   (`dealid` set) beats an open bid; if still tied, the partner that answered first wins.
3. **Clearing price:**
   - two or more qualifying bids: `max(floor, second-highest qualifying price)`
   - exactly one qualifying bid: the **floor** (not the bid)
   - if the winner is a deal: also at least its `deal_floor`, and never more than its own bid
   - round to 4 decimal places
4. A bid for an `impid` that is not in the request is ignored. A bid with a non-positive or
   non-numeric price is ignored.
5. The win notice URL (`nurl`) from the partner may contain `${AUCTION_PRICE}`. Substitute
   the clearing price in the response.

## Latency rules

- **One shared deadline** for the whole request: `deadline = start + (tmax - 10) ms`,
  measured with `time.monotonic()`. Every partner call gets the *same* absolute deadline,
  not its own fresh timeout.
- Call all partners **concurrently** (threads via `concurrent.futures`, or `asyncio`).
- At the deadline, run the auction on whatever has arrived. Late bids are dropped, never
  awaited. A partner that raises an exception counts as no-bid; it must not break the request.
- The total handling time must stay under `tmax` even if a partner hangs forever.

## Partners

`MockPartner(name, price, latency_ms, deal_id=None, deal_floor=0.0, fail=False)` returns one
bid per impression after sleeping `latency_ms`, or raises if `fail=True`. The server starts
with four mocks: two fast open bidders, one deal partner, one that takes 500 ms (always late).

## Tests required (deterministic: no reliance on real timing for auction rules)

`test_auction.py` (pure function, no sleeps):
- 3 bids above floor → winner is highest, pays the second-highest
- 1 bid above floor → pays the floor
- bid below floor is excluded and does not set the second price
- tie between deal and open bid → deal wins
- deal winner is charged at least its `deal_floor` but never above its bid
- no qualifying bids → no winner
- `${AUCTION_PRICE}` substitution in `nurl`

`test_exchange.py`:
- a partner with latency far above the deadline is excluded and the call returns in well
  under `tmax` (generous margin, e.g. assert < tmax + 50 ms)
- a partner that raises does not break the auction
- two impressions run two independent auctions

`test_server.py` (start the server on a free port in a background thread):
- valid request → 200 and a well-formed response
- all bids below floor → 204
- malformed JSON → 400

## README

Explain the design choices behind the shared deadline and the second-price rules, how to run
the server and the tests, an example `curl`, and an honest list of what a production exchange
would need that this does not have.

## When you finish

List every file you wrote, then state which rules above you are least sure you got right.
