"""Online ridge/RLS residual score prediction from delivered feedback only.

No hidden factors or weather labels. Correlated fibres share one exposure's
learning weight. The learned quantity is score error, not true efficiency.
"""
import json
import math
import numpy as np
from .optimizer import completion
from .latent_band import band_scale
from .latent_declaration import choose_program

DIM=10


class Model:
    def __init__(self):
        self.coef=np.zeros(DIM);self.cov=np.eye(DIM)*2.
        self.exposures=0;self.total_updates=0;self.changes=0;self.last_residual=0.
        self.squared_error=0.;self.baseline_squared_error=0.;self.pending=None

    def predict(self,x):
        # Shrink unsupported directions rather than interpreting extrapolation
        # as a known score multiplier. This is not a calibrated probability.
        uncertainty=max(0.,float(x@self.cov@x))
        return max(-math.log(4),min(math.log(4),float(x@self.coef)/(1.+uncertainty)))

    def update(self,rows):
        if not rows:return
        self.cov/= .98
        residuals=[]
        for x,y in rows:
            prediction=self.predict(x)
            self.squared_error+=(y-prediction)**2/len(rows)
            self.baseline_squared_error+=y*y/len(rows)
            px=self.cov@x
            gain=px/(len(rows)+float(x@px))
            self.coef+=gain*(y-float(x@self.coef))
            self.cov-=np.outer(gain,px)
            residuals.append(y)
        self.cov=(self.cov+self.cov.T)/2.
        self.last_residual=float(np.median(residuals))
        self.exposures+=1;self.total_updates+=1


def model(p):
    if not hasattr(p,'_outcome_model'):p._outcome_model=Model()
    return p._outcome_model


def features(p,item,duration,factor):
    s=p.state;m=model(p);az=math.radians(item['az']);alt=math.radians(item['alt'])
    return np.array([1.,math.cos(alt)*math.sin(az),math.cos(alt)*math.cos(az),
        1.-math.sin(alt),math.log(max(1.,duration)/900.),factor,
        math.log(max(.05,s.scale)),float(bool(s.notices)),
        max(-2.,min(2.,m.last_residual)),math.log(max(.001,s.flux[item['i']]))/4.])


def predicted_rows(p,chosen,duration,program,hours):
    s=p.state;sky=band_scale(s,hours);rows=[]
    for item in chosen.values():
        factor=completion(item,duration);a,b,c=item['quality_coefficients']
        quality=max(0.,a+b*duration/2.+c*duration*duration/3.)
        nominal=s.weight[item['i']]*factor*s.scoring.program_multiplier(program,s.scoring.program_band(quality*sky))
        rows.append((item['i'],features(p,item,duration,factor),nominal))
    return rows


def collect(p,result):
    m=model(p);pending=m.pending;m.pending=None
    if not result:return
    if result.get('action')=='report':
        # Repairs invalidate the previous score residual, whatever its cause.
        if result.get('correct'):
            fresh=Model();fresh.total_updates=m.total_updates;fresh.changes=m.changes
            p._outcome_model=fresh
        return
    if result.get('action')!='observe' or pending is None:return
    hits={h.get('target_id'):float(h.get('score',0.)) for h in result.get('hits',())}
    rows=[]
    for tid,x,predicted in pending:
        if tid not in hits or predicted<=1e-9:continue
        y=math.log(max(.1,min(10.,hits[tid]/predicted)))
        rows.append((x,y))
    m.update(rows)


def select(p,candidates,best,hours):
    m=model(p)
    if m.exposures<8:return best
    s=p.state
    def value(candidate):
        rate,duration,program,chosen,_,_=candidate
        program=choose_program(s,chosen,duration,program,hours)
        correction=0.
        for i,x,nominal in predicted_rows(p,chosen,duration,program,hours):
            estimate=min(s.weight[i]*max(s.scoring.program_multipliers.values()),nominal*math.exp(m.predict(x)))
            correction+=max(0.,estimate-s.best_score[i])-max(0.,nominal-s.best_score[i])
        # Both terms are score per (exposure seconds + original search overhead).
        # Existing mandatory/request priorities are unchanged, not learned away.
        return rate+correction/(duration+40.)
    selected=max([best]+list(candidates),key=value)
    if selected is not best:m.changes+=1
    return selected


def remember(p,chosen,duration,program,hours):
    m=model(p)
    m.pending=[(p.state.ids[i],x.copy(),score) for i,x,score in predicted_rows(p,chosen,duration,program,hours)]


def summary(p):
    m=model(p)
    p.log('online_outcome_summary: '+json.dumps(dict(exposures=m.exposures,total_updates=m.total_updates,
        changed_selections=m.changes,prequential_squared_error=m.squared_error,
        baseline_squared_error=m.baseline_squared_error,coefficients=m.coef.tolist())))
