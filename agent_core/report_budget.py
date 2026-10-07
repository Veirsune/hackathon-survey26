"""Spend public free-report allowance on sustained, unexplained throughput loss."""
from statistics import median
from datetime import timedelta

from .geometry import parse_utc


def all_sky_weather(notices):
    """Quakes have their own geometry/cooldown gate; sky attenuation is different."""
    for notice in notices:
        if isinstance(notice, str):
            kind, _, direction = notice.partition("|")
        else:
            kind, direction = notice.get("event_kind"), notice.get("direction")
        if direction == "ALL" and kind not in ("earthquake", "terrain_obstruction"):
            return True
    return False


def track_notice(state, bulletin):
    active = any(n.get("event_kind") == "earthquake" for n in (bulletin or {}).get("notices", ()))
    if active and not getattr(state, "_earthquake_active", False):
        stamp = (bulletin or {}).get("issued_at_utc")
        if stamp:
            state._earthquake_seen_hours = (parse_utc(stamp) - state.survey_start).total_seconds() / 3600
    state._earthquake_active = active


def collect_exposure(state, hours):
    ratios = [ratio for when, ratio in state._samples if when == hours]
    if len(ratios) < 3:
        return
    rows = getattr(state, "_diagnostic_exposures", [])
    rows.append((hours, state.pending_night, median(ratios)))
    state._diagnostic_exposures = [r for r in rows[-128:] if hours - r[0] <= 96.]
    paid_rows = getattr(state, "_weather_clear_diagnostic_exposures", [])
    if (not getattr(state, "_pending_sky_weather", True)
            and not all_sky_weather(getattr(state, "notices", ()))):
        paid_rows.append((hours, state.pending_night, median(ratios)))
    state._weather_clear_diagnostic_exposures = [r for r in paid_rows[-128:] if hours - r[0] <= 96.]


def early_free_diagnostic(planner, hours, paid):
    """Public membership consistency is evidence of pointing recovery, not fault proof."""
    if paid:
        return False
    state = planner.state
    age = hours - getattr(state, "_earthquake_seen_hours", float("-inf"))
    if not 4 * 24 <= age < 7 * 24:
        return False
    # Stronger than the normal paid ALL-sky gate: no current sky warning anywhere.
    for notice in state.notices:
        kind = notice.partition("|")[0] if isinstance(notice, str) else notice.get("event_kind")
        if kind not in ("earthquake", "terrain_obstruction"):
            return False
    mount = getattr(planner, "mount", None)
    if mount is None or len(mount.history) < 3:
        return False
    count = sum(len(points) for _, _, points in mount.history)
    return count >= 24 and mount.errors(mount.offset) <= .02 * count


def budgeted_report(planner, hours, payload):
    state = planner.state
    state.force_program = None
    result = payload.get("last_result") or {}
    if (getattr(planner, "_await_report_result", False) and result.get("action") == "report"
            and isinstance(result.get("correct"), bool)):
        if result["correct"]:
            planner._false_since_correct = 0
            planner._last_false_hours = float("-inf")
            planner._last_false_ratio = 1.
            state._diagnostic_exposures = []
            state._weather_clear_diagnostic_exposures = []
            state.forget_quality_history()
        else:
            planner._false_since_correct = getattr(planner, "_false_since_correct", 0) + 1
            planner._last_false_hours = hours
            planner._last_false_ratio = getattr(planner, "_pending_report_ratio", 1.)
        planner._await_report_result = False
    if getattr(planner, "_await_report_result", False):
        return None
    used = getattr(planner, "_false_since_correct", 0)
    paid = used >= state.false_report_free_allowance
    if paid:
        if all_sky_weather(getattr(state, "notices", ())):
            return None
        if getattr(planner, "_paid_diagnostic_attempts", 0) >= 1:
            return None
        now = state.survey_start + timedelta(hours=hours)
        remaining_hours = sum(max(0., (end - max(start, now)).total_seconds()) / 3600
                              for start, end in state.nights)
        if remaining_hours < 24.:
            return None
    # The original free path remains identical. Paid actions use stricter gates.
    original = None if paid else planner._baseline_report(hours, payload)
    if original is not None:
        planner._await_report_result = True
        planner._pending_report_ratio = .6
        return original
    if hours - planner.last_report_hours < 48.:
        return None
    quake = getattr(state, "_earthquake_seen_hours", float("-inf"))
    early = early_free_diagnostic(planner, hours, paid)
    quake_guard = 4 * 24 if early else 7 * 24
    if hours - quake < quake_guard:
        return None
    older = [ratio for when, _, ratio in state.clean_history if when < hours - 72.]
    if len(older) < 32:
        return None
    reference = median(older)
    history_key = "_weather_clear_diagnostic_exposures" if paid or early else "_diagnostic_exposures"
    rows = [r for r in getattr(state, history_key, ())
            if hours - r[0] <= 48. and r[0] - quake >= quake_guard]
    nights = {}
    for when, night, ratio in rows:
        nights.setdefault(night, []).append((when, ratio))
    if len(nights) < 2:
        return None
    recent_nights = sorted(nights)[-2:]
    if recent_nights[1] - recent_nights[0] != 1:
        return None
    groups = [nights[n] for n in recent_nights]
    if min(map(len, groups)) < 3 or hours - max(t for t, _ in groups[-1]) > 2.:
        return None
    ratio = max(median(v for _, v in group) for group in groups) / max(reference, 1e-9)
    if ratio >= (.55 if paid or early else .70):
        return None
    bayes_p = planner._bayes_support(hours)
    if bayes_p is None or bayes_p < 0.35:
        return None  # evidence gate: rule triggers alone no longer suffice
    since_false = hours - getattr(planner, "_last_false_hours", float("-inf"))
    if since_false < 7 * 24 and ratio >= .8 * getattr(planner, "_last_false_ratio", 1.):
        return None
    if paid:
        planner._paid_diagnostic_attempts = getattr(planner, "_paid_diagnostic_attempts", 0) + 1
    planner.reports += 1
    planner.last_report_hours = hours
    planner._await_report_result = True
    planner._pending_report_ratio = ratio
    planner.suspicion_hours = []
    planner.log(f"planner: {'bounded paid' if paid else 'free'} diagnostic report at {payload.get('now_utc')} ratio={ratio:.3f} allowance_left={state.false_report_free_allowance-used}")
    return {"action": "report", "reason": "Further persistent throughput loss; one bounded paid diagnostic" if paid else "Sustained throughput loss; diagnostic report within remaining free allowance",
            "decision_source": "rule"}
