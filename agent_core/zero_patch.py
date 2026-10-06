"""Short spatial backoff after a fully zero exposure, without fault inference."""
from collections import deque

LIFETIME_HOURS = 10. / 60.


def remember_zero_patch(state, hits, hours):
    if not hits or any(score != 0. for score in hits.values()):
        return
    points = []
    for target, prediction in state.pending.items():
        i = state.index_of.get(target)
        if (target in hits and i is not None and state.weight[i] > 0.
                and state.flux[i] > 0.):
            points.append((prediction.az, prediction.alt))
    if len(points) < 3:
        return
    if not hasattr(state, '_temporary_zero_blocks'):
        state._temporary_zero_blocks = deque(maxlen=80)
    for az, alt in points:
        state._temporary_zero_blocks.append((hours + LIFETIME_HOURS, az, alt))


def active_zero_patches(state, hours):
    rows = getattr(state, '_temporary_zero_blocks', ())
    return [(az, alt) for until, az, alt in rows if hours < until]
