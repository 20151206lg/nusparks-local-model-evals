"""Executable form of RULES.md (written from that document). Used only as the oracle of the controller acceptance probe.
API (what the probe needs): start_countdown(), advance(dt, thrust), reset(), get_countdown(), and the attributes phase, countdown_left,
altitude, vertical_speed, fuel, heat, flight_time, airborne, thrust_active, result_reason."""
import math

G, ACCEL, FUEL0, BURN_PER_S, HEAT_MAX, HEAT_UP, HEAT_DOWN = 9.8, 30.0, 100.0, 20.0, 100.0, 35.0, 30.0
COUNT_S, LIMIT_S, GOAL_M, CEILING_M, MAX_DT = 3.0, 30.0, 150.0, 1000.0, 0.05


def _limit(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Oracle:
    _INITIAL = dict(phase="ready", countdown_left=COUNT_S, altitude=0.0, vertical_speed=0.0, fuel=FUEL0, heat=0.0,
                    flight_time=0.0, airborne=False, thrust_active=False, result_reason="")

    def __init__(self):
        self.reset()

    def reset(self):
        for k, v in self._INITIAL.items():
            setattr(self, k, v)

    def start_countdown(self):
        if self.phase == "ready":
            self.phase, self.countdown_left = "countdown", COUNT_S

    def get_countdown(self):
        return str(math.ceil(self.countdown_left)) if self.phase == "countdown" else ""

    def advance(self, dt, thrust):
        dt = _limit(dt, 0.0, MAX_DT)
        if self.phase == "countdown":
            self.countdown_left -= dt
            if self.countdown_left <= 0.0:
                self.phase = "flight"
        elif self.phase == "flight":
            self._fly(dt, bool(thrust))

    def _fly(self, dt, thrust):
        burning = thrust and self.fuel > 0.0
        self.thrust_active = burning
        accel = (ACCEL if burning else 0.0) - G
        if burning:
            self.fuel = _limit(self.fuel - BURN_PER_S * dt, 0.0, FUEL0)
        self.heat = _limit(self.heat + (HEAT_UP if burning else -HEAT_DOWN) * dt, 0.0, HEAT_MAX)
        self.vertical_speed += accel * dt
        self.altitude = _limit(self.altitude + self.vertical_speed * dt, 0.0, CEILING_M)
        self.airborne = self.airborne or self.altitude > 0.001
        self.flight_time += dt
        outcome = next((name for name, hit in (
            ("overheat", self.heat >= HEAT_MAX),
            ("ground_impact", self.altitude <= 0.0 and self.airborne),
            ("time_limit", self.flight_time >= LIMIT_S),
            ("success", self.altitude >= GOAL_M)) if hit), None)
        if outcome:
            self.phase, self.result_reason = "result", outcome
