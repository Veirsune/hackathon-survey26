"""Offline-only tests: every attempted HTTP call is mocked; no real credentials."""
from __future__ import annotations

import importlib.util
import json
import os
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / "agent_core/llm_client.py"
SPEC = importlib.util.spec_from_file_location("_kimi_client_under_test", PATH)
kimi = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kimi)

FAKE_ENV = {"OPENAI_API_KEY": "fake-test-secret-never-valid",
            "OPENAI_BASE_URL": "https://unit.test/v1", "OPENAI_MODEL": "test-model"}


def envelope(content='{"answer":42}'):
    return json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")


class FakeResponse:
    def __init__(self, data=None):
        self.data = envelope() if data is None else data
        self.read_limit = None
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        pass
    def read(self, limit):
        self.read_limit = limit
        return self.data[:limit]


class KimiClientTests(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, FAKE_ENV, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        # Even a failing test cannot accidentally issue live HTTP.
        self.network = mock.patch.object(kimi.urllib.request, "urlopen", return_value=FakeResponse())
        self.urlopen = self.network.start()
        self.addCleanup(self.network.stop)

    def test_success_headers_strict_json_and_counters(self):
        logs = []
        client = kimi.LLMClient(log=logs.append)
        self.assertTrue(client.configured)
        self.assertEqual(client.ask_json("Reply with JSON.", {"天气": "晴"}, 900, stage="forecast"), {"answer": 42})
        self.assertEqual((client.calls_made, client.successes, client.last_status), (1, 1, "ok"))
        request = self.urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://unit.test/v1/chat/completions")
        self.assertEqual(request.get_method(), "POST")
        headers = {k.lower(): v for k, v in request.header_items()}
        self.assertEqual(headers["authorization"], "Bearer " + FAKE_ENV["OPENAI_API_KEY"])
        self.assertNotIn("user-agent", headers)
        body = json.loads(request.data)
        self.assertEqual(body["max_tokens"], 2000)
        self.assertNotIn("temperature", body)
        self.assertNotIn("reasoning_effort", body)
        self.assertEqual(json.loads(body["messages"][1]["content"]), {"天气": "晴"})
        self.assertLessEqual(self.urlopen.call_args.kwargs["timeout"], 30)
        self.assertNotIn(FAKE_ENV["OPENAI_API_KEY"], " ".join(logs))

    def test_primary_environment_overrides_fallbacks(self):
        os.environ.update({"KIMI_API_KEY": "fallback-fake", "KIMI_BASE_URL": "https://fallback.test/v1",
                           "KIMI_MODEL": "fallback-model"})
        client = kimi.LLMClient()
        self.assertEqual(client.base_url, FAKE_ENV["OPENAI_BASE_URL"])
        self.assertEqual(client.model, FAKE_ENV["OPENAI_MODEL"])
        for key in FAKE_ENV:
            del os.environ[key]
        fallback = kimi.LLMClient()
        self.assertTrue(fallback.configured)
        self.assertEqual(fallback.base_url, "https://fallback.test/v1")
        self.assertEqual(fallback.model, "fallback-model")

    def test_missing_key_base_or_model_means_no_network(self):
        for missing in FAKE_ENV:
            with self.subTest(missing=missing), mock.patch.dict(os.environ, {k: v for k, v in FAKE_ENV.items() if k != missing}, clear=True):
                client = kimi.LLMClient()
                self.assertFalse(client.configured)
                self.assertIsNone(client.ask_json("test", {}, 900))
                self.assertEqual(client.calls_made, 0)
        self.urlopen.assert_not_called()
        with mock.patch.dict(os.environ, {}, clear=True):
            empty = kimi.LLMClient()
            self.assertEqual((empty.model, empty.base_url), ("unconfigured", "unconfigured"))

    def test_disabled_flag_and_invalid_url_never_call(self):
        os.environ["AGENT_LLM_ENABLED"] = "0"
        disabled = kimi.LLMClient()
        self.assertFalse(disabled.configured)
        self.assertEqual(disabled.last_status, "disabled")
        self.assertIsNone(disabled.ask_json("test", {}, 900))
        del os.environ["AGENT_LLM_ENABLED"]
        for url in ("file:///private", "https://name:secret@unit.test", "https://unit.test?key=secret"):
            os.environ["OPENAI_BASE_URL"] = url
            self.assertFalse(kimi.LLMClient().configured)
        self.urlopen.assert_not_called()

    def test_budget_configuration_is_bounded_and_effort_is_optional(self):
        os.environ.update({"AGENT_LLM_TOTAL_SECONDS": "900", "AGENT_LLM_CALL_SECONDS": "99",
                           "AGENT_LLM_MAX_CALLS": "99", "AGENT_LLM_REASONING_EFFORT": "low"})
        client = kimi.LLMClient()
        self.assertEqual((client.total_budget_seconds, client.call_timeout_seconds, client.max_calls), (120, 30, 8))
        client.ask_json("test", {}, 900)
        body = json.loads(self.urlopen.call_args.args[0].data)
        self.assertEqual(body["reasoning_effort"], "low")
        for name in ("AGENT_LLM_TOTAL_SECONDS", "AGENT_LLM_CALL_SECONDS", "AGENT_LLM_MAX_CALLS"):
            os.environ[name] = "nan"
        fallback = kimi.LLMClient()
        self.assertEqual((fallback.total_budget_seconds, fallback.call_timeout_seconds, fallback.max_calls), (120, 30, 6))

    def test_call_count_and_total_budget_stop_future_attempts(self):
        client = kimi.LLMClient(max_calls=1)
        self.assertIsNotNone(client.ask_json("test", {}, 900))
        self.assertIsNone(client.ask_json("test", {}, 900))
        self.assertEqual(client.last_status, "call_limit")
        exhausted = kimi.LLMClient()
        exhausted.seconds_spent = exhausted.total_budget_seconds
        self.assertIsNone(exhausted.ask_json("test", {}, 900))
        self.assertEqual(exhausted.last_status, "time_budget")
        self.assertEqual(self.urlopen.call_count, 1)

    def test_reserves_last_ninety_wallclock_seconds(self):
        client = kimi.LLMClient()
        self.assertIsNone(client.ask_json("test", {}, 90))
        self.assertIsNone(client.ask_json("test", {}, 40))
        self.assertEqual(client.calls_made, 0)
        self.assertIsNotNone(client.ask_json("test", {}, 95))
        self.assertLessEqual(self.urlopen.call_args.kwargs["timeout"], 5)

    def test_records_real_elapsed_monotonic_time(self):
        client = kimi.LLMClient()
        with mock.patch.object(kimi.time, "monotonic", side_effect=[100.0, 100.0, 100.4, 100.4, 100.4]):
            self.assertEqual(client.ask_json("test", {}, 900), {"answer": 42})
        self.assertAlmostEqual(client.seconds_spent, 0.4)
        self.assertAlmostEqual(client.spent_seconds, 0.4)

    def test_strict_content_rejects_fences_arrays_nonfinite_duplicate_keys_and_prose(self):
        for content in ('```json\n{"x":1}\n```', 'prefix {"x":1}', '[]', '{"x":NaN}', '{"x":1,"x":2}', '{"x":1} trailing'):
            with self.subTest(content=content):
                self.urlopen.return_value = FakeResponse(envelope(content))
                client = kimi.LLMClient()
                self.assertIsNone(client.ask_json("test", {}, 900))
                self.assertEqual(client.successes, 0)

    def test_bad_outer_json_and_oversized_response_are_bounded(self):
        for raw in (b"not json", b"[]", b'{"choices":[]}', b"\xff"):
            with self.subTest(raw=raw):
                self.urlopen.return_value = FakeResponse(raw)
                self.assertIsNone(kimi.LLMClient().ask_json("test", {}, 900))
        response = FakeResponse(b"x" * (kimi.MAX_RESPONSE_BYTES + 2))
        self.urlopen.return_value = response
        client = kimi.LLMClient()
        self.assertIsNone(client.ask_json("test", {}, 900))
        self.assertEqual(client.last_status, "response_too_large")
        self.assertEqual(response.read_limit, kimi.MAX_RESPONSE_BYTES + 1)

    def test_auth_and_bad_request_errors_stop_without_retries_or_secret_logs(self):
        for code in (400, 401, 403):
            with self.subTest(code=code):
                self.urlopen.reset_mock()
                secret = FAKE_ENV["OPENAI_API_KEY"]
                self.urlopen.side_effect = urllib.error.HTTPError("https://unit.test/" + secret, code, secret, {}, None)
                logs = []
                client = kimi.LLMClient(log=logs.append)
                client.begin_night(0)
                self.assertIsNone(client.ask_json(secret, {"private": secret}, 900, stage=secret))
                client.begin_night(1)
                self.assertIsNone(client.ask_json("test", {}, 900))
                self.assertEqual((client.calls_made, client.successes), (1, 0))
                self.assertEqual(client.last_status, f"http_{code}")
                self.assertEqual(self.urlopen.call_count, 1)
                self.assertNotIn(secret, " ".join(logs))

    def test_network_failure_returns_none_without_body_or_exception_logging(self):
        secret = "private-reply-or-request-body"
        logs = []
        self.urlopen.side_effect = urllib.error.URLError(secret)
        client = kimi.LLMClient(log=logs.append)
        self.assertIsNone(client.ask_json("test", {"private": secret}, 900))
        self.assertEqual(client.last_status, "network_error")
        self.assertEqual(self.urlopen.call_count, 1)
        self.assertNotIn(secret, " ".join(logs))

    def test_entire_slow_body_is_deadline_bounded_and_same_night_stops(self):
        release = threading.Event()
        finished = threading.Event()
        class SlowBody(FakeResponse):
            def read(self, limit):
                release.wait(2)
                return super().read(limit)
            def __exit__(self, *_args):
                finished.set()
        self.urlopen.return_value = SlowBody()
        client = kimi.LLMClient(call_timeout_seconds=0.05)
        started = time.monotonic()
        try:
            self.assertIsNone(client.ask_json("test", {}, 900))
            elapsed = time.monotonic() - started
            self.assertLess(elapsed, 0.4)
            self.assertGreaterEqual(client.seconds_spent, 0.04)
            self.assertEqual(client.last_status, "timeout")
            self.assertIsNone(client.ask_json("test", {}, 900))
            self.assertEqual(self.urlopen.call_count, 1)
        finally:
            release.set()
            self.assertTrue(finished.wait(1))
            client._worker.join(1)

    def test_timeout_retries_next_night_but_not_same_night_or_same_night_reset(self):
        self.urlopen.side_effect = [TimeoutError(), FakeResponse()]
        client = kimi.LLMClient()
        client.begin_night("night-1")
        self.assertIsNone(client.ask_json("test", {}, 900, stage="weather_interpretation"))
        self.assertEqual(client.last_status, "timeout")
        spent = client.seconds_spent
        client.begin_night("night-1")
        self.assertIsNone(client.ask_json("test", {}, 900, stage="weather_interpretation"))
        self.assertEqual(client.last_status, "night_cooldown")
        self.assertEqual(client.calls_made, 1)
        client.begin_night("night-2")
        self.assertEqual(client.ask_json("test", {}, 890, stage="weather_interpretation"), {"answer": 42})
        self.assertEqual((client.calls_made, client.successes), (2, 1))
        self.assertGreaterEqual(client.seconds_spent, spent)

    def test_failed_stage_does_not_disable_other_stage_after_worker_exits(self):
        self.urlopen.side_effect = [TimeoutError(), FakeResponse()]
        client = kimi.LLMClient()
        client.begin_night(0)
        self.assertIsNone(client.ask_json("test", {}, 900, stage="weather_interpretation"))
        self.assertEqual(client.ask_json("test", {}, 890, stage="action_selection"), {"answer": 42})
        self.assertEqual(client.calls_made, 2)
        self.assertIsNone(client.ask_json("test", {}, 880, stage="weather_interpretation"))
        self.assertEqual(client.calls_made, 2)

    def test_hanging_worker_never_overlaps_and_late_result_is_discarded(self):
        release = threading.Event()
        finished = threading.Event()

        class SlowBody(FakeResponse):
            def read(self, limit):
                release.wait(2)
                return super().read(limit)
            def __exit__(self, *_args):
                finished.set()

        self.urlopen.side_effect = [SlowBody(envelope('{"answer":"late"}')),
                                    FakeResponse(envelope('{"answer":"fresh"}'))]
        client = kimi.LLMClient(call_timeout_seconds=0.03)
        client.begin_night(0)
        try:
            self.assertIsNone(client.ask_json("test", {}, 900, stage="weather_interpretation"))
            old_worker = client._worker
            self.assertTrue(old_worker.is_alive())
            client.begin_night(1)
            for stage in ("weather_interpretation", "action_selection", "fault_diagnosis"):
                self.assertIsNone(client.ask_json("test", {}, 890, stage=stage))
                self.assertEqual(client.last_status, "request_in_flight")
            self.assertEqual(self.urlopen.call_count, 1)
            release.set()
            self.assertTrue(finished.wait(1))
            old_worker.join(1)
            self.assertFalse(old_worker.is_alive())
            self.assertEqual(client.successes, 0)
            self.assertIsNone(client.ask_json("test", {}, 880, stage="weather_interpretation"))
            self.assertEqual(client.last_status, "night_cooldown")
            self.assertEqual(self.urlopen.call_count, 1)
            client.begin_night(2)
            self.assertEqual(client.ask_json("test", {}, 870, stage="weather_interpretation"), {"answer": "fresh"})
            self.assertEqual((client.calls_made, client.successes), (2, 1))
        finally:
            release.set()
            if client._worker is not None:
                client._worker.join(1)

    def test_next_night_does_not_reset_call_total_wait_or_reserve_budgets(self):
        self.urlopen.side_effect = [TimeoutError()]
        exhausted_calls = kimi.LLMClient(max_calls=1)
        exhausted_calls.begin_night(0)
        self.assertIsNone(exhausted_calls.ask_json("test", {}, 900, stage="weather"))
        exhausted_calls.begin_night(1)
        self.assertIsNone(exhausted_calls.ask_json("test", {}, 900, stage="weather"))
        self.assertEqual(exhausted_calls.last_status, "call_limit")
        self.assertFalse(exhausted_calls.retry_available)
        exhausted_time = kimi.LLMClient()
        exhausted_time.seconds_spent = 120.0
        exhausted_time.begin_night(1)
        self.assertIsNone(exhausted_time.ask_json("test", {}, 900))
        self.assertEqual(exhausted_time.last_status, "time_budget")
        reserve = kimi.LLMClient()
        reserve.begin_night(1)
        self.assertIsNone(reserve.ask_json("test", {}, 90))
        self.assertEqual(reserve.last_status, "time_budget")
        self.assertEqual(self.urlopen.call_count, 1)

    def test_late_auth_or_parameter_error_remains_a_hard_stop(self):
        for code in (400, 401, 403):
            with self.subTest(code=code):
                release = threading.Event()
                self.urlopen.reset_mock()

                def delayed_failure(*args, **kwargs):
                    release.wait(2)
                    raise urllib.error.HTTPError("https://unit.test", code, "failed", {}, None)

                self.urlopen.side_effect = delayed_failure
                client = kimi.LLMClient(call_timeout_seconds=0.02)
                client.begin_night(0)
                try:
                    self.assertIsNone(client.ask_json("test", {}, 900, stage="weather"))
                    self.assertEqual(client.last_status, "timeout")
                    release.set()
                    client._worker.join(1)
                    self.assertFalse(client._worker.is_alive())
                    client.begin_night(1)
                    self.assertIsNone(client.ask_json("test", {}, 890, stage="weather"))
                    self.assertEqual(client.last_status, f"http_{code}")
                    self.assertFalse(client.retry_available)
                    self.assertEqual((client.calls_made, client.successes), (1, 0))
                    self.assertEqual(self.urlopen.call_count, 1)
                finally:
                    release.set()
                    if client._worker is not None:
                        client._worker.join(1)

    def test_queued_auth_error_cannot_be_erased_by_expired_deadline(self):
        self.urlopen.side_effect = urllib.error.HTTPError(
            "https://unit.test/v1/chat/completions", 401, "unauthorized", {}, None)
        client = kimi.LLMClient(call_timeout_seconds=0.1)
        client.begin_night(0)
        with mock.patch.object(kimi.time, "monotonic", side_effect=[100.0, 100.0, 100.0, 100.2, 100.2]):
            self.assertIsNone(client.ask_json("test", {}, 900, stage="weather_interpretation"))
        self.assertEqual(client.last_status, "http_401")
        client.begin_night(1)
        self.assertIsNone(client.ask_json("test", {}, 900, stage="weather_interpretation"))
        self.assertEqual(client.calls_made, 1)
        self.assertFalse(client.retry_available)

    def test_invalid_or_large_payload_never_reaches_network(self):
        client = kimi.LLMClient()
        self.assertIsNone(client.ask_json("test", {"x": float("nan")}, 900))
        self.assertIsNone(client.ask_json("test", {"x": object()}, 900))
        self.assertIsNone(client.ask_json("test", {"x": "a" * kimi.MAX_REQUEST_BYTES}, 900))
        self.assertIsNone(client.ask_json("test", {}, float("inf")))
        self.assertEqual(client.calls_made, 0)
        self.urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
