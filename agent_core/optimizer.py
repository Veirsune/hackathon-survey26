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


def band_boundaries(item, scoring):
    """Integral seconds on either side of a quadratic average-quality crossing."""
    memo = item.get("_band_boundary_times")
    if memo is not None:
        return memo
    a, b, c = item["quality_coefficients"]
    scale = item["band_scale"]
    quadratic, linear = scale * c / 3., scale * b / 2.
    times = set()
    for threshold in scoring.program_bands.values():
        constant = scale * a - threshold
        if abs(quadratic) < 1e-15:
            roots = [-constant / linear] if abs(linear) >= 1e-15 else []
        else:
            discriminant = linear * linear - 4. * quadratic * constant
            if discriminant < 0:
                roots = []
            else:
                # Stable quadratic formula, including a repeated zero root.
                q = -.5 * (linear + math.copysign(math.sqrt(discriminant), linear))
                roots = [q / quadratic, constant / q] if q else [-linear / (2. * quadratic)]
        for value in roots:
            if math.isfinite(value) and 0 <= value <= item["max_duration"] + 1:
                floor, ceil = math.floor(value), math.ceil(value)
                times.update((floor - 1, floor, ceil, ceil + 1))
    item["_band_boundary_times"] = tuple(sorted(times))
    return item["_band_boundary_times"]


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
            times.update(t for t in band_boundaries(item, scoring) if low <= t <= maximum)
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
    """Same joint objective with target constants cached outside duration loops."""
    programs = (force_program,) if force_program else ("DARK", "BRIGHT", "BACKUP")
    multipliers = [scoring.program_multipliers.get(p, 1.0) for p in programs]
    mismatch = scoring.mismatch_multiplier
    dark, bright = scoring.program_bands["DARK"], scoring.program_bands["BRIGHT"]
    required_threshold = scoring.required_threshold
    uniformity_threshold = scoring.uniformity_threshold
    positions = range(len(programs))
    cached = []
    for fiber, options in cells.items():
        rows = []
        for item in options:
            rows.append((item, *item["quality_coefficients"], item["max_duration"],
                         item["factor_scale"], item["band_scale"], item["weight"],
                         item["best_score"], item.get("confidence", 1.0),
                         scoring.required_penalty * item["urgency"] if item["required_missing"] else 0.0,
                         item.get("uniformity_gain", 0.0), item.get("requests", ())))
        cached.append((fiber, rows))
    best = None
    for duration in candidate_durations(cells, scoring, low, high):
        totals = [0.0] * len(programs)
        chosen = [{} for _ in programs]
        contributions = [{} for _ in programs]
        caps = [{} for _ in programs]
        for fiber, options in cached:
            local_gains = [0.0] * len(programs)
            local_items = [None] * len(programs)
            local_factors = [0.0] * len(programs)
            for item, a, b, c, maximum, scale, band_scale, weight, previous, confidence, required, uniformity, requests in options:
                if duration > maximum:
                    continue
                # Search creates one cache per target per decision. Geometry
                # copies share it; pointing confidence is applied below and
                # deliberately excluded from the cached values.
                memo = item.get("_exposure_cache")
                values = memo.get(duration) if memo is not None else None
                if values is None:
                    model = max(0.0, a + b * duration / 2.0 + c * duration * duration / 3.0)
                    factor = min(1.0, max(0.0, scale * duration * model))
                    band_quality = model * band_scale
                    band = "DARK" if band_quality >= dark else "BRIGHT" if band_quality >= bright else "BACKUP"
                    reward = sum(share for threshold, deadline, share, _ in requests
                                 if duration <= deadline and factor >= threshold)
                    if required and factor >= required_threshold:
                        reward += required
                    if uniformity and factor >= uniformity_threshold:
                        reward += uniformity
                    science = weight * factor
                    match_gain = max(0.0, science * scoring.program_multipliers.get(band, 1.0) - previous) + reward
                    other_gain = max(0.0, science * mismatch - previous) + reward
                    if memo is not None:
                        memo[duration] = (factor, band, match_gain, other_gain)
                else:
                    factor, band, match_gain, other_gain = values
                for k in positions:
                    gain = (match_gain if programs[k] == band else other_gain) * confidence
                    if gain > local_gains[k]:
                        local_gains[k], local_items[k], local_factors[k] = gain, item, factor
            for k in positions:
                selected = local_items[k]
                if selected is None:
                    continue
                chosen[k][fiber] = selected
                totals[k] += local_gains[k]
                for threshold, deadline, share, request_id in selected.get("requests", ()):
                    if duration <= deadline and local_factors[k] >= threshold:
                        value = share * selected.get("confidence", 1.0)
                        contributions[k][request_id] = contributions[k].get(request_id, 0.0) + value
                        caps[k][request_id] = selected["request_caps"][request_id]
        for k in positions:
            if not chosen[k]:
                continue
            gain = totals[k]
            for request_id, value in contributions[k].items():
                gain -= max(0.0, value - caps[k][request_id])
            rate = gain / (duration + 40.0)
            candidate = (rate, duration, programs[k], chosen[k])
            if best is None or (rate, duration) > (best[0], best[1]):
                best = candidate
    return best


