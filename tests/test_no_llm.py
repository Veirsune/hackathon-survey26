"""An injected API configuration must never activate a model on this branch."""
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_core.geometry import altaz_to_radec, local_sidereal_deg, parse_utc
from agent_core.llm_client import LLMClient
from agent_core.planner import Planner
from agent_core.state import SurveyState
from agent_core.validation import validate_action


class OfflineTests(unittest.TestCase):
    def test_injected_key_and_enable_flag_cannot_activate_client_or_planner(self):
        settings = {"OPENAI_API_KEY": "fake-test-key", "OPENAI_BASE_URL": "https://unit.test/v1",
                    "OPENAI_MODEL": "test-model", "AGENT_LLM_ENABLED": "1"}
        with patch.dict(os.environ, settings, clear=True), patch(
                "urllib.request.urlopen", side_effect=AssertionError("unexpected network")) as network:
            client = LLMClient()
            client.begin_night(0)
            self.assertIsNone(client.ask_json("test", {}, 900))
            self.assertFalse(client.configured)
            start, end = "2026-11-10T02:00:00Z", "2026-11-10T04:00:00Z"
            lat, lon = -24.6157, -70.3976
            ra, dec = altaz_to_radec(60., 100., local_sidereal_deg(parse_utc(start), lon), lat)
            state = SurveyState({
                "site": {"latitude_deg": lat, "longitude_deg": lon},
                "survey": {"start_utc": start, "end_utc": end, "nights": [
                    {"observing_start_utc": start, "observing_end_utc": end}]},
                "instrument": {"grid_side": 4, "n_fibers": 16, "glass_side_deg": .632455,
                    "pitch_deg": .632455, "fov_side_deg": 2.52982,
                    "exposure": {"min_duration_seconds": 60, "max_duration_seconds": 3600}},
                "targets": {"columns": ["target_id", "ra_deg", "dec_deg", "feature_flux", "science_weight", "required"],
                    "rows": [["test-target", ra, dec, .8, 1., True]]}})
            planner = Planner(state)
            action = planner.decide({"now_utc": start, "new_messages": [], "last_result": None,
                "latest_bulletin": {"notices": []}, "active_requests": [],
                "wallclock": {"remaining_seconds": 900}})
            action = validate_action(action, state, 0)
            self.assertEqual(action["action"], "observe")
            self.assertEqual(planner.llm.calls_made, 0)
            self.assertFalse(planner.llm.retry_available)
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
