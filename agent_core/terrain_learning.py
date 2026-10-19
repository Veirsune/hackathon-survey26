"""Bounded exploration of an uncertain permanent terrain horizon.

Only delivered hit scores and public target geometry update this memory. An
azimuth bin is not a precise terrain boundary; two independent exposures and
an altitude guard reduce, but cannot eliminate, errors near angular edges.
"""
import math
from collections import defaultdict
from datetime import timedelta
from time import process_time

from .geometry import (Moon, SIDEREAL_DEG_PER_SECOND, local_sidereal_deg,
                       lunar_factor, radec_to_altaz, shift_altaz,
                       tangent_offsets, wrap180)
from .state import PendingPrediction

CENTRES = dict(N=0., NE=45., E=90., SE=135., S=180., SW=225., W=270., NW=315.)
BIN_WIDTH = 2.
GUARD = 1.
MAX_PROBES = 24
CPU_LIMIT = 12.


def sector(az, directions):
    return any(d in CENTRES and abs(wrap180(az-CENTRES[d])) <= 60. for d in directions)


def key(az):
    return int((az % 360.) // BIN_WIDTH)


class Horizon:
    def __init__(self):
        self.prior_limit = None
        self.clear = defaultdict(list)
        self.blocked = defaultdict(list)
        self.pending = None
        self.serial = 0
        self.probes = 0
        self.probe_bins = defaultdict(int)
        self.probe_nights = defaultdict(int)
        self.last_attempt = -math.inf
        self.cpu = 0.

    def floor(self, az):
        # Require two separate turns supporting at least this blocked height.
        rows = self.blocked.get(key(az), ())
        return sorted(a for _, a in rows)[-2] if len(rows) >= 2 else -math.inf

    def factor(self, alt, az, directions):
        if not sector(az, directions):
            return 1.
        floor = self.floor(az)
        if alt < floor:
            return 0.
        rows = [(n, a) for n, a in self.clear.get(key(az), ()) if a <= alt and a >= floor]
        if len(rows) >= 2:
            return 1.
        # Grounded language gives a prior; two independent positive exposures
        # can revise it locally. Positive-control negatives take precedence.
        limit = self.prior_limit(az, directions) if self.prior_limit is not None else 50.
        return 1. if alt >= limit else 0.

    def ingest(self, samples, clean=True):
        """One exposure: (alt_min, alt_max, az, positive, az_bin_stable).

        Many fibers in a bin count once. A zero is usable only with a positive
        control in this exposure; all-zero and absent-hit cases remain unknown.
        """
        self.serial += 1
        if not clean:
            return
        positive_control = any(r[3] for r in samples)
        good, bad = {}, {}
        for lo, hi, az, positive, stable in samples:
            if not stable:
                continue
            k = key(az)
            if positive:
                good.setdefault(k, []).append(hi + GUARD)
            elif positive_control:
                bad[k] = max(bad.get(k, -math.inf), hi + GUARD)
        for k, heights in good.items():
            # Lower blocked fibers and higher clear fibers can bracket a
            # horizon. Retain the lowest consistent clear height, once per
            # exposure; conflicting negative evidence still takes precedence.
            consistent = [a for a in heights if a >= bad.get(k, -math.inf)]
            if consistent:
                self.clear[k].append((self.serial, min(consistent)))
                self.clear[k] = self.clear[k][-16:]
        for k, height in bad.items():
            self.blocked[k].append((self.serial, height))
            self.blocked[k] = self.blocked[k][-16:]

    def remember(self, planner, action, now):
        self.pending = None
        s = planner.state
        if action.get('action') != 'observe' or not s.terrain:
            return
        duration = action['duration_seconds']
        lst = local_sidereal_deg(now, s.lon)
        rows = {}
        for target in action.get('assignments', {}).values():
            i = s.index_of.get(target)
            if i is None:
                continue
            coords = [radec_to_altaz(s.ra[i], s.dec[i], lst+dt*SIDEREAL_DEG_PER_SECOND, s.lat)
                      for dt in (0., duration/2., duration)]
            if not sector(coords[1][1], s.terrain):
                continue
            rows[target] = (min(a for a, _ in coords), max(a for a, _ in coords), coords[1][1],
                            len({key(z) for _, z in coords}) == 1)
        # All current non-terrain notices block learning, including earthquakes.
        self.pending = (rows, not bool(s.notices))

    def consume(self, payload):
        pending, self.pending = self.pending, None
        result = payload.get('last_result') or {}
        if pending is None or result.get('action') != 'observe':
            return
        rows, clean = pending
        for message in payload.get('new_messages', ()):
            if message.get('record_type') == 'bulletin' and any(
                    n.get('event_kind') != 'terrain_obstruction' for n in message.get('notices', ())):
                clean = False
        hits = {h['target_id']: float(h.get('score', 0.)) for h in result.get('hits', ())}
        samples = [(lo, hi, az, hits[target] > 1e-6, stable)
                   for target, (lo, hi, az, stable) in rows.items() if target in hits]
        self.ingest(samples, clean)


def propose(planner, now, night_end, night_index, hours):
    s = planner.state
    h = planner.horizon
    duration = max(60, s.min_exposure)
    if (not s.terrain or s.notices or s.extra_avoid or duration > min(120, s.max_exposure)
            or h.probes >= MAX_PROBES or h.probe_nights[night_index] >= 2
            or hours-h.last_attempt < 1. or h.cpu >= CPU_LIMIT or planner._cpu_left() < 30.
            or (night_end-now).total_seconds() < duration
            or any(r.get('remaining_count', 0) > 0 for r in planner.active_requests)):
        return None
    h.last_attempt = hours
    started = process_time()
    try:
        return _propose(planner, now, night_index, duration)
    finally:
        h.cpu += max(0., process_time()-started)/max(1e-9, planner._decision_speed)


def _propose(planner, now, night_index, duration):
    s, h, grid = planner.state, planner.horizon, planner.grid
    lst = local_sidereal_deg(now, s.lon)
    if not hasattr(h, 'required_indices'):
        h.required_indices = [i for i, r in enumerate(s.required) if r]
    pool = []
    for i in h.required_indices:
        if s.factor[i] >= s.scoring.required_threshold:
            continue
        peak = 90.-abs(s.lat-s.dec[i])
        if not s.min_alt+.6 <= peak < 50.:
            continue
        alt, az = radec_to_altaz(s.ra[i], s.dec[i], lst, s.lat)
        end_alt, _ = radec_to_altaz(s.ra[i], s.dec[i], lst+duration*SIDEREAL_DEG_PER_SECOND, s.lat)
        k = key(az)
        if (min(alt, end_alt) < s.min_alt+.6 or peak-alt < GUARD+grid.fov/2.+.5
                or key(radec_to_altaz(s.ra[i], s.dec[i], lst+duration*SIDEREAL_DEG_PER_SECOND, s.lat)[1]) != k
                or not sector(az, s.terrain)
                or h.factor(alt, az, s.terrain) > 0 or alt < h.floor(az)
                or h.probe_bins[k] >= 2):
            continue
        # Prefer close-to-transit targets; two probes in the same bin establish
        # separate exposure evidence. Public geometry only, no card identifiers.
        value = s.flux[i] / (1.+peak-alt)
        if len(h.clear.get(k, ())) == 1:
            value *= 2.  # Complete an existing one-exposure hypothesis first.
        # Seek evidence near the uncertain boundary rather than repeatedly
        # spending probes on bright targets far below the current prior.
        if h.prior_limit is not None:
            prior = h.prior_limit(az, s.terrain)
            support = [a for _, a in h.clear.get(k, ()) if h.floor(az) <= a < prior]
            confirm = len(support) == 1
            desired_alt = support[0] - GUARD if confirm else prior - GUARD - grid.fov / 2.
            value = (confirm, -abs(alt - desired_alt), value)
        pool.append((value, i, alt, az))
    if not pool:
        return None
    _, anchor, aa, az = max(pool)
    fiber = min(grid.n-1, (grid.side//2)*grid.side + grid.side//2)
    dn, de = grid.fiber_center(fiber)
    ca, cz = shift_altaz(aa, az, -dn, -de)
    ca, cz = round(ca, 4), round(cz, 4) % 360.
    radius = (grid.fov+(grid.side-1)*grid.pitch)/math.sqrt(2.)+.1
    moon = Moon(now+timedelta(seconds=duration/2), lst+duration/2*SIDEREAL_DEG_PER_SECOND, s.lat)
    cells = {}
    for i in s.neighbours(s.ra[anchor], s.dec[anchor], radius):
        coords = [radec_to_altaz(s.ra[i], s.dec[i], lst+t*SIDEREAL_DEG_PER_SECOND, s.lat)
                  for t in (0., duration/2., duration)]
        if min(a for a, _ in coords) < s.min_alt+.6:
            continue
        offsets = tangent_offsets(*coords[0], ca, cz)
        if offsets is None:
            continue
        f, margin = grid.classify(*offsets)
        if f is None or margin < .04:
            continue
        lunar = lunar_factor(moon, s.ra[i], s.dec[i], s.scoring.lunar_model)
        model = s.scoring.quality_model(coords[1][0], lunar)
        priority = (s.scoring.required_penalty if s.required[i] and s.factor[i] < s.scoring.required_threshold else 0.) + s.flux[i]*s.weight[i]
        row = (priority, i, model, coords[0])
        if f not in cells or i == anchor or (cells[f][1] != anchor and priority > cells[f][0]):
            cells[f] = row
    if not cells or not any(row[1] == anchor for row in cells.values()):
        return None
    # An exploratory exposure does not certify atmosphere or fault state.
    program = s.force_program or 'BACKUP'
    s.pending = {s.ids[i]: PendingPrediction(model, model/.95, alt, az, False)
                 for _, i, model, (alt, az) in cells.values()}
    s.pending_program, s.pending_duration, s.pending_night = program, duration, night_index
    s._latent_direction_clear = set()
    s._pending_sky_weather = False
    s._certificate_pending_notices = tuple(s.notices)
    h.probes += 1
    h.probe_bins[key(az)] += 1
    h.probe_nights[night_index] += 1
    planner.log('terrain_probe: night={} duration={} targets={} anchor={} bin={} count={}'.format(
        night_index, duration, len(cells), s.ids[anchor], key(az), h.probes))
    return {'action': 'observe', 'pointing': {'alt_deg': ca, 'az_deg': cz},
            'assignments': {str(f): s.ids[row[1]] for f, row in cells.items()},
            'duration_seconds': duration, 'program': program}
