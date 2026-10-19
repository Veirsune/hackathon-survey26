"""Optional, bounded OpenAI-compatible JSON advice using explicit configuration.

OPENAI_API_KEY / BASE_URL / MODEL take priority over their KIMI_* equivalents.
There is no implicit endpoint or model: missing configuration keeps the
deterministic strategy running without network access. No client identity is
impersonated. Logs never include credentials, payloads, or exception messages.

urllib's timeout applies to socket operations, not a whole request. A daemon
worker plus a monotonic deadline bounds the caller's entire wait, including a
slow response body. A temporary failure suspends its stage for the current
observing night. A later night may retry, but only after the previous worker
has exited. Each call owns its response queue, so late results are discarded.
"""
from __future__ import annotations

import json
import math
import os
import queue
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

MAX_REQUEST_BYTES = 256 * 1024
MAX_RESPONSE_BYTES = 256 * 1024
WALLCLOCK_RESERVE_SECONDS = 90.0
HARD_STOP_STATUSES = {"http_400", "http_401", "http_403"}


def _configured(primary: str, fallback: str) -> str:
    return os.environ.get(primary, "").strip() or os.environ.get(fallback, "").strip()


def _number(value, default: float, maximum: float) -> float:
    try:
        number = float(value)
        if not math.isfinite(number):
            return default
        return max(0.0, min(maximum, number))
    except (ValueError, TypeError):
        return default


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _strict_json(text):
    def reject_constant(_value):
        raise ValueError("Non-finite JSON value")
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=reject_constant)


