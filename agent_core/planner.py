"""Deterministic observing agent with joint pointing and exposure optimisation.

Protocol handling, weather notices and conservative fault reporting live here.
SearchPlanner supplies the ledger-aware search implemented in search.py and
optimizer.py. RuntimeAdvisor integrates a bounded, configurable Kimi-compatible model.
"""
from __future__ import annotations

from datetime import timedelta
from time import perf_counter

from .geometry import format_utc, parse_utc, wrap180
from .llm_client import LLMClient
from .memory import TraceLog
from .search import SearchPlanner
from .expert_observer import ExpertObserver as RuntimeAdvisor
from .report_budget import budgeted_report
from .pointing_calibration import PointingCalibration

BLOCKING_KINDS = {"terrain_obstruction", "rocket_launch"}
DIRECTION_AZ = {"N": 0.0, "NE": 45.0, "E": 90.0, "SE": 135.0, "S": 180.0,
                "SW": 225.0, "W": 270.0, "NW": 315.0}

REPORT_DROP = 0.62
REPORT_RECOVERY = 0.80
REPORT_CONFIRMATIONS = 3
REPORT_SPACING_HOURS = 6.0
MAX_REPORTS = 2


def _az_distance(a: float, b: float) -> float:
    return abs(wrap180(a - b))


def _bulletin_text(notices: list) -> str:
    """A human-readable rendering of a bulletin's notices, for the LLM call that reads
    "live bulletin text" rather than structured JSON."""
    if not notices:
        return "clear (no active notices)"
    return "; ".join(f"{n.get('event_kind')} {n.get('direction')}" for n in notices)


