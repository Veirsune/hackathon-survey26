"""Exact public-data accelerations; optional NumPy, original scalar fallback."""
import math
from statistics import median
try:
 import numpy as np
except ImportError:
 np=None

def arrays(state):
 cache=getattr(state,'_compute_arrays',None)
 if cache is None:
  cache={k:np.asarray(getattr(state,k)) for k in ('ra','flux','weight','required','hmax','last_night')}
  band_order={}
  for ra in state.ra:
   b=int(ra//state.scoring.uniformity_band_width_deg);band_order[b]=band_order.get(b,0)+1
  cache['bands']=np.asarray([int(ra//state.scoring.uniformity_band_width_deg) for ra in state.ra]);cache['totals']=band_order;state._compute_arrays=cache
 return cache

def uniformity_counts(state):
 if np is None:return None
 cache=arrays(state);done_values=np.bincount(cache['bands'][np.asarray(state.factor)>=state.scoring.uniformity_threshold],minlength=max(cache['totals'])+1)
 return dict(cache['totals']),{b:int(done_values[b]) for b in cache['totals'] if done_values[b]}

def preliminary(planner,now,night_index,lst,requests,top_multiplier):
 if not getattr(planner,'_compute_announced',False):
  planner._compute_announced=True
  planner.log('compute_fastpath: activated='+str(np is not None)+' numpy='+str(np.__version__ if np is not None else 'unavailable')+' scalar_fallback='+str(np is None))
 if np is None:return None
 s=planner.state;c=arrays(s);missing=c['required'] & (np.asarray(s.factor)<s.scoring.required_threshold)
 science=np.maximum(0.,c['weight']*top_multiplier-np.asarray(s.best_score))
 poorer=s.scoring.program_bands['BRIGHT']*.95
 if getattr(planner,'science_scarcity_enabled',False) and s.scale>poorer and poorer>0:
  completion=np.minimum(1.,np.maximum(0.,c['flux']*s.max_exposure*poorer/s.scoring.f0t0))
  science*=1.+2.*(1.-poorer/s.scale)*(1.-completion)
 value=science+np.where(missing,s.scoring.required_penalty,0.)
 for i,rows in requests.items():value[i]+=sum(row[2] for row in rows)
 ha=(lst-c['ra']+180.)%360.-180.
 # Keep the exact geometry module constant rather than a rounded approximation.
 from .geometry import SIDEREAL_DEG_PER_SECOND
 up=np.where(c['hmax']<180.,(c['hmax']-ha)/SIDEREAL_DEG_PER_SECOND,1e9)
 mask=(value>.01)&(-c['hmax']<=ha)&(ha<=c['hmax'])&(up>=s.min_exposure)
 indices=np.flatnonzero(mask);left=np.maximum(1,c['last_night']-night_index+1)
 urgency=(1.+np.where(missing,2./left,0.))*getattr(planner,'required_priority',1.)
 priorities=value*np.sqrt(np.maximum(.001,c['flux']))*urgency
 return set(map(int,indices)),[(float(priorities[i]),int(i)) for i in indices]

def clean_exposure_history(state):
 values=state.clean_history;cache=getattr(state,'_compute_clean',None)
 if cache is None or cache['source'] is not values or cache['length']>len(values):
  cache={'source':values,'length':0,'groups':{},'rows':{},'history':[]};state._compute_clean=cache
 changed=set()
 for hours,night,ratio in values[cache['length']:]:
  if night>=0 and math.isfinite(hours) and math.isfinite(ratio) and ratio>0:
   key=(hours,night);cache['groups'].setdefault(key,[]).append(ratio);changed.add(key)
 cache['length']=len(values)
 if changed:
  for key in changed:cache['rows'][key]=(*key,median(cache['groups'][key]))
  cache['history']=sorted(cache['rows'].values())
 return cache['history']
