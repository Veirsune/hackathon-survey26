"""Offline branch: no model transport, credentials, or network dependencies."""

class LLMClient:
    """Keep the shared planner interface with an unconditionally disabled client."""
    enabled = configured = retry_available = False
    calls_made = successes = max_calls = 0
    seconds_spent = spent_seconds = 0.0
    last_status = "disabled_by_no_llm_branch"
    model = base_url = "disabled"

    def __init__(self, *args, **kwargs):
        pass

    def begin_night(self, night_id):
        pass

    def ask_json(self, *args, **kwargs):
        return None
