"""Small geometric refinements of a coarse field; uses only current target data."""
import math

from .geometry import altaz_to_radec, shift_altaz, tangent_offsets
from .optimizer import optimise_field


def refine(planner, candidates, best, information, visible, lst, seconds_left, fractions=None):
    state, grid = planner.state, planner.grid
    if state.fast_level >= 2:
        return best
    if fractions is None:
        fractions = (0.25, 0.125, 0.0625) if state.fast_level == 0 else (0.25, 0.125)
    for fraction in fractions:
        original_alt, original_az = best[4:]
        ra, dec = altaz_to_radec(original_alt, original_az, lst, state.lat)
        radius = grid.fov / math.sqrt(2.0) + 0.5 * grid.pitch
        neighbours = [information(i) for i in state.neighbours(ra, dec, radius) if i in visible]
        neighbours = [item for item in neighbours if item is not None]
        step = fraction * grid.pitch
        shifts = [(step, 0), (-step, 0), (0, step), (0, -step)]
        if state.fast_level == 0:
            shifts += [(step, step), (step, -step), (-step, step), (-step, -step)]
        for north, east in shifts:
            alt, az = shift_altaz(original_alt, original_az, north, east)
            alt, az = round(alt, 4), round(az, 4) % 360.0
            cells = {}
            for original in neighbours:
                offsets = tangent_offsets(original["alt"], original["az"], alt, az)
                if offsets is None:
                    continue
                fiber, margin = grid.classify(*offsets)
                if fiber is None:
                    continue
                item = original.copy()
                edge = min(0.12, 0.055 + 0.025 * state.misses[item["i"]])
                stability = 1.0 if margin >= edge else 0.65 + 0.35 * max(0.0, margin / edge)
                item["confidence"] *= stability
                item["priority"] *= stability
                cells.setdefault(fiber, []).append(item)
            for options in cells.values():
                options.sort(key=lambda item: item["priority"], reverse=True)
                del options[3:]
            result = optimise_field(cells, state.scoring, state.min_exposure, seconds_left, state.force_program)
            if result is None:
                continue
            rate, duration, program, chosen = result
            candidate = (rate, duration, program, chosen, alt, az)
            candidates.append(candidate)
            if rate > best[0]:
                best = candidate
    return best


def refine_multistart(planner, candidates, best, information, visible, lst, seconds_left):
    """Preserve the usual result, then test two spatially distinct coarse seeds."""
    seeds = [best]
    if planner.state.fast_level == 0:
        separation = .5 * planner.grid.fov
        for candidate in sorted(candidates, key=lambda row: row[0], reverse=True):
            distinct = True
            for seed in seeds:
                offsets = tangent_offsets(candidate[4], candidate[5], seed[4], seed[5])
                if offsets is not None and sum(x*x for x in offsets) < separation*separation:
                    distinct = False
                    break
            if distinct:
                seeds.append(candidate)
            if len(seeds) == 3:
                break
    best = refine(planner, candidates, best, information, visible, lst, seconds_left)
    for seed in seeds[1:]:
        alternative = refine(planner, candidates, seed, information, visible, lst,
                             seconds_left, fractions=(.25, .125, .0625))
        if alternative[0] > best[0]:
            best = alternative
            log = getattr(planner, 'log', None)
            if log:
                log('search: alternate refinement neighborhood selected')
    return best
