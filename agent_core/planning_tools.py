"""Short nominal projections, not observations or hidden-engine rollouts."""
from copy import copy, deepcopy
from datetime import timedelta

from .geometry import parse_utc
from .optimizer import completion
from .latent_band import band_scale


def project_exposure(probe, chosen, duration, program, finish):
    """Update a disposable ledger; repeats never accumulate completion."""
    state = probe.state
    start = finish - timedelta(seconds=duration)
    hours = (start - state.survey_start).total_seconds() / 3600.
    projected_band_scale = band_scale(state, hours)
    science = reward = 0.
    required = request_targets = 0
    factors = {}
    for item in chosen.values():
        i = item["i"]
        factor = completion(item, duration)
        a, b, c = item["quality_coefficients"]
        quality = max(0., a + b * duration / 2. + c * duration * duration / 3.)
        band = state.scoring.program_band(quality * projected_band_scale)
        score = state.weight[i] * factor * state.scoring.program_multiplier(program, band)
        science += max(0., score - state.best_score[i]) * item.get("confidence", 1.)
        required += int(state.required[i] and state.factor[i] < state.scoring.required_threshold <= factor)
        state.best_score[i] = max(state.best_score[i], score)
        state.factor[i] = max(state.factor[i], factor)
        factors[state.ids[i]] = factor
    for request in probe.active_requests:
        remaining = int(request.get("remaining_count", 0))
        if remaining <= 0 or start < parse_utc(request["issued_at_utc"]) or finish > parse_utc(request["deadline_utc"]):
            continue
        done = set(request.get("completed_target_ids", ()))
        threshold = float(request["completion_factor_threshold"])
        new = {target for target in request.get("target_ids", ())
               if target not in done and factors.get(target, -1.) >= threshold}
        request_targets += min(remaining, len(new))
        request["completed_target_ids"] = sorted(done | new)
        request["remaining_count"] = max(0, remaining - len(new))
        if request["remaining_count"] == 0:
            reward += float(request["completion_reward"])
    return science, required, request_targets, reward


def evaluate_policies(planner, payload):
    now = parse_utc(payload["now_utc"])
    night = planner.state.current_night(now)
    if night is None:
        return []
    index, _, end = night
    hours = (now - planner.state.survey_start).total_seconds() / 3600.
    results = []
    for policy in ("balanced", "required", "requests", "immediate"):
        equivalent = (policy == "requests" and not any(r.get("remaining_count", 0) > 0 for r in planner.active_requests))
        equivalent = equivalent or (policy == "required" and not any(r and f < planner.state.scoring.required_threshold
            for r, f in zip(planner.state.required, planner.state.factor)))
        if equivalent:
            results.append(dict(deepcopy(results[0]), policy=policy))
            continue
        probe = copy(planner)
        probe.state = deepcopy(planner.state)
        probe.active_requests = deepcopy(planner.active_requests)
        probe._policy_preview = True
        probe.required_priority = 2. if policy == "required" else 1.
        probe.request_priority = 2. if policy == "requests" else 1.
        probe.science_scarcity_enabled = policy != "immediate"
        probe.exposure_margin = planner.exposure_margin
        probe.state.update_scale(hours)
        # Freeze inferred throughput, while plan() advances astronomical geometry.
        probe.state.update_scale = lambda _hours: None
        moment = now
        total_seconds = count = fibres = required = request_targets = 0
        science = reward = 0.
        programs = []
        for _ in range(3):
            if (end - moment).total_seconds() < probe.state.min_exposure:
                break
            probe._preview_best = None
            action = probe.plan(moment, end, index, (moment - probe.state.survey_start).total_seconds() / 3600.)
            if action is None or probe._preview_best is None:
                break
            _, duration, _, chosen, _, _ = probe._preview_best
            program = action["program"]
            moment += timedelta(seconds=duration)
            gain, req, targets, request_reward = project_exposure(probe, chosen, duration, program, moment)
            science += gain
            required += req
            request_targets += targets
            reward += request_reward
            count += 1
            fibres += len(chosen)
            total_seconds += duration
            programs.append(program)
        if not count:
            results.append({"policy": policy, "available": False})
            continue
        results.append({"policy": policy, "available": True, "simulated_exposures": count,
                        "simulated_minutes": round(total_seconds / 60., 2),
                        "mean_fibres": round(fibres / count, 2), "programs": programs,
                        "predicted_science_gain": round(science, 4),
                        "predicted_science_per_hour": round(science * 3600 / total_seconds, 3),
                        "predicted_required_completions": required,
                        "predicted_request_target_completions": request_targets,
                        "predicted_request_reward": reward,
                        "scope": "Up to three nominal-hit exposures, NOT a full night; fixed throughput, uncertain weather; no action executed."})
    return results
