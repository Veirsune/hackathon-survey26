"""Small discrete sky/efficiency filter driven only by public target scores."""
import math

EFFICIENCIES=tuple(.2+.05*i for i in range(17))
SKIES=tuple(.2+.04*i for i in range(41))


def initial_efficiency():
    weights=[math.exp(-.5*((e-.95)/.12)**2)+.01 for e in EFFICIENCIES]
    total=sum(weights)
    return [w/total for w in weights]


def infer(rows,program,scoring,old_probs=None,old_sky=1.,elapsed=1.,details=False):
    """Rows contain (public geometry, flux*time*geometry/F0t0, score/weight)."""
    initial=initial_efficiency()
    previous=old_probs or initial
    eff_prior=[.9*p+.1*q for p,q in zip(previous,initial)]
    sigma=.25*math.sqrt(1.+min(8.,max(0.,elapsed)))
    sky_prior=[]
    for sky in SKIES:
        transition=math.exp(-.5*(math.log(sky/max(.1,old_sky))/sigma)**2)
        broad=math.exp(-.5*(math.log(sky)/.5)**2)
        sky_prior.append(.8*transition+.2*broad)
    scores=[]
    for j,sky in enumerate(SKIES):
        multipliers=[scoring.program_multiplier(program,scoring.program_band(sky*model)) for model,_,_ in rows]
        # A normalized score above the mismatch cap proves a matching program.
        # Do not let a soft noise prior override this exact public constraint.
        if any(observed>scoring.mismatch_multiplier+1e-5 and multiplier==scoring.mismatch_multiplier
               for (_,_,observed),multiplier in zip(rows,multipliers)):
            continue
        for k,eff in enumerate(EFFICIENCIES):
            loss=0.
            for (_model,dose,observed),multiplier in zip(rows,multipliers):
                predicted=max(1e-9,min(1.,dose*sky*eff)*multiplier)
                error=abs(math.log(predicted/max(1e-9,observed)))
                # Huber loss tempers unmodelled directional or time-varying
                # effects; all fibers share one exposure, so evidence is capped.
                loss+=error*error if error<=.15 else .3*error-.0225
            logp=math.log(max(1e-12,sky_prior[j]*eff_prior[k]))-.5*min(4,len(rows))*loss/len(rows)/(.08*.08)
            scores.append((logp,j,k))
    if not scores:
        return None
    maximum=max(row[0] for row in scores)
    eff_probs=[0.]*len(EFFICIENCIES);sky_sum=0.;total=0.
    sky_probs=[0.]*len(SKIES)
    for logp,j,k in scores:
        p=math.exp(logp-maximum)
        eff_probs[k]+=p;sky_sum+=p*SKIES[j];total+=p
        sky_probs[j]+=p
    eff_probs=[p/total for p in eff_probs]
    cumulative=0.;estimate=EFFICIENCIES[-1]
    for eff,p in zip(EFFICIENCIES,eff_probs):
        cumulative+=p
        if cumulative>=.5:
            estimate=eff;break
    result=(eff_probs,sky_sum/total,estimate)
    return result+([p/total for p in sky_probs],) if details else result


def record_exposure(state,hits,hours):
    clear=getattr(state,'_latent_direction_clear',set())
    rows=[]
    for target_id,prediction in state.pending.items():
        if target_id not in hits or target_id not in clear:continue
        i=state.index_of[target_id]
        weight=state.weight[i]
        if weight<=0 or prediction.model<=0 or hits[target_id]<=0:continue
        dose=state.flux[i]*state.pending_duration*prediction.model/state.scoring.f0t0
        if dose>0:rows.append((prediction.model,dose,hits[target_id]/weight))
    if len(rows)<4 or sum(score<.97 for _,_,score in rows)<3:return
    mismatch=state.scoring.mismatch_multiplier
    informative=any(score>mismatch+1e-5 for _,_,score in rows) or sum(abs(score-mismatch)<1e-5 for _,_,score in rows)>=3
    if not informative:return
    previous=getattr(state,'_latent_band',None)
    posterior=infer(rows,state.pending_program,state.scoring,
        previous[0] if previous else None,previous[1] if previous else 1.,
        hours-previous[3] if previous else 1.,details=True)
    if posterior is None:return
    probs,sky,eff,sky_probs=posterior
    state._latent_band=(probs,sky,eff,hours,sky_probs)


def band_scale(state,hours):
    posterior=getattr(state,'_latent_band',None)
    # Instrument evidence may survive overnight, but never indefinitely.
    if posterior is None or hours-posterior[3]>24.:
        return state.scale/.95
    return state.scale/posterior[2]


def feedback_matched(state, prediction, hours, score, weight, original, target_id):
    """A heuristic posterior threshold, never a calibrated fault probability."""
    if score>weight*state.scoring.mismatch_multiplier+1e-5:
        return True
    posterior=getattr(state,'_latent_band',None)
    if (posterior is None or len(posterior)<5 or abs(posterior[3]-hours)>1e-9
            or target_id not in getattr(state,'_latent_direction_clear',set())):
        return original
    probability=sum(p for sky,p in zip(SKIES,posterior[4])
                    if state.scoring.program_band(sky*prediction.model)==state.pending_program)
    if probability>=.9:return True
    if probability<=.1:return False
    return original
