import copy,heapq,math,unittest
from types import SimpleNamespace as S
from unittest.mock import Mock,patch
from agent_core import compute_fastpath as fast,planner as pm
from agent_core.geometry import SIDEREAL_DEG_PER_SECOND as sidereal
class ComputeTests(unittest.TestCase):
 def state(self):
  n=1000;return S(ra=[i*37%360. for i in range(n)],flux=[.04+i%10*.1 for i in range(n)],weight=[1.+i%3*.2 for i in range(n)],required=[i%5==0 for i in range(n)],hmax=[45.+i%80 for i in range(n)],last_night=[10+i%30 for i in range(n)],factor=[i%10/10 for i in range(n)],best_score=[i%5/5 for i in range(n)],max_exposure=3600,min_exposure=60,scale=.73,scoring=S(uniformity_band_width_deg=10.,uniformity_threshold=.5,required_threshold=.5,required_penalty=50.,program_bands={'BRIGHT':.4},f0t0=800.))
 def test_priorities_and_heap(self):
  s=self.state();p=S(state=s,science_scarcity_enabled=True,required_priority=2.,log=lambda _:None);requests={7:[(.5,100,23.,'r')]};visible,items=fast.preliminary(p,None,3,127.,requests,1.2);expected=[];indices=set()
  for i in range(len(s.ra)):
   missing=s.required[i] and s.factor[i]<.5;science=max(0.,s.weight[i]*1.2-s.best_score[i]);poorer=.4*.95;science*=1.+2.*(1.-poorer/s.scale)*(1.-min(1.,max(0.,s.flux[i]*3600*poorer/800.)));value=science+(50. if missing else 0.)+sum(x[2] for x in requests.get(i,()));ha=(127.-s.ra[i]+180.)%360.-180.;up=(s.hmax[i]-ha)/sidereal if s.hmax[i]<180 else 1e9
   if value>.01 and -s.hmax[i]<=ha<=s.hmax[i] and up>=60:
    indices.add(i);urgency=(1.+(2./max(1,s.last_night[i]-3+1) if missing else 0.))*2.;expected.append((value*math.sqrt(max(.001,s.flux[i]))*urgency,i))
  self.assertEqual(visible,indices);self.assertEqual([i for _,i in heapq.nlargest(160,items)],[i for _,i in heapq.nlargest(160,expected)])
  for a,b in zip(items,expected):self.assertEqual(a[1],b[1]);self.assertAlmostEqual(a[0],b[0],12)
 def test_uniformity_changes(self):
  s=self.state();totals,done=fast.uniformity_counts(s);s.factor=[0.]*1000;self.assertEqual(fast.uniformity_counts(s)[1],{});s.factor[0]=1.;self.assertEqual(fast.uniformity_counts(s)[1],{0:1});self.assertEqual(totals,fast.uniformity_counts(s)[0])
 def test_history_isolation_reset(self):
  s=S(clean_history=[(1.,0,.4),(1.,0,.8),(2.,1,.7)]);self.assertEqual(fast.clean_exposure_history(s),[(1.,0,(.4+.8)/2),(2.,1,.7)]);s.clean_history.append((2.,1,.9));self.assertEqual(fast.clean_exposure_history(s),[(1.,0,(.4+.8)/2),(2.,1,(.7+.9)/2)]);q=copy.deepcopy(s);q.clean_history.append((3.,2,.2));fast.clean_exposure_history(q);self.assertEqual(len(fast.clean_exposure_history(s)),2);s.clean_history=[];self.assertEqual(fast.clean_exposure_history(s),[])
 def test_full_turn_units(self):
  p=pm.Planner.__new__(pm.Planner);p.state=S(fast_level=2);p._decide=lambda payload:{'action':'wait','duration_seconds':60}
  p.calendar_governor=Mock()
  with patch.object(pm,'process_time',side_effect=[100.,115.]):action=p.decide({'wallclock':{'speed_factor':1.5,'remaining_seconds':700.,'wall_remaining_seconds':1000.}})
  self.assertEqual(p._turn_costs[2],10.);self.assertEqual(p._turn_counts[2],1);self.assertEqual(action['action'],'wait')
  p.calendar_governor.record.assert_called_once_with(10.,2,False,60.)
 def test_optional_fallback(self):
  with patch.object(fast,'np',None):self.assertIsNone(fast.uniformity_counts(self.state()));self.assertIsNone(fast.preliminary(S(log=lambda _:None),None,0,0.,{},1.2))
if __name__=='__main__':unittest.main()
