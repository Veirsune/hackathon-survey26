"""One fibre-aware catalogue proposal at a bounded deterministic cadence."""
from collections import defaultdict
import math

from .geometry import tangent_offsets
from .optimizer import completion, marginal_gain, optimise_field
from .pointing_refinement import refine


def scan_due(planner):
    """Count only real full-search calls; shallow preview copies cannot advance it."""
    if planner.state.fast_level != 0 or getattr(planner, "_policy_preview", False):
        return False
    planner._catalogue_plan_calls = getattr(planner, "_catalogue_plan_calls", 0) + 1
    return planner._catalogue_plan_calls % 4 == 0


def coarse_gain(cells, duration, program, scoring):
    chosen, gain = {}, 0.
    for fiber, options in cells.items():
        maximum, selected = 0., None
        for item in options:
            proposed = marginal_gain(item, duration, program, scoring)
            if proposed > maximum:
                maximum, selected = proposed, item
        if selected is not None:
            chosen[fiber] = selected
            gain += maximum
    totals, caps = defaultdict(float), {}
    for item in chosen.values():
        factor = completion(item, duration)
        for threshold, deadline, value, request in item.get("requests", ()):
            if duration <= deadline and factor >= threshold:
                totals[request] += value * item.get("confidence", 1.)
                caps[request] = item["request_caps"][request]
    gain -= sum(max(0., value - caps[request]) for request, value in totals.items())
    return gain / (duration + 40.) if chosen else 0.


def tile_candidate(planner, incumbent, information, visible, lst, seconds_left):
    state, grid = planner.state, planner.grid
    if state.fast_level != 0 or getattr(planner, "_policy_preview", False):
        return None
    step = grid.fov
    rings = []
    alt = state.min_alt + step / 2.
    while alt < 90.:
        count = max(1, int(round(360. * math.cos(math.radians(alt)) / step)))
        rings.append((round(alt, 4), count))
        alt += step
    if not rings:
        return None
    tiles = defaultdict(lambda: defaultdict(list))
    for i in sorted(visible):
        item = information(i)
        if item is None:
            continue
        near_ring = int(round((item["alt"] - rings[0][0]) / step))
        for row in range(max(0, near_ring - 1), min(len(rings), near_ring + 2)):
            alt, count = rings[row]
            middle = int(round(item["az"] / 360. * count))
            for col in sorted({(middle - 1) % count, middle % count, (middle + 1) % count}):
                az = round(col * 360. / count, 4) % 360.
                offsets = tangent_offsets(item["alt"], item["az"], alt, az)
                if offsets is None:
                    continue
                fiber, margin = grid.classify(*offsets)
                if fiber is None:
                    continue
                adapted = item.copy()
                edge = min(.12, .055 + .025 * state.misses[i])
                stability = 1. if margin >= edge else .65 + .35 * max(0., margin / edge)
                adapted["confidence"] *= stability
                adapted["priority"] *= stability
                tiles[row, col][fiber].append(adapted)
    durations = sorted({max(state.min_exposure, min(seconds_left, t)) for t in (300, 900, 1800, 3600, incumbent[1])})
    programs = (state.force_program,) if state.force_program else ("DARK", "BRIGHT", "BACKUP")
    best = None
    for key, cells in tiles.items():
        for duration in durations:
            for program in programs:
                rate = coarse_gain(cells, duration, program, state.scoring)
                if rate > 0. and (best is None or rate > best[0]):
                    best = rate, key
    if best is None:
        return None
    _, key = best
    exact = optimise_field(tiles[key], state.scoring, state.min_exposure, seconds_left, state.force_program)
    if exact is None:
        return None
    alt, count = rings[key[0]]
    az = round(key[1] * 360. / count, 4) % 360.
    candidate = (*exact, alt, az)
    return refine(planner, [], candidate, information, visible, lst, seconds_left)


def append_tile(planner, candidates, best, information, visible, lst, seconds_left):
    if planner.state.fast_level != 0 or getattr(planner, "_policy_preview", False):
        return best
    proposal = tile_candidate(planner, best, information, visible, lst, seconds_left)
    if proposal is not None and proposal[0] > best[0]:
        candidates.append(proposal)
        log = getattr(planner, "log", None)
        if log:
            log("catalogue_tile: proposal selected")
        return proposal
    return best
