"""Spend public free-report allowance on sustained, unexplained throughput loss."""
from statistics import median

from .geometry import parse_utc


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
            state.forget_quality_history()
        else:
            planner._false_since_correct = getattr(planner, "_false_since_correct", 0) + 1
            planner._last_false_hours = hours
            planner._last_false_ratio = getattr(planner, "_pending_report_ratio", 1.)
        planner._await_report_result = False
    if getattr(planner, "_await_report_result", False):
        return None
    used = getattr(planner, "_false_since_correct", 0)
    if used >= state.false_report_free_allowance:
        return None
    # Preserve the established strong-evidence path while it is still free.
    original = planner._baseline_report(hours, payload)
    if original is not None:
        planner._await_report_result = True
        planner._pending_report_ratio = .6
        return original
    if hours - planner.last_report_hours < 48.:
        return None
    quake = getattr(state, "_earthquake_seen_hours", float("-inf"))
    if hours - quake < 7 * 24:
        return None
    older = [ratio for when, _, ratio in state.clean_history if when < hours - 72.]
    if len(older) < 32:
        return None
    reference = median(older)
    rows = [r for r in getattr(state, "_diagnostic_exposures", ())
            if hours - r[0] <= 48. and r[0] - quake >= 7 * 24]
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
    if ratio >= .70:
        return None
    since_false = hours - getattr(planner, "_last_false_hours", float("-inf"))
    if since_false < 7 * 24 and ratio >= .8 * getattr(planner, "_last_false_ratio", 1.):
        return None
    planner.reports += 1
    planner.last_report_hours = hours
    planner._await_report_result = True
    planner._pending_report_ratio = ratio
    planner.suspicion_hours = []
    planner.log(f"planner: free diagnostic report at {payload.get('now_utc')} ratio={ratio:.3f} allowance_left={state.false_report_free_allowance-used}")
    return {"action": "report", "reason": "Sustained throughput loss; diagnostic report within remaining free allowance",
            "decision_source": "rule"}
