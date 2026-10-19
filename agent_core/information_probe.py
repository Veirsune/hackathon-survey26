"""Collect enough independent public measurements for the existing diagnosis gate.

The temporary search ledger rewards measuring catalogue targets; it is never
copied into the actual completion ledger. Only a real exposure updates beliefs.
"""
from copy import copy, deepcopy
from time import process_time

from .bonus_certificate import sky_warning

CPU_ALLOWANCE = 18.0
MAX_EXPOSURE = 300


def propose(planner, now, night_end, night_index, hours):
    state = planner.state
    spent = getattr(planner, '_information_probe_cpu', 0.)
    attempts = getattr(planner, '_diagnostic_probe_attempts', {})
    after = planner.last_report_hours
    samples = [r for r in getattr(state, '_weather_clear_diagnostic_exposures', ())
               if r[1] == night_index and r[0] > after]
    if (len(samples) >= 3
            or attempts.get(night_index, 0) >= 3
            or any(r.get('remaining_count', 1) > 0 for r in planner.active_requests)
            or hours - getattr(planner, '_diagnostic_probe_last_attempt', float('-inf')) < 2.
            or spent >= CPU_ALLOWANCE
            or planner._cpu_left() < 10.
            or state.scale >= .55
            or state.has_recent_sample(hours)
            or sky_warning(state.notices)
            or (night_end - now).total_seconds() < MAX_EXPOSURE):
        return None
    planner._diagnostic_probe_attempts = {night_index: attempts.get(night_index, 0) + 1}
    planner._diagnostic_probe_last_attempt = hours
    started = process_time()
    probe = copy(planner)
    probe.state = deepcopy(state)
    probe.grid = probe.state.fiber_grid
    probe.active_requests = []
    probe.science_scarcity_enabled = False
    probe.exposure_margin = 1.
    probe._select_candidate = lambda candidates, best, *args: best
    probe.log = lambda *_: None
    s = probe.state
    # Initial nominal throughput is an exploration assumption, not new evidence.
    s.scale = 1.; s.band_scale = 1. / .95
    s._latent_band = None
    s.update_scale = lambda *_: None
    s.best_score = [0.] * len(s.ids)
    s.required = [False] * len(s.ids)
    s.factor = [1.] * len(s.ids)
    s.max_exposure = min(state.max_exposure, MAX_EXPOSURE)
    s.fast_level = 2
    if hasattr(s, '_compute_arrays'):
        del s._compute_arrays
    try:
        action = probe.plan(now, night_end, night_index, hours)
    finally:
        elapsed = max(0., process_time() - started) / planner._decision_speed
        planner._information_probe_cpu = spent + elapsed
    if action is None or len(action.get('assignments', ())) < 4:
        return None
    # Copy only predictions for the action actually about to be executed.
    # Scores, completion factors, quality history and inferred scale stay real.
    for name in ('pending', 'pending_program', 'pending_duration', 'pending_night',
                 '_latent_direction_clear', '_pending_sky_weather',
                 '_certificate_pending_notices'):
        setattr(state, name, getattr(s, name))
    planner.log('information_probe: night={} duration={} targets={} scale={:.6f} cpu={:.6f} total_cpu={:.6f}'.format(
        night_index, action['duration_seconds'], len(action['assignments']), state.scale,
        elapsed, planner._information_probe_cpu))
    return action
