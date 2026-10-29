# docs/labs/lab-test-sunday-source/live_client.py
"""Shared, pre-paced model client for the Sunday lab test. Import
get_client() wherever a question asks you to make a live call -- it
already handles the gateway's 30-calls-per-minute limit so you don't
hit a silent retry delay.

Aider: ALLOWED for this file -- it is given to you finished; you are
not expected to write or modify it."""
import collections
import os
import threading
import time

import openai

RATE_LIMIT_RPM = 28  # every gateway key allows 30 calls a minute


class _Pacer:
    def __init__(self):
        self.starts = collections.deque()
        self.lock = threading.Lock()

    def wait_for_slot(self):
        while True:
            with self.lock:
                now = time.monotonic()
                while self.starts and now - self.starts[0] >= 60:
                    self.starts.popleft()
                if len(self.starts) < RATE_LIMIT_RPM:
                    self.starts.append(now)
                    return
                pause = 60 - (now - self.starts[0]) + 0.05
            time.sleep(pause)


_PACER = _Pacer()


class _CountingCompletions:
    def __init__(self, outer):
        self.outer = outer

    def create(self, **kwargs):
        self.outer.calls += 1
        for attempt in range(4):
            _PACER.wait_for_slot()
            try:
                return self.outer.inner.chat.completions.create(**kwargs)
            except openai.RateLimitError as e:
                if attempt == 3:
                    raise
                time.sleep(float(e.response.headers.get("retry-after", "10")))


class _CountingChat:
    def __init__(self, outer):
        self.completions = _CountingCompletions(outer)


class CountingClient:
    """Wraps a client. Counts model calls in .calls, and self-paces
    under the gateway's rate limit. Use one per run."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0
        self.chat = _CountingChat(self)


def get_client():
    # max_retries=0: the SDK would otherwise wait out a rate limit
    # silently inside what looks like one slow call. CountingClient
    # paces and retries itself instead.
    inner = openai.OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
        max_retries=0,
    )
    return CountingClient(inner)
