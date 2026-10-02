"""Small, public-information exposure optimiser.

The objective is the *increment* in the best-score ledger, not exposure score
and not squared completion. Required and request rewards are threshold events.
No hidden weather, catalogue files or card identifiers are accessed here.
"""
from __future__ import annotations

import math


def completion(item: dict, duration: float) -> float:
    """Integrate a quadratic public geometry model with a learned sky scale."""
    a, b, c = item["quality_coefficients"]
    quality = max(0.0, a + b * duration / 2.0 + c * duration * duration / 3.0)
    return min(1.0, max(0.0, item["factor_scale"] * duration * quality))


def duration_to_factor(item: dict, threshold: float, low: int, high: int):
    """First integral second attaining a threshold, under our predictive model."""
    if high < low or completion(item, high) + 1e-12 < threshold:
        return None
    if completion(item, low) >= threshold:
        return low
    left, right = low, high
    while left < right:
        mid = (left + right) // 2
        if completion(item, mid) >= threshold:
            right = mid
        else:
            left = mid + 1
    return left


def request_gain(item: dict, factor: float, duration: int) -> float:
    """Reward shares for unfinished request targets in wholly valid windows."""
    return sum(value for threshold, deadline_seconds, value, _request_id in item.get("requests", ())
               if duration <= deadline_seconds and factor >= threshold)


def marginal_gain(item: dict, duration: int, program: str, scoring) -> float:
    if duration > item["max_duration"]:
        return 0.0
    factor = completion(item, duration)
    a, b, c = item["quality_coefficients"]
    model = max(0.0, a + b * duration / 2.0 + c * duration * duration / 3.0)
    band = scoring.program_band(model * item["band_scale"])
    score = item["weight"] * factor * scoring.program_multiplier(program, band)
    gain = max(0.0, score - item["best_score"])
    if item["required_missing"] and factor >= scoring.required_threshold:
        gain += scoring.required_penalty * item["urgency"]
    gain += request_gain(item, factor, duration)
    if item.get("uniformity_gain", 0.0) and factor >= scoring.uniformity_threshold:
        gain += item["uniformity_gain"]
    return gain * item.get("confidence", 1.0)


def candidate_durations(cells: dict, scoring, low: int, high: int) -> list[int]:
    """Include exact threshold/saturation boundaries and a coarse safety grid."""
    times = {high}
    times.update(d for d in (300, 600, 900, 1200, 1800, 2400, 3000) if low <= d <= high)
    if high < 300:
        times.add(low)
    for options in cells.values():
        for item in options:
            maximum = min(high, int(item["max_duration"]))
            if maximum < low:
                continue
            times.add(maximum)
            thresholds = [1.0]
            if item["required_missing"]:
                thresholds.append(scoring.required_threshold)
            if item.get("uniformity_gain", 0.0):
                thresholds.append(scoring.uniformity_threshold)
            for threshold, deadline_seconds, _value, _request_id in item.get("requests", ()):
                request_max = min(maximum, int(deadline_seconds))
                point = duration_to_factor(item, threshold, low, request_max)
                if point is not None:
                    times.add(point)
            for threshold in thresholds:
                point = duration_to_factor(item, threshold, low, maximum)
                if point is not None:
                    times.add(point)
    return sorted(d for d in times if low <= d <= high)


def optimise_field(cells: dict, scoring, low: int, high: int, force_program=None):
    """Jointly select exposure duration, program and at most one target per cell.

    A small scheduling reserve in the denominator avoids splitting an otherwise
    equal-yield exposure into repeated tiny shots; this is a planning heuristic,
    not a claimed simulator overhead.
    """
    best = None
    programs = (force_program,) if force_program else ("DARK", "BRIGHT", "BACKUP")
    for duration in candidate_durations(cells, scoring, low, high):
        # A target's completion, required reward and request reward are shared
        # by all three program declarations. Compute them only once.
        evaluated = {}
        for fiber, options in cells.items():
            rows = []
            for item in options:
                if duration > item["max_duration"]:
                    continue
                a, b, c = item["quality_coefficients"]
                model = max(0.0, a + b * duration / 2.0 + c * duration * duration / 3.0)
                factor = min(1.0, max(0.0, item["factor_scale"] * duration * model))
                band = scoring.program_band(model * item["band_scale"])
                reward = request_gain(item, factor, duration)
                if item["required_missing"] and factor >= scoring.required_threshold:
                    reward += scoring.required_penalty * item["urgency"]
                if item.get("uniformity_gain", 0.0) and factor >= scoring.uniformity_threshold:
                    reward += item["uniformity_gain"]
                science = item["weight"] * factor
                gains = {
                    program: (max(0.0, science * scoring.program_multiplier(program, band) - item["best_score"])
                              + reward) * item.get("confidence", 1.0)
                    for program in programs
                }
                rows.append((item, factor, gains))
            evaluated[fiber] = rows
        for program in programs:
            chosen = {}
            gain = 0.0
            request_contributions = {}
            request_caps = {}
            for fiber, options in evaluated.items():
                selected = None
                selected_gain = 0.0
                selected_factor = 0.0
                for item, factor, gains in options:
                    value = gains[program]
                    if value > selected_gain:
                        selected, selected_gain = item, value
                        selected_factor = factor
                if selected is not None:
                    chosen[fiber] = selected
                    gain += selected_gain
                    for threshold, deadline, value, request_id in selected.get("requests", ()):
                        if duration <= deadline and selected_factor >= threshold:
                            contribution = value * selected.get("confidence", 1.0)
                            request_contributions[request_id] = request_contributions.get(request_id, 0.0) + contribution
                            request_caps[request_id] = selected["request_caps"][request_id]
            # Do not count more than the remaining reward when several chosen
            # fibres serve the same request and fewer completions are needed.
            for request_id, value in request_contributions.items():
                gain -= max(0.0, value - request_caps[request_id])
            if not chosen:
                continue
            rate = gain / (duration + 40.0)
            candidate = (rate, duration, program, chosen)
            if best is None or (rate, duration) > (best[0], best[1]):
                best = candidate
    return best
