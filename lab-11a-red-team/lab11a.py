"""Lab 11a runner -- given, do not edit. The grader uses its own copy.

  python3 lab11a.py attack <level>   run attacks.json[<level>] 3 times against
                                     that level; writes traces/level<level>.jsonl
                                     and keeps a copy of every attempt in
                                     traces/history/
  python3 lab11a.py status           one line per level from your saved traces
"""
import fcntl
import json
import os
import sys
import shutil
import tempfile
import time
from pathlib import Path

import ladder

ROOT = Path(__file__).resolve().parent

# Each command is a new process, so pacing has to be shared through a file:
# the gateway allows 30 calls a minute per key, and this keeps a margin for
# aider using the same key.
CALLS_PER_MINUTE = 25
CALL_LOG = Path(tempfile.gettempdir()) / "lab11a-model-calls.json"


def _wait_for_shared_slot():
    while True:
        with open(CALL_LOG, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            try:
                starts = json.loads(f.read() or "[]")
            except ValueError:
                starts = []
            now = time.time()
            starts = [t for t in starts if now - t < 60]
            if len(starts) < CALLS_PER_MINUTE:
                starts.append(now)
                f.seek(0)
                f.truncate()
                f.write(json.dumps(starts))
                return
            pause = 60 - (now - starts[0]) + 0.1
        time.sleep(pause)


class _PacedCompletions:
    def __init__(self, inner):
        self.inner = inner

    def create(self, **kwargs):
        for attempt in range(6):
            _wait_for_shared_slot()
            try:
                return self.inner.chat.completions.create(**kwargs)
            except Exception as e:
                rate_limited = getattr(e, "status_code", None) == 429 or type(e).__name__ == "RateLimitError"
                if not rate_limited or attempt == 5:
                    raise
                print("  (gateway rate limit hit -- waiting 20s and retrying)")
                time.sleep(20)


class PacedClient:
    def __init__(self, inner):
        self.chat = type("Chat", (), {})()
        self.chat.completions = _PacedCompletions(inner)


def make_client():
    from openai import OpenAI
    return PacedClient(OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"],
                              timeout=120))


def load_attack(path, level):
    path = Path(path)
    if not path.exists():
        sys.exit(f"no attacks.json at {path}")
    try:
        attacks = json.loads(path.read_text())
    except ValueError as e:
        sys.exit(f"attacks.json is not valid JSON: {e}")
    if not isinstance(attacks, dict) or str(level) not in attacks:
        sys.exit(f'attacks.json has no entry for level {level} (expected a key "{level}")')
    text = attacks[str(level)]
    if not isinstance(text, str):
        sys.exit(f"the level {level} attack must be text (a JSON string)")
    if not text.strip():
        sys.exit(f"the level {level} attack is empty -- write it in attacks.json first")
    if len(text) > ladder.MAX_ATTACK_CHARS:
        sys.exit(f"the level {level} attack is {len(text)} characters; the limit is {ladder.MAX_ATTACK_CHARS}")
    return text


def trace_path(level):
    return ROOT / "traces" / f"level{level}.jsonl"


def cmd_attack(level):
    text = load_attack(ROOT / "attacks.json", level)
    print(f"Level {level}: running your attack {ladder.RUNS} times...")
    result = ladder.attack(make_client(), level, text)
    trace_path(level).parent.mkdir(exist_ok=True)
    with open(trace_path(level), "w") as f:
        for i, run in enumerate(result["runs"], 1):
            for event in run.get("events", []):
                f.write(json.dumps({"run": i, **event}) + "\n")
            if run["verdict"] == "error":
                f.write(json.dumps({"run": i, "type": "error", "error": run["error"]}) + "\n")
        f.write(json.dumps({"summary": True, "level": level, "attack": text, "successes": result["successes"],
                            "beaten": result["beaten"], "verdicts": [r["verdict"] for r in result["runs"]]}) + "\n")
    stamp, n = time.strftime("%Y%m%d-%H%M%S"), 1
    while (kept := ROOT / "traces" / "history" / f"level{level}-{stamp}-{n}.jsonl").exists():
        n += 1  # two attempts in the same second
    kept.parent.mkdir(exist_ok=True)
    shutil.copyfile(trace_path(level), kept)
    for i, run in enumerate(result["runs"], 1):
        detail = f" ({run['error']})" if run["verdict"] == "error" else ""
        print(f"  run {i}: {run['verdict']}{detail}")
    print(f"Level {level}: {'BEATEN' if result['beaten'] else 'HELD'} "
          f"({result['successes']} of {ladder.RUNS} runs succeeded; 2 needed). Trace: traces/level{level}.jsonl"
          f" (also kept as traces/history/{kept.name})")
    if any(r["verdict"] == "error" for r in result["runs"]):
        print("  A run failed on a gateway error, which counts neither way -- rerun this command.")


def cmd_status():
    for level in sorted(ladder.POINTS):
        p = trace_path(level)
        if not p.exists():
            print(f"level {level}: not tried")
            continue
        last = json.loads(p.read_text().splitlines()[-1])
        print(f"level {level}: {'BEATEN' if last['beaten'] else 'HELD'} ({last['successes']} of {ladder.RUNS})")


def main(argv):
    if argv[:1] == ["attack"] and len(argv) == 2 and argv[1].isdigit() and int(argv[1]) in ladder.POINTS:
        cmd_attack(int(argv[1]))
    elif argv == ["status"]:
        cmd_status()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
