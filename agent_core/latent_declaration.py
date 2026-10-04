"""Correct the declaration after preserving original field and duration selection."""
from .optimizer import marginal_gain
from .latent_band import band_scale


def choose_program(state, chosen, duration, original, hours):
    posterior=getattr(state, '_latent_band', None)
    if state.force_program or posterior is None or hours-posterior[3]>24.:
        return original
    scale=band_scale(state,hours)
    # Use standalone gain evaluation: cached duration values include old bands.
    items=[dict(item,band_scale=scale) for item in chosen.values()]
    def gain(program):
        return sum(marginal_gain(item,duration,program,state.scoring) for item in items)
    best, value=original,gain(original)
    for program in ('DARK','BRIGHT','BACKUP'):
        proposed=gain(program)
        if proposed>value+1e-12:
            best,value=program,proposed
    return best
