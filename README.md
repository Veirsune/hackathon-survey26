# Survey Observer

A rules-based scheduling agent using the competition JSONL protocol. Run `python agent.py`; dependencies are in `requirements.txt`.

This experimental branch adapts search effort to both normalized CPU remaining and an explicitly supplied wall-clock deadline. Missing wall-clock information falls back to CPU scheduling. It preserves the baseline observing objective, exposure model, and diagnostic policy. Model calls are disabled.
