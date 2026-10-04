from copy import deepcopy
from datetime import datetime,timedelta,timezone
import importlib
from types import SimpleNamespace
import unittest
from agent_core.scoring import ScoringModel


class ProjectionState:
    def __init__(self,scoring,start):
        self.scoring=scoring;self.survey_start=start;self.scale=.5
        self._latent_band=([],1.,.5,0.)
        self.weight=[1.];self.best_score=[0.];self.factor=[0.]
        self.required=[False];self.ids=['t'];self.min_exposure=60
    def current_night(self,now):return 0,self.survey_start,self.survey_start+timedelta(hours=1)
    def update_scale(self,hours):pass


class PreviewPlanner:
    def __init__(self,state):self.state=state;self.active_requests=[]
    def plan(self,now,end,index,hours):
        item=dict(i=0,quality_coefficients=(1.,0.,0.),factor_scale=.005,band_scale=.5/.95)
        self._preview_best=(1.,100,'BRIGHT',{0:item},60.,90.)
        return dict(action='observe',duration_seconds=100,program='DARK')


class LatentPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scoring=ScoringModel({}, {})
        cls.tool=importlib.import_module('agent_core.planning_tools')

    def fixture(self):
        start=datetime(2026,11,23,tzinfo=timezone.utc)
        return PreviewPlanner(ProjectionState(self.scoring,start)),start

    def test_projection_uses_latent_sky_not_search_band_and_repeats_do_not_add(self):
        planner,start=self.fixture();planner.plan(start,None,0,0.)
        chosen=planner._preview_best[3]
        first=self.tool.project_exposure(planner,chosen,100,'DARK',start+timedelta(seconds=100))
        second=self.tool.project_exposure(planner,chosen,100,'DARK',start+timedelta(seconds=200))
        self.assertAlmostEqual(first[0],.6)
        self.assertEqual(second,(0.,0,0,0.))

    def test_full_preview_uses_returned_program_and_preserves_actual_ledger(self):
        planner,start=self.fixture();before=deepcopy(planner.state.__dict__)
        rows=self.tool.evaluate_policies(planner,{'now_utc':start.isoformat()})
        for row in rows:
            self.assertEqual(row['programs'],['DARK']*3)
            self.assertAlmostEqual(row['predicted_science_gain'],.6)
        for key in ['best_score','factor','_latent_band']:
            self.assertEqual(planner.state.__dict__[key],before[key])

    def test_stale_sky_estimate_falls_back_to_original_scale(self):
        planner,start=self.fixture();planner.plan(start,None,0,0.)
        score=self.tool.project_exposure(planner,planner._preview_best[3],100,'DARK',start+timedelta(hours=25))
        self.assertAlmostEqual(score[0],.5)
