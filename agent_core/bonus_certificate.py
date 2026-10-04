"""Additional paid-report path from confirmed unsaturated DARK observations.
The bound is conditional on absence of unannounced directional attenuation.
Nominal healthy efficiency .95 and relative decline .55 are inherited model
assumptions, not a calibrated healthy lower bound or a fault probability.
"""
from statistics import median
from datetime import timedelta
import json
from .geometry import parse_utc

NOMINAL_HEALTHY_EFFICIENCY=.95
EXISTING_PAID_DECLINE=.55
EFFICIENCY_CEILING=NOMINAL_HEALTHY_EFFICIENCY*EXISTING_PAID_DECLINE


def sky_warning(notices):
    for notice in notices:
        kind=notice.partition('|')[0] if isinstance(notice,str) else notice.get('event_kind')
        if kind not in ('earthquake','terrain_obstruction'):return True
    return False


def mount_consistent(planner):
    mount=planner.mount
    count=sum(len(points) for _,_,points in mount.history)
    return len(mount.history)>=3 and count>=24 and mount.errors(mount.offset)<=.02*count


def collect(planner,payload,hours):
    state=planner.state;result=payload.get('last_result') or {}
    if any(m.get('record_type')=='state_resync' for m in payload.get('new_messages',())):
        state._bonus_certificates=[]
        return
    if result.get('action')!='observe' or not state.pending or state.pending_program!='DARK':return
    if sky_warning(getattr(state,'_certificate_pending_notices',())) or sky_warning(state.notices):return
    if any(sky_warning(m.get('notices',())) for m in payload.get('new_messages',()) if m.get('record_type')=='bulletin'):return
    if not mount_consistent(planner):return
    scoring=state.scoring;mult=scoring.program_multipliers['DARK'];threshold=scoring.program_bands['DARK']
    bounds=[];azimuths=[]
    for hit in result.get('hits',()):
        tid=hit['target_id'];prediction=state.pending.get(tid)
        if prediction is None or planner._direction_factor(prediction.alt,prediction.az)<1.:continue
        i=state.index_of[tid];weight=state.weight[i];score=float(hit['score'])
        if not weight or not state.flux[i] or not state.pending_duration:continue
        if not weight*scoring.mismatch_multiplier+1e-5<score<.97*weight*mult:continue
        # A matching DARK bonus proves band quality>=threshold independently
        # of instrument throughput. At nonsaturation the score fixes q_exp.
        upper=score/(weight*mult)*scoring.f0t0/(state.flux[i]*state.pending_duration*threshold)
        bounds.append(upper);azimuths.append(prediction.az)
    if not bounds:return
    row={'hours':hours,'night':state.pending_night,'upper':max(bounds),'hits':len(bounds),
         'sector':int(median(azimuths)//90),'now_utc':payload['now_utc']}
    history=getattr(state,'_bonus_certificates',[])
    history.append(row);state._bonus_certificates=[r for r in history[-128:] if hours-r['hours']<=48.]


def evidence(planner,hours):
    s=planner.state
    if getattr(planner,'_await_report_result',False):return None
    if getattr(planner,'_false_since_correct',0)<s.false_report_free_allowance:return None
    if getattr(planner,'_paid_diagnostic_attempts',0)>=1:return None
    if sky_warning(s.notices) or not mount_consistent(planner):return None
    if hours-getattr(s,'_earthquake_seen_hours',float('-inf'))<7*24:return None
    now=s.survey_start+timedelta(hours=hours)
    remaining=sum(max(0,(end-max(start,now)).total_seconds())/3600 for start,end in s.nights)
    if remaining<24:return None
    after=max(getattr(planner,'_last_false_hours',float('-inf')),planner.last_report_hours)
    rows=[r for r in getattr(s,'_bonus_certificates',())
          if r['hours']>after and hours-r['hours']<=48 and r['upper']<EFFICIENCY_CEILING]
    by={}
    for r in rows:by.setdefault(r['night'],[]).append(r)
    nights=sorted(by)[-2:]
    if len(nights)<2 or nights[1]!=nights[0]+1:return None
    groups=[by[n] for n in nights]
    if min(map(len,groups))<2:return None
    selected=groups[0]+groups[1]
    if hours-max(r['hours'] for r in groups[-1])>2:return None
    if len({r['sector'] for r in selected})<2:return None
    return {'night_counts':[len(g) for g in groups],'night_indices':nights,
            'max_upper':max(r['upper'] for r in selected),'ceiling':EFFICIENCY_CEILING,
            'since_last_report_hours':hours-planner.last_report_hours,'remaining_hours':remaining,
            'certificates':selected}


def report(planner,hours,payload):
    info=evidence(planner,hours)
    if info is None:return None
    planner._paid_diagnostic_attempts=getattr(planner,'_paid_diagnostic_attempts',0)+1
    planner.reports+=1;planner.last_report_hours=hours;planner._await_report_result=True
    planner._pending_report_ratio=info['max_upper']/NOMINAL_HEALTHY_EFFICIENCY
    planner.suspicion_hours=[]
    planner.log('bonus_certificate_report: '+json.dumps(dict(now_utc=payload['now_utc'],**info),separators=(',',':')))
    return {'action':'report','reason':'Repeated matched DARK exposures imply low effective instrument throughput; bounded paid diagnostic','decision_source':'rule'}