class Planner(RuntimeAdvisor, SearchPlanner):
    def __init__(self, state, log=lambda text: None):
        self.state = state
        self.log = log
        self.grid = state.fiber_grid
        self.mount = PointingCalibration(state, log)
        self.llm = LLMClient(log=log)
        self.trace = TraceLog(log=log)

        self.observe_count = 0
        self.reports = 0
        self.last_report_hours = float("-inf")
        self.suspicion_hours: list[float] = []
        self.night_index_seen: int | None = None
        self.consecutive_reports = 0
        self._last_forecast_notices: list = []
        self.total_assigned = 0
        self.total_hit = 0
        self.mean_exposure_seconds = 900.0
        self._plan_costs = [None, None, None]
        self._plan_counts = [0, 0, 0]
        self._init_advisor()

        log(f"planner: {len(state.ids)} targets ({sum(state.required)} required), "
            f"{len(state.nights)} nights, model_configured={self.llm.configured}")

    # -- top-level decision ----------------------------------------------------

    def decide(self, payload: dict) -> dict:
        self._begin_advice_decision(payload)
        state = self.state
        now = parse_utc(payload["now_utc"])
        hours = (now - state.survey_start).total_seconds() / 3600.0

        for message in payload.get("new_messages", []):
            if message.get("record_type") == "forecast":
                self._last_forecast_notices = message.get("notices", [])
        self.mount.consume(payload.get("last_result"))
        self.mount.notice(payload.get("latest_bulletin"))
        state.on_messages(payload.get("new_messages", []), payload.get("latest_bulletin"))
        state.on_result(payload.get("last_result"), hours)
        self._expert_after_result(payload, hours)
        self.active_requests = payload.get("active_requests") or []
        last_result = payload.get("last_result")
        if last_result and last_result.get("action") == "observe":
            self.total_assigned += int(last_result.get("assigned_count", 0))
            self.total_hit += int(last_result.get("hit_count", 0))
        self._pace(payload, now)

        night = state.current_night(now)
        if night is None:
            nxt = state.next_night_start(now)
            if nxt is None:
                return {"action": "finish", "reason": "no observing night left"}
            return {"action": "wait", "until_utc": format_utc(nxt), "reason": "daytime: sleep until the next night"}
        night_index, night_start, night_end = night

        if self.night_index_seen != night_index:
            self.night_index_seen = night_index
            self._night_advice(night_start, payload)

        if (night_end - now).total_seconds() < state.min_exposure:
            nxt = state.next_night_start(now)
            if nxt is None:
                return {"action": "finish", "reason": "survey over"}
            return {"action": "wait", "until_utc": format_utc(nxt), "reason": "night ending"}

        if state.site_closed():
            return {"action": "wait", "duration_seconds": self._to_next_slot(now, night_start),
                    "reason": "bulletin: rain/storm over the whole sky"}

        report = self._maybe_report(hours, payload)
        if report is not None:
            return report

        started = perf_counter()
        model_before = self.llm.seconds_spent
        action = self.plan(now, night_end, night_index, hours)
        # Model selection waits occur inside plan(), but do not recur on every
        # search. Charge them to real wall time, not the search-cost estimate.
        model_wait = max(0., self.llm.seconds_spent - model_before)
        elapsed = max(0., perf_counter() - started - model_wait)
        tier = state.fast_level
        previous = self._plan_costs[tier]
        self._plan_costs[tier] = elapsed if previous is None else .8 * previous + .2 * elapsed
        self._plan_counts[tier] += 1
        if action is None:
            return {"action": "wait", "duration_seconds": self._to_next_slot(now, night_start),
                    "reason": "nothing useful is up"}
        action = self.mount.correct(action)
        self.observe_count += 1
        self.mean_exposure_seconds = 0.95 * self.mean_exposure_seconds + 0.05 * action["duration_seconds"]
        action["reason"] = f"{len(action['assignments'])} fibres, program {action['program']}"
        action["decision_source"] = self._decision_source
        return action

    def on_finish(self, payload: dict) -> None:
        self._advisor_summary()
        self.trace.write({"event": "finish", **payload})
        self.trace.close()
        self.log(f"planner: finished termination_reason={payload.get('termination_reason')} "
                 f"observes={self.observe_count} reports={self.reports} llm_calls={self.llm.calls_made}")

    def note_action(self, action: dict) -> None:
        """Called by agent.py right after an action is validated, so the consecutive-report
        counter (enforced by validation.py) stays correct even when a fallback replaced it."""
        self.consecutive_reports = self.consecutive_reports + 1 if action.get("action") == "report" else 0
        self.mount.remember(action, self._current_payload.get("now_utc"))

    def _to_next_slot(self, now, night_start) -> int:
        slot = self.state.slot_seconds
        into = (now - night_start).total_seconds() % slot
        return int(max(60, min(3600, slot - into if into else slot)))

    def _pace(self, payload: dict, now) -> None:
        """Use full search until the actual runtime reserve requires fallback."""
        remaining = float((payload.get("wallclock") or {}).get("remaining_seconds", 1e9))
        level = 0 if remaining > 180. else 2
        if level != self.state.fast_level:
            self.log(f"planner: steady pace level {level} ({remaining:.1f}s remaining)")
            self.state.fast_level = level

    # -- instrument fault reporting (deterministic rules + LLM confirmation) -----

    def _maybe_report(self, hours: float, payload: dict):
        fallback = budgeted_report(self, hours, payload)
        if fallback is not None:
            return fallback
        self._expert_review(hours, payload)
        return self._expert_report(hours, payload)

    def _baseline_report(self, hours: float, payload: dict):
        state = self.state
        state.force_program = None
        if self.reports >= MAX_REPORTS or hours - self.last_report_hours < 24.0:
            return None
        evidence = state.fault_evidence(current_hours=hours)
        threshold = REPORT_DROP if self.reports == 0 else REPORT_DROP - 0.07
        # Dense short exposures may temporarily leave the recent sample window
        # covering only one night. That is missing evidence, not recovery.
        # Preserve independent confirmations across nights, bounded to 72 hours.
        self.suspicion_hours = [when for when in self.suspicion_hours if hours - when <= 72.0]
        if evidence is None:
            return None
        # Hysteresis: starting suspicion requires a large drop, while clearing
        # it requires a measured recovery. Borderline noise must not repeatedly
        # erase independent confirmations of a still-degraded instrument.
        recovery = REPORT_RECOVERY if self.reports == 0 else REPORT_RECOVERY - 0.05
        if evidence.drop >= recovery:
            self.suspicion_hours = []
            return None
        if evidence.drop >= threshold and not self.suspicion_hours:
            return None
        if evidence.dark_checks < 6:
            state.force_program = "DARK"
        elif evidence.dark_matched < 0.5 * evidence.dark_checks:
            self.suspicion_hours = []
            return None
        if self.suspicion_hours and hours - self.suspicion_hours[-1] < REPORT_SPACING_HOURS:
            return None
        self.suspicion_hours.append(hours)
        if len(self.suspicion_hours) < REPORT_CONFIRMATIONS:
            return None
        self.suspicion_hours = []
        verdict = self._fault_advice(evidence)
        if verdict is False:
            self.log(f"planner: report vetoed by the model at {payload.get('now_utc')} ({evidence})")
            self.last_report_hours = hours
            return None
        self.reports += 1
        self.last_report_hours = hours
        state.forget_quality_history()
        self.log(f"planner: reporting instrument fault at {payload.get('now_utc')} evidence={evidence}")
        return {"action": "report", "reason": f"quality dropped to {evidence.drop:.0%} of the earlier level",
                "decision_source": "llm-confirmed" if verdict else "rule"}

    # -- planning value / achievability -----------------------------------------

    def _direction_factor(self, alt: float, az: float) -> float:
        state = self.state
        for direction in state.terrain:
            if direction in DIRECTION_AZ and alt < 50.0 and _az_distance(az, DIRECTION_AZ[direction]) <= 60.0:
                return 0.0
        factor = 1.0
        for key in state.notices:
            kind, _, direction = key.partition("|")
            if direction not in DIRECTION_AZ:
                continue
            near = _az_distance(az, DIRECTION_AZ[direction]) <= 67.5
            if kind in BLOCKING_KINDS and near and alt < 62.0:
                return 0.0
            if near and alt < 75.0:
                factor = min(factor, 0.35)
        for direction in state.extra_avoid:
            if direction in DIRECTION_AZ and _az_distance(az, DIRECTION_AZ[direction]) <= 67.5 and alt < 70.0:
                factor = min(factor, 0.35)
        for blocked_az, blocked_alt in state.blocked[-40:]:
            if _az_distance(az, blocked_az) <= 12.0 and alt <= blocked_alt + 3.0:
                factor = min(factor, 0.2)
        return factor
