"""Bounded diagnostic for catastrophic, persistent public throughput loss.

Uses no card identifiers, event dates or truth fields. A report is an experiment,
not a claim that low throughput uniquely identifies an instrument fault.
"""
from statistics import median
import math
from .report_budget import all_sky_weather

def collect(planner,payload,hours):
    s=planner.state;r=payload.get('last_result') or {}
    rows=getattr(planner,'_collapse_rows',[])
    if r.get('action')=='report':
        pending=getattr(planner,'_collapse_pending',None)
        if pending is not None:
            if r.get('correct') is False:
                planner._collapse_locked=True
                planner._collapse_paid_false=getattr(planner,'_collapse_paid_false',0)+int(pending)
            elif r.get('correct') is True:
                planner._collapse_locked=False
            planner._collapse_pending=None
        planner._collapse_rows=[]
        return
    if r.get('action')!='observe':return
    hits={h['target_id']:float(h.get('score',0.)) for h in r.get('hits',())}
    assigned=max(1,len(s.pending))
    if len(hits)<.8*assigned or getattr(s,'_pending_sky_weather',True) or all_sky_weather(s.notices):
        planner._collapse_rows=[];return
    multiplier=min(s.scoring.program_multipliers.get(s.pending_program,1.),s.scoring.mismatch_multiplier)
    if multiplier<=0:return
    values=[]
    for tid,pred in s.pending.items():
        if tid not in hits or tid not in getattr(s,'_latent_direction_clear',set()):continue
        i=s.index_of[tid];w=s.weight[i]
        dose=s.flux[i]*s.pending_duration*pred.model/s.scoring.f0t0
        if w<=0 or dose<=0:continue
        normalized=hits[tid]/w
        # Zero signals are ambiguous (e.g. opaque sky or obstruction).
        # Require a measurable signal for this throughput diagnostic.
        if normalized<=0:continue
        # Saturated factors have no upper throughput bound.
        if normalized>=.97*multiplier:continue
        upper=normalized/(multiplier*dose)
        if math.isfinite(upper) and upper>=0:values.append((tid,upper))
    if len(values)<4:
        planner._collapse_rows=[];return
    value=sorted(v for _,v in values)[int(.75*(len(values)-1))]
    rows=(rows+[(hours,value,tuple(t for t,_ in values))])[-3:]
    planner._collapse_rows=rows
    if len(rows)>=3 and rows[-1][0]-rows[0][0]<=24 and all(v>.15 for _,v,_ in rows):
        planner._collapse_locked=False

def report(planner,hours,payload):
    s=planner.state
    if getattr(planner,'_collapse_locked',False) or getattr(planner,'_collapse_pending',None) is not None:return None
    if getattr(planner,'_await_report_result',False) or all_sky_weather(s.notices):return None
    if hours-planner.last_report_hours<6.:return None
    rows=getattr(planner,'_collapse_rows',[])[-2:]
    if len(rows)<2 or rows[-1][0]-rows[0][0]>8 or hours-rows[-1][0]>1:return None
    if any(v>=.025 for _,v,_ in rows) or len(set(t for _,_,ids in rows for t in ids))<8:return None
    used=getattr(planner,'_false_since_correct',0);paid=used>=s.false_report_free_allowance
    if paid and getattr(planner,'_collapse_paid_false',0)>=2:return None
    planner._collapse_pending=paid
    planner._collapse_rows=[]
    planner._await_report_result=True
    planner._pending_report_ratio=max(v for _,v,_ in rows)
    planner.reports+=1;planner.last_report_hours=hours;planner.suspicion_hours=[]
    planner.log(f'collapse_diagnostic: {payload["now_utc"]} public_upper={planner._pending_report_ratio:.6f} paid={paid}')
    return dict(action='report',reason='Repeated catastrophic throughput loss with consistent fibre membership; bounded diagnostic',decision_source='rule')
