import importlib
from types import SimpleNamespace
import unittest
from agent_core.scoring import ScoringModel


class LatentFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scoring=ScoringModel({}, {})
        cls.module=importlib.import_module('agent_core.latent_band')

    def state(self, dark_mass):
        skies=self.module.SKIES
        low=next(i for i,s in enumerate(skies) if self.scoring.program_band(s)=='BACKUP')
        high=next(i for i,s in enumerate(skies) if self.scoring.program_band(s)=='DARK')
        probs=[0.]*len(skies);probs[low]=1.-dark_mass;probs[high]=dark_mass
        return SimpleNamespace(scoring=self.scoring,pending_program='DARK',
               _latent_band=([],1.,.5,10.,probs),_latent_direction_clear={'t'})

    def matched(self,state,score=.7,original=False,hours=10.,target='t'):
        return self.module.feedback_matched(state,SimpleNamespace(model=1.),hours,score,1.,original,target)

    def test_exact_bonus_overrides_even_confident_mismatch(self):
        self.assertTrue(self.matched(self.state(0.),score=1.08))

    def test_only_high_confidence_can_change_ambiguous_feedback(self):
        self.assertTrue(self.matched(self.state(.95)))
        self.assertFalse(self.matched(self.state(.05),original=True))
        self.assertFalse(self.matched(self.state(.5)))
        self.assertTrue(self.matched(self.state(.5),original=True))

    def test_stale_and_directionally_affected_fallback(self):
        self.assertFalse(self.matched(self.state(.95),hours=11.))
        self.assertFalse(self.matched(self.state(.95),target='affected'))

    def test_sky_marginal_normalizes_and_respects_confirmed_bonus(self):
        doses=(.2,.4,.8,1.4,3.,4.,5.,6.)
        rows=[(1.,d,min(1.,d*.3*.95)*1.06) for d in doses]
        posterior=self.module.infer(rows,'BACKUP',self.scoring,details=True)
        self.assertAlmostEqual(sum(posterior[3]),1.)
        self.assertAlmostEqual(sum(p for s,p in zip(self.module.SKIES,posterior[3])
            if self.scoring.program_band(s)!='BACKUP'),0.)
