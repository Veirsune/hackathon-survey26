import copy
import importlib
from types import SimpleNamespace
import unittest
from agent_core.scoring import ScoringModel


class DeclarationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scoring=ScoringModel({}, {})
        cls.module=importlib.import_module('agent_core.latent_declaration')

    def inputs(self):
        state=SimpleNamespace(scale=.5,force_program=None,scoring=self.scoring,
                              _latent_band=([],1.,.5,10.))
        item=dict(quality_coefficients=(1.,0.,0.),factor_scale=.01,max_duration=900,
                  band_scale=.5/.95,weight=1.,best_score=0.,required_missing=False,
                  confidence=1.,_exposure_cache={100:(1.,'BRIGHT',999.,999.)})
        return state,{0:item}

    def test_correction_changes_only_declaration_and_ignores_old_band_cache(self):
        state,chosen=self.inputs();before=copy.deepcopy(chosen)
        self.assertEqual(self.module.choose_program(state,chosen,100,'BRIGHT',11.),'DARK')
        self.assertEqual(chosen,before)

    def test_forced_missing_and_stale_predictions_preserve_original(self):
        state,chosen=self.inputs()
        state.force_program='BACKUP'
        self.assertEqual(self.module.choose_program(state,chosen,100,'BACKUP',11.),'BACKUP')
        state.force_program=None
        self.assertEqual(self.module.choose_program(state,chosen,100,'BRIGHT',35.),'BRIGHT')
        state._latent_band=None
        self.assertEqual(self.module.choose_program(state,chosen,100,'BRIGHT',11.),'BRIGHT')

    def test_already_completed_science_keeps_tie(self):
        state,chosen=self.inputs();chosen[0]['best_score']=2.
        self.assertEqual(self.module.choose_program(state,chosen,100,'BACKUP',11.),'BACKUP')
