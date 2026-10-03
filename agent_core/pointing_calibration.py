"""Infer a mount offset from public fibre hit membership, never hidden truth."""
import math
from collections import deque
from datetime import timedelta

from .geometry import local_sidereal_deg, parse_utc, radec_to_altaz


def vector(alt, az):
    a, z = math.radians(alt), math.radians(az)
    return math.cos(a) * math.cos(z), math.cos(a) * math.sin(z), math.sin(a)


class PointingCalibration:
    def __init__(self, state, log=lambda text: None):
        self.state, self.grid, self.log = state, state.fiber_grid, log
        self.offset = (0., 0.)
        self.history = deque(maxlen=8)
        self.pending = None
        self.quake_active = False
        self.fits = 0
        self.ambiguous_fits = 0

    def notice(self, bulletin):
        if bulletin is None:
            return
        quake = any(n.get("event_kind") == "earthquake" for n in bulletin.get("notices", ()))
        if quake and not self.quake_active:
            self.history.clear()
            self.offset = (0., 0.)
            self.log("pointing: public earthquake notice; discard previous calibration")
        self.quake_active = quake

    def remember(self, action, now_utc):
        self.pending = None
        if action.get("action") != "observe" or not now_utc:
            return
        now = parse_utc(now_utc)
        duration = action["duration_seconds"]
        sidereals = [local_sidereal_deg(now + timedelta(seconds=duration * f), self.state.lon)
                     for f in (0., .5, 1.)]
        points = []
        for fiber, target_id in action["assignments"].items():
            i = self.state.index_of.get(target_id)
            if i is None:
                continue
            coords = [radec_to_altaz(self.state.ra[i], self.state.dec[i], s, self.state.lat) for s in sidereals]
            # A missed horizon-crossing target is not evidence of mispointing.
            if min(a for a, _ in coords) < self.state.min_alt + 2.:
                continue
            points.append((int(fiber), target_id, vector(*coords[0])))
        if points:
            p = action["pointing"]
            self.pending = (p["alt_deg"], p["az_deg"], points)

    def consume(self, result):
        pending, self.pending = self.pending, None
        if pending is None or not result or result.get("action") != "observe":
            return
        hits = {h["target_id"] for h in result.get("hits", ())}
        alt, az, points = pending
        # Score can be zero in bad weather. Membership, not score, is evidence.
        self.history.append((alt, az, [(fiber, point, target in hits) for fiber, target, point in points]))
        if len(self.history) < 3:
            return
        count = sum(len(points) for _, _, points in self.history)
        old_error = self.errors(self.offset)
        if count < 24 or old_error < 3:
            return
        prior = self.offset
        best = prior
        best_error = old_error
        for stage, (step, radius) in enumerate(((self.grid.pitch / 8., 8), (self.grid.pitch / 32., 4), (self.grid.pitch / 128., 4))):
            center = best
            candidates = [(center[0] + x * step, center[1] + y * step)
                          for x in range(-radius, radius + 1) for y in range(-radius, radius + 1)
                          if max(abs(center[0] + x * step), abs(center[1] + y * step)) <= 2 * self.grid.pitch]
            ranked = [(self.errors(candidate), (candidate[0] - prior[0]) ** 2 + (candidate[1] - prior[1]) ** 2,
                       candidate) for candidate in candidates]
            if ranked:
                error, _, candidate = min(ranked)
                if stage == 0:
                    tied = [p for e, _, p in ranked if e == error]
                    alt_span = max(p[0] for p in tied) - min(p[0] for p in tied)
                    az_span = max(p[1] for p in tied) - min(p[1] for p in tied)
                    projection = max(math.cos(math.radians(a)) for a, _, _ in self.history)
                    # A fine search around an arbitrary tied solution would
                    # hide global ambiguity. Wait for varied edge distances.
                    if max(alt_span, az_span * projection) > self.grid.glass / 2.:
                        self.ambiguous_fits += 1
                        return
                if error <= best_error:
                    best, best_error = candidate, error
        # Require several explained misses and near-consistent recent evidence.
        if old_error - best_error >= 3 and best_error <= .02 * count:
            self.offset = best
            self.fits += 1
            self.log(f"pointing: fitted offset alt={best[0]:.4f} az={best[1]:.4f}; conflicts {old_error}->{best_error}/{count}")

    def errors(self, offset):
        errors = 0
        for alt, az, points in self.history:
            a, z = math.radians(alt + offset[0]), math.radians((az + offset[1]) % 360.)
            sa, ca, sz, cz = math.sin(a), math.cos(a), math.sin(z), math.cos(z)
            center = (ca * cz, ca * sz, sa)
            north, east = (-sa * cz, -sa * sz, ca), (-sz, cz, 0.)
            for assigned, (x, y, v), hit in points:
                depth = x * center[0] + y * center[1] + v * center[2]
                predicted = False
                if depth > 0. and 0. <= alt + offset[0] <= 90.:
                    dn = math.degrees((x * north[0] + y * north[1] + v * north[2]) / depth)
                    de = math.degrees((x * east[0] + y * east[1]) / depth)
                    fiber, _ = self.grid.classify(dn, de)
                    predicted = fiber == assigned
                errors += predicted != hit
        return errors

    def correct(self, action):
        if action.get("action") != "observe" or self.offset == (0., 0.):
            return action
        point = action["pointing"]
        alt = point["alt_deg"] - self.offset[0]
        if not 0. <= alt <= 90.:
            return action
        return dict(action, pointing={"alt_deg": round(alt, 4),
                                      "az_deg": round(point["az_deg"] - self.offset[1], 4) % 360.})
