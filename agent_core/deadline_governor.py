"""Calendar credit for the explicit real-time deadline, alongside CPU credit.

The delivered clock difference includes both agent and evaluator time. It is
not charged as CPU, and is not attributed to model latency or a specific task.
"""
import math

from .calendar_governor import CalendarGovernor
from .geometry import parse_utc


def wall_remaining(payload):
    value = (payload.get('wallclock') or {}).get('wall_remaining_seconds')
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value >= 0. else None


class DeadlineGovernor:
    def __init__(self, nights, minimum_exposure):
        self.credit = CalendarGovernor(nights, minimum_exposure)
        self.previous = None
        self.available = False
        self.measured_intervals = 0
        self.measured_wall = 0.
        self.interventions = 0
        self.last_forecast = None

    def consume(self, payload):
        remaining = wall_remaining(payload)
        self.available = remaining is not None
        previous, self.previous = self.previous, None
        if remaining is None or previous is None:
            return
        old_remaining, old_now, tier, searched = previous
        elapsed = old_remaining - remaining
        advance = (parse_utc(payload['now_utc']) - old_now).total_seconds()
        # Missing/reset clocks are not evidence of free or negative work.
        if elapsed < 0. or advance < 0.:
            self.available = False
            return
        self.credit.record(elapsed, tier, searched, advance)
        self.measured_intervals += 1
        self.measured_wall += elapsed

    def remember(self, payload, tier, searched):
        remaining = wall_remaining(payload)
        self.previous = None if remaining is None else (
            remaining, parse_utc(payload['now_utc']), tier, searched)

    def choose(self, now, remaining, cpu_tier, current):
        if not self.available:
            self.last_forecast = {'reason': 'explicit_wall_clock_unavailable'}
            return cpu_tier
        wall_tier = self.credit.choose(now, max(0., remaining), current, 0)
        chosen = max(cpu_tier, wall_tier)
        self.interventions += chosen > cpu_tier
        self.last_forecast = dict(self.credit.last_forecast or {},
                                  cpu_tier=cpu_tier, wall_tier=wall_tier,
                                  remaining_wall_seconds=remaining)
        return chosen
