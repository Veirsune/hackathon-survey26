"""Joint pointing/assignment/exposure search using public observations only."""
from __future__ import annotations

import heapq
import math
from datetime import timedelta

from .geometry import (Moon, SIDEREAL_DEG_PER_SECOND, local_sidereal_deg,
                       lunar_factor, parse_utc, radec_to_altaz, shift_altaz,
                       tangent_offsets, wrap180)
from .optimizer import completion, duration_to_factor, marginal_gain, optimise_field
from .state import PendingPrediction
from .report_budget import all_sky_weather
from .pointing_refinement import refine_multistart as refine
from .latent_declaration import choose_program
from .catalogue_tile import scan_due, append_tile


class SearchPlanner:
    def _science_preference(self, flux, quality):
        # Static control: apply the public-quality opportunity rule every night.
        scoring = self.state.scoring
        poorer_quality = scoring.program_bands["BRIGHT"] * .95
        if quality <= poorer_quality or poorer_quality <= 0:
            return 1.0
        poorer_completion = min(1., max(0., flux * self.state.max_exposure * poorer_quality / scoring.f0t0))
        return 1. + 2. * (1. - poorer_quality / quality) * (1. - poorer_completion)

    def _request_values(self, now):
        """Use request-window progress, never season-long target completion."""
        state = self.state
        requests = {}
        caps = {}
        for request in self.active_requests:
            remaining = int(request.get("remaining_count", 0))
            if remaining <= 0:
                continue
            available = parse_utc(request["issued_at_utc"])
            deadline = (parse_utc(request["deadline_utc"]) - now).total_seconds()
            if now < available or deadline < state.min_exposure:
                continue
            request_id = str(request["request_id"])
            reward = max(0.0, float(request["completion_reward"]))
            caps[request_id] = reward
            completed = set(request.get("completed_target_ids", ()))
            threshold = float(request["completion_factor_threshold"])
            value = reward / remaining
            for target_id in request.get("target_ids", ()):
                if target_id in completed or target_id not in state.index_of:
                    continue
                i = state.index_of[target_id]
                requests.setdefault(i, []).append((threshold, deadline, value, request_id))
        return requests, caps

    def _uniformity_values(self):
        """Exact one-target change to the public Jain-index penalty."""
        state = self.state
        scoring = state.scoring
        totals = {}
        done = {}
        for i, ra in enumerate(state.ra):
            band = int(ra // scoring.uniformity_band_width_deg)
            totals[band] = totals.get(band, 0) + 1
            if state.factor[i] >= scoring.uniformity_threshold:
                done[band] = done.get(band, 0) + 1
        ratios = {band: done.get(band, 0) / count for band, count in totals.items()}
        count = max(1, len(ratios))
        total = sum(ratios.values())
        squares = sum(value * value for value in ratios.values())
        before = total * total / (count * squares) if squares > 0 else 0.0
        values = {}
        for band, ratio in ratios.items():
            delta = 1.0 / totals[band]
            after = (total + delta) ** 2 / (count * (squares + 2 * ratio * delta + delta * delta))
            # The first handful of completions can make the finite-difference
            # enormous; required/science targets will establish coverage anyway.
            values[band] = min(0.5, max(0.0, scoring.uniformity_weight * (after - before)))
        return values

    def plan(self, now, night_end, night_index: int, hours: float):
        state = self.state
        scoring = state.scoring
        catalogue_scan = scan_due(self)
        state.update_scale(hours)
        seconds_left = int(min(state.max_exposure, (min(night_end, state.survey_end) - now).total_seconds()))
        if seconds_left < state.min_exposure:
            return None
        lst = local_sidereal_deg(now, state.lon)
        requests, request_caps = self._request_values(now)
        uniformity = self._uniformity_values()
        top_multiplier = max(scoring.program_multipliers.values())
        visible = set()
        preliminary = []
        for i in range(len(state.ids)):
            best_score = state.best_score[i]
            missing = state.required[i] and state.factor[i] < scoring.required_threshold
            science = max(0.0, state.weight[i] * top_multiplier - best_score)
            science *= self._science_preference(state.flux[i], state.scale)
            request_value = sum(row[2] for row in requests.get(i, ()))
            value = science + (scoring.required_penalty if missing else 0.0) + request_value
            if value <= 0.01:
                continue
            ha = wrap180(lst - state.ra[i])
            hmax = state.hmax[i]
            if not (-hmax <= ha <= hmax):
                continue
            up = (hmax - ha) / SIDEREAL_DEG_PER_SECOND if hmax < 180 else 1e9
            if up < state.min_exposure:
                continue
            visible.add(i)
            nights_left = max(1, state.last_night[i] - night_index + 1)
            urgency = (1.0 + (2.0 / nights_left if missing else 0.0)) * getattr(self, "required_priority", 1.0)
            # Public flux is a cheap initial estimate of completion speed.
            preliminary.append((value * math.sqrt(max(0.001, state.flux[i])) * urgency, i))
        if not preliminary:
            return None
        pool_count = 400 if state.fast_level == 0 else 160
        pool = heapq.nlargest(pool_count, preliminary)
        altaz_cache = {}
        info_cache = {}
        moon_cache = {}

        def altaz(i):
            if i not in altaz_cache:
                altaz_cache[i] = radec_to_altaz(state.ra[i], state.dec[i], lst, state.lat)
            return altaz_cache[i]

        def information(i):
            if i in info_cache:
                return info_cache[i]
            alt, az = altaz(i)
            direction = self._direction_factor(alt, az)
            if direction <= 0.0:
                info_cache[i] = None
                return None
            ha = wrap180(lst - state.ra[i])
            up = (state.hmax[i] - ha) / SIDEREAL_DEG_PER_SECOND if state.hmax[i] < 180 else 1e9
            maximum = min(seconds_left, int(up))
            if maximum < state.min_exposure:
                info_cache[i] = None
                return None
            models = []
            for fraction in (0.0, 0.5, 1.0):
                elapsed = maximum * fraction
                moment = now + timedelta(seconds=elapsed)
                sidereal = lst + elapsed * SIDEREAL_DEG_PER_SECOND
                a, z = radec_to_altaz(state.ra[i], state.dec[i], sidereal, state.lat)
                if elapsed not in moon_cache:
                    moon_cache[elapsed] = Moon(moment, sidereal, state.lat)
                moon = moon_cache[elapsed]
                lunar = lunar_factor(moon, state.ra[i], state.dec[i], scoring.lunar_model)
                models.append(scoring.quality_model(a, lunar))
            # q(t) through the beginning/middle/end geometry samples.
            q0, qm, qe = models
            c = 2.0 * (qe - 2.0 * qm + q0) / (maximum * maximum)
            b = (qe - q0 - c * maximum * maximum) / maximum
            missing = state.required[i] and state.factor[i] < scoring.required_threshold
            nights_left = max(1, state.last_night[i] - night_index + 1)
            urgency = (1.0 + (2.0 / nights_left if missing else 0.0)) * getattr(self, "required_priority", 1.0)
            # Soft deadlines increase priority only moderately: the actual
            # 50-point penalty is already much larger than any science target.
            if missing and ha > 0 and up < 3600:
                urgency *= 1.10
            item = {
                "i": i, "alt": alt, "az": az, "quality_coefficients": (q0, b, c),
                "max_duration": maximum,
                "factor_scale": (state.flux[i] * state.scale * (0.90 if missing or requests.get(i) else 1.0) * direction / scoring.f0t0
                                 / getattr(self, "exposure_margin", 1.0)),
                "band_scale": state.scale / 0.95,
                "weight": state.weight[i], "best_score": state.best_score[i],
                "required_missing": missing, "urgency": urgency,
                "requests": requests.get(i, ()), "request_caps": request_caps,
                "uniformity_gain": uniformity.get(int(state.ra[i] // scoring.uniformity_band_width_deg), 0.0)
                    if state.factor[i] < scoring.uniformity_threshold else 0.0,
                "confidence": 1.0,
                "_exposure_cache": {},  # per target, recreated each decision
            }
            science_preference = self._science_preference(state.flux[i],
                max(0., (q0 + 4 * qm + qe) / 6. * state.scale))
            item["weight"] *= science_preference
            item["best_score"] *= science_preference
            a_rad, z_rad = math.radians(alt), math.radians(az)
            item["vector"] = (math.cos(a_rad) * math.cos(z_rad),
                              math.cos(a_rad) * math.sin(z_rad), math.sin(a_rad))
            # Missing fibres indicate geometric uncertainty; never permanently
            # erase a required target simply because it has previously missed.
            confidence = max(0.45, 0.85 ** state.misses[i])
            item["confidence"] = confidence
            durations = {maximum}
            for threshold in (1.0, scoring.required_threshold if missing else 1.0):
                point = duration_to_factor(item, threshold, state.min_exposure, maximum)
                if point is not None:
                    durations.add(point)
            for threshold, deadline, _value, _rid in item["requests"]:
                point = duration_to_factor(item, threshold, state.min_exposure, min(maximum, int(deadline)))
                if point is not None:
                    durations.add(point)
            priority = max((marginal_gain(item, duration, program, scoring) / (duration + 40.0)
                            for duration in durations for program in ("DARK", "BRIGHT", "BACKUP")), default=0.0)
            item["priority"] = priority
            info_cache[i] = item if priority > 1e-8 else None
            return info_cache[i]

        anchors = []
        for _, i in pool:
            item = information(i)
            if item is not None:
                anchors.append((item["priority"], i))
        anchors.sort(reverse=True)
        if not anchors:
            return None

        n_anchors = 8 if state.fast_level == 0 else 3 if state.fast_level == 1 else 1
        fibers = range(self.grid.n) if state.fast_level < 2 else range(self.grid.n // 2 - 2, self.grid.n // 2 + 2)
        placements = []
        placement_signatures = set()
        selected_anchors = []
        # Cover several different fields rather than spending every candidate
        # on required targets in the same small cluster.
        for _value, i in anchors:
            if any(abs(wrap180(state.ra[i] - state.ra[j])) * math.cos(math.radians(state.dec[i])) < 0.8
                   and abs(state.dec[i] - state.dec[j]) < 0.8 for j in selected_anchors):
                continue
            selected_anchors.append(i)
            if len(selected_anchors) >= n_anchors:
                break
        radius = (self.grid.fov + (self.grid.side - 1) * self.grid.pitch) / math.sqrt(2.0) + 0.1
        for anchor in selected_anchors:
            aa, az = altaz(anchor)
            near = [information(i) for i in state.neighbours(state.ra[anchor], state.dec[anchor], radius) if i in visible]
            near = [item for item in near if item is not None]
            for anchor_fiber in fibers:
                north, east = self.grid.fiber_center(anchor_fiber)
                ca, cz = shift_altaz(aa, az, -north, -east)
                if not (0.0 <= ca <= 90.0):
                    continue
                ca, cz = round(ca, 4), round(cz, 4) % 360.0
                a, z = math.radians(ca), math.radians(cz)
                sa, ca_cos, sz, cz_cos = math.sin(a), math.cos(a), math.sin(z), math.cos(z)
                center = (ca_cos * cz_cos, ca_cos * sz, sa)
                north_axis = (-sa * cz_cos, -sa * sz, ca_cos)
                east_axis = (-sz, cz_cos, 0.0)
                cells = {}
                for original in near:
                    x, y, z = original["vector"]
                    depth = x * center[0] + y * center[1] + z * center[2]
                    if depth <= 0.0:
                        continue
                    dn = math.degrees((x * north_axis[0] + y * north_axis[1] + z * north_axis[2]) / depth)
                    de = math.degrees((x * east_axis[0] + y * east_axis[1]) / depth)
                    fiber, margin = self.grid.classify(dn, de)
                    if fiber is None:
                        continue
                    item = original.copy()
                    edge = min(0.12, 0.055 + 0.025 * state.misses[item["i"]])
                    stability = 1.0 if margin >= edge else 0.65 + 0.35 * max(0.0, margin / edge)
                    item["confidence"] *= stability
                    item["priority"] *= stability
                    cells.setdefault(fiber, []).append(item)
                if not cells:
                    continue
                for options in cells.values():
                    options.sort(key=lambda item: item["priority"], reverse=True)
                    del options[3:]
                signature = tuple((fiber, tuple(item["i"] for item in options)) for fiber, options in sorted(cells.items()))
                if signature in placement_signatures:
                    continue
                placement_signatures.add(signature)
                heuristic = sum(options[0]["priority"] for options in cells.values())
                placements.append((heuristic, ca, cz, cells))
        placements.sort(key=lambda row: row[0], reverse=True)
        shortlist = 12 if state.fast_level == 0 else 5 if state.fast_level == 1 else 2
        best = None
        candidates = []
        for _heuristic, ca, cz, cells in placements[:shortlist]:
            result = optimise_field(cells, scoring, state.min_exposure, seconds_left, state.force_program)
            if result is not None:
                rate, duration, program, chosen = result
                candidate = (rate, duration, program, chosen, ca, cz)
                candidates.append(candidate)
                if best is None or rate > best[0]:
                    best = candidate
        if best is None:
            return None
        best = refine(self, candidates, best, information, visible, lst, seconds_left)
        if catalogue_scan:
            best = append_tile(self, candidates, best, information, visible, lst, seconds_left)
        # An optional adviser may select one of the already optimised actions.
        # Keep the original strict-greater tie rule and build predictions only
        # after selection, so the no-adviser path is exactly deterministic.
        selector = getattr(self, "_select_candidate", None)
        if callable(selector):
            approved = tuple(candidates)
            try:
                selected = selector(candidates, best, now, night_end, night_index)
            except Exception as exc:
                selected = best
                log = getattr(self, "log", None)
                if callable(log):
                    log(f"candidate adviser failed ({type(exc).__name__}); retaining deterministic choice")
            if any(selected is candidate for candidate in approved):
                best = selected
        _rate, duration, program, chosen, ca, cz = best
        program = choose_program(state, chosen, duration, program, hours)
        state.pending.clear()
        state._latent_direction_clear = {state.ids[item["i"]] for item in chosen.values()
            if self._direction_factor(item["alt"], item["az"]) >= 1.0}
        state._pending_sky_weather = all_sky_weather(state.notices)
        clean = not state.all_sky_notice()
        for item in chosen.values():
            a, b, c = item["quality_coefficients"]
            model = max(0.0, a + b * duration / 2.0 + c * duration * duration / 3.0)
            state.pending[state.ids[item["i"]]] = PendingPrediction(
                model=model, band_model=model / 0.95, alt=item["alt"], az=item["az"],
                clean=clean and self._direction_factor(item["alt"], item["az"]) >= 1.0,
            )
        state.pending_program = program
        state.pending_duration = duration
        state.pending_night = night_index
        return {"action": "observe", "pointing": {"alt_deg": ca, "az_deg": cz},
                "assignments": {str(fiber): state.ids[item["i"]] for fiber, item in chosen.items()},
                "duration_seconds": duration, "program": program}
