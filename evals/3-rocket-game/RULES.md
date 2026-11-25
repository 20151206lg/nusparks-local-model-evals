# Game rules the probes check (behaviour specification)

This is the written specification the acceptance oracle (`accept/rules_oracle.py`) is implemented from. It describes observable behaviour of a one-axis arcade launch game; it contains no code of any particular project.

**Constants.** gravity 9.8 m/s²; thrust acceleration 30 m/s²; fuel starts at 100 and burns 20 per second of thrust; heat starts at 0, rises 35 per second of thrust, falls 30 per second without thrust, and is limited to 0-100; countdown 3 s; flight limit 30 s; target altitude 150 m; altitude is limited to 0-1000 m.

**Phases.** `ready` -> `countdown` -> `flight` -> `result`. A fresh game is `ready`. Starting the countdown only does anything in `ready`. Reset returns every value to its initial state and the phase to `ready`, from any phase.

**Advancing time.** One call advances the game by a time step `dt` with a boolean "thrust requested". `dt` is first limited to the range 0 to 0.05 s. In `ready` and `result` nothing changes. In `countdown`, the remaining countdown time decreases by `dt`; when it reaches zero or below the phase becomes `flight` (no flight physics happen in that same call). The displayed countdown is the remaining time rounded **up** to a whole number, as text, only during the countdown (otherwise empty).

**One flight step**, in this order:
1. Thrust applies only if it is requested **and** fuel is above zero. With thrust: fuel decreases by 20·dt (not below 0), heat increases by 35·dt, vertical speed increases by (30 − 9.8)·dt. Without thrust: heat decreases by 30·dt, vertical speed decreases by 9.8·dt.
2. Altitude changes by vertical speed · dt and is limited to 0-1000. Vertical speed is not reset when the ground limit is hit.
3. The rocket counts as *airborne* once altitude has exceeded 0.001 m at any step; this never clears until reset.
4. Flight time increases by `dt`.
5. The first matching rule ends the round, in this priority: heat at 100 -> `overheat`; altitude 0 or below **and** airborne -> `ground_impact`; flight time at or above 30 s -> `time_limit`; altitude at or above 150 m -> `success`.
A finished round (`result`) never changes until reset.

Consequences worth testing: Space alone does not start anything; holding thrust from liftoff overheats (about 83 m); a rocket sitting on the pad with no thrust is not a ground impact; the round ends by itself after a win or loss.