class LLMClient:
    def __init__(self, log=None, call_timeout_seconds=None,
                 total_budget_seconds=None, max_calls=None, budget_profile="standard"):
        if budget_profile not in ("standard", "engineering"):
            raise ValueError("Unknown model budget profile")
        total_cap, calls_cap = (240., 16) if budget_profile == "engineering" else (120., 8)
        self.log = log or (lambda _text: None)
        self._api_key = _configured("OPENAI_API_KEY", "KIMI_API_KEY")
        self.base_url = _configured("OPENAI_BASE_URL", "KIMI_BASE_URL").rstrip("/") or "unconfigured"
        self.model = _configured("OPENAI_MODEL", "KIMI_MODEL") or "unconfigured"
        self.enabled = os.environ.get("AGENT_LLM_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}
        try:
            url = urllib.parse.urlsplit(self.base_url)
            valid_url = bool(url.scheme in {"http", "https"} and url.netloc
                             and url.username is None and url.password is None
                             and not url.query and not url.fragment)
        except ValueError:
            valid_url = False
        self.configured = bool(self.enabled and self._api_key and valid_url and self.model != "unconfigured")
        self.call_timeout_seconds = _number(
            os.environ.get("AGENT_LLM_CALL_SECONDS", 30) if call_timeout_seconds is None else call_timeout_seconds, 30.0, 30.0)
        self.total_budget_seconds = _number(
            os.environ.get("AGENT_LLM_TOTAL_SECONDS", 120) if total_budget_seconds is None else total_budget_seconds, 120.0, total_cap)
        self.max_calls = int(_number(
            os.environ.get("AGENT_LLM_MAX_CALLS", 6) if max_calls is None else max_calls, 6, calls_cap))
        self.max_tokens = max(64, int(_number(os.environ.get("AGENT_LLM_MAX_TOKENS", os.environ.get("AGENT_LLM_OUTPUT_LIMIT", 2000)), 2000, 4096)))
        effort = os.environ.get("AGENT_LLM_REASONING_EFFORT", "").strip().lower()
        self.reasoning_effort = effort if effort in {"low", "medium", "high"} else None
        self.calls_made = 0
        self.successes = 0
        self.seconds_spent = 0.0
        self.last_status = "ready" if self.configured else "disabled" if not self.enabled else "missing_config"
        self._blocked = False
        self._call_lock = threading.Lock()
        self._worker = None
        self._worker_result = None
        self._night_id = None
        self._night_failed_stages = set()

    def begin_night(self, night_id) -> None:
        """Advance an explicit simulation-night identity; never reset budgets.

        The planner supplies its public calendar index. Wall-clock elapsed time
        is deliberately not used to decide whether another night has begun.
        """
        if night_id != self._night_id:
            self._night_id = night_id
            self._night_failed_stages.clear()

    @property
    def retry_available(self) -> bool:
        """Whether a later night can still attempt this configured client."""
        return bool(self.configured and not self._blocked
                    and self.calls_made < self.max_calls
                    and self.seconds_spent < self.total_budget_seconds
                    and self.call_timeout_seconds > 0
                    and self.last_status not in {"time_budget", "invalid_budget", "invalid_request",
                                                 "request_too_large"})

    @property
    def spent_seconds(self) -> float:
        """Compatibility alias for the original example's counter."""
        return self.seconds_spent

    def _status(self, value: str) -> None:
        self.last_status = value
        try:
            self.log(f"llm: status={value} calls={self.calls_made} elapsed={self.seconds_spent:.3f}s")
        except Exception:
            pass

    def _budget_left(self, wallclock_remaining: float) -> float:
        return max(0.0, min(self.call_timeout_seconds,
                            self.total_budget_seconds - self.seconds_spent,
                            wallclock_remaining - WALLCLOCK_RESERVE_SECONDS))

    def _request(self, request, timeout: float):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                return "response_too_large", None
            envelope = _strict_json(raw.decode("utf-8"))
            if not isinstance(envelope, dict):
                return "invalid_response", None
            choices = envelope.get("choices")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                return "invalid_response", None
            message = choices[0].get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                return "invalid_response", None
            result = _strict_json(message["content"])
            return ("ok", result) if isinstance(result, dict) else ("invalid_json", None)
        except urllib.error.HTTPError as exc:
            code = int(exc.code)
            try:
                exc.close()
            except Exception:
                pass
            return f"http_{code}", None
        except TimeoutError:
            return "timeout", None
        except urllib.error.URLError as exc:
            return ("timeout", None) if isinstance(exc.reason, TimeoutError) else ("network_error", None)
        except (ValueError, UnicodeError, TypeError, KeyError, IndexError):
            return "invalid_json", None
        except OSError:
            return "network_error", None
        except Exception:
            return "request_error", None

    def ask_json(self, system_prompt: str, user_payload: dict, wallclock_remaining_seconds: float,
                 *, stage: Optional[str] = None) -> Optional[dict]:
        """Return one strict JSON object or None, with no retries or stdout output.

        ``stage`` scopes the current night's temporary-failure cooldown; it is
        never sent or logged. The caller advances nights with ``begin_night``.
        """
        if not self.configured or self._blocked:
            return None
        if not self._call_lock.acquire(blocking=False):
            return None
        try:
            stage_key = stage or "default"
            if self._worker is not None:
                if self._worker.is_alive():
                    self._night_failed_stages.add(stage_key)
                    self._status("request_in_flight")
                    return None
                self._worker = None
                # Discard all late model content. A late authentication or
                # parameter error is still a transport-level hard stop, not
                # advice to adopt, and must prevent another network request.
                try:
                    retired_status, _retired_content = self._worker_result.get_nowait()
                except queue.Empty:
                    retired_status = None
                self._worker_result = None
                if retired_status in HARD_STOP_STATUSES:
                    self._blocked = True
                    self._status(retired_status)
                    return None
            if stage_key in self._night_failed_stages:
                self._status("night_cooldown")
                return None
            if self.calls_made >= self.max_calls:
                self._status("call_limit")
                return None
            try:
                wallclock_remaining = float(wallclock_remaining_seconds)
                if not math.isfinite(wallclock_remaining):
                    raise ValueError
            except (ValueError, TypeError):
                self._status("invalid_budget")
                return None
            timeout = self._budget_left(wallclock_remaining)
            if timeout <= 0.0:
                self._status("time_budget")
                return None
            if not isinstance(system_prompt, str) or not isinstance(user_payload, dict):
                self._status("invalid_request")
                return None
            try:
                request_body = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, allow_nan=False)},
                    ],
                    "max_tokens": self.max_tokens,
                }
                if self.reasoning_effort is not None:
                    request_body["reasoning_effort"] = self.reasoning_effort
                body = json.dumps(request_body, ensure_ascii=False, allow_nan=False,
                                  separators=(",", ":")).encode("utf-8")
                if len(body) > MAX_REQUEST_BYTES:
                    self._status("request_too_large")
                    return None
                endpoint = self.base_url if self.base_url.endswith("/chat/completions") else self.base_url + "/chat/completions"
                request = urllib.request.Request(
                    endpoint, data=body, method="POST",
                    headers={"Content-Type": "application/json", "Accept": "application/json",
                             "Authorization": "Bearer " + self._api_key},
                )
            except (ValueError, TypeError, UnicodeError):
                self._status("invalid_request")
                return None
            completed = queue.Queue(maxsize=1)
            def work():
                completed.put(self._request(request, timeout))
            started = time.monotonic()
            deadline = started + timeout
            self.calls_made += 1
            worker = threading.Thread(target=work, name="bounded-llm-request", daemon=True)
            self._worker = worker
            self._worker_result = completed
            try:
                worker.start()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise queue.Empty
                status, result = completed.get(timeout=remaining)
                # Do not release the single-worker guard while this worker is
                # still unwinding, even after its response has been queued.
                worker.join(timeout=max(0.0, deadline - time.monotonic()))
                if worker.is_alive() or time.monotonic() > deadline:
                    # A queued authentication/parameter error remains a hard
                    # stop even if the worker or caller crosses the deadline.
                    # Discard late advice, never discard known bad credentials.
                    if status not in HARD_STOP_STATUSES:
                        status = "timeout"
                    result = None
            except queue.Empty:
                status, result = "timeout", None
            except Exception:
                status, result = "request_error", None
            finally:
                self.seconds_spent += max(0.0, time.monotonic() - started)
            if status in HARD_STOP_STATUSES:
                self._blocked = True
            elif status != "ok":
                self._night_failed_stages.add(stage_key)
            if status == "ok":
                self.successes += 1
            self._status(status)
            return result
        finally:
            self._call_lock.release()
