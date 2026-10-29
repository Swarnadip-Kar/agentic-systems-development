"""Lab 10 runner -- given, not your work. Runs your own Lab 9a harness
against one of the two broken scaffold files, and writes the files this
lab asks you to commit.

  python3 lab10.py run <scaffold_file> <case_id> <trace_out.jsonl>
  python3 lab10.py diagnose <trace.jsonl> <diagnosis_out.json>
  python3 lab10.py sweep <scaffold_file> <rows_out.json>
"""
import fcntl
import importlib.util
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATTERN = "plan-execute"
SHAPE = ["get_ticket_history", "escalate_ticket"]

# Each lab10.py command is a new process, so the scaffold's own pacer starts
# empty every time; back-to-back commands could exceed the gateway's 30 calls
# a minute. This pacer is shared by every command in the workspace, and keeps
# a margin for aider using the same key.
CALLS_PER_MINUTE = 25
CALL_LOG = Path(tempfile.gettempdir()) / "lab10-model-calls.json"


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


class _PacedChat:
    def __init__(self, inner):
        self.completions = _PacedCompletions(inner)


class PacedClient:
    """Wraps the scaffold's client; your CountingClient wraps this in turn."""

    def __init__(self, inner):
        self.inner = inner
        self.chat = _PacedChat(inner)

    def __getattr__(self, name):
        return getattr(self.inner, name)


def client_for(scaffold):
    return PacedClient(scaffold.get_client())


def load_module(path, name):
    path = Path(path).resolve()
    if not path.exists():
        sys.exit(f"no such file: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_trace(trace_path):
    with open(trace_path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_cases(scaffold):
    """Your own load_test_set; if it fails or drops cases, test_set.json as is,
    so this lab is never blocked by last week's loader."""
    path = HERE / "test_set.json"
    raw = json.loads(path.read_text())
    try:
        cases = scaffold.load_test_set(str(path))
    except Exception as e:
        cases, why = None, f"raised {e!r}"
    else:
        why = "did not return all eight cases"
    if not cases or {c.get("id") for c in cases} != {c["id"] for c in raw}:
        print(f"note: your load_test_set {why}; using test_set.json directly")
        cases = [dict(c, expected_escalations=sorted(c["expected_escalations"])) for c in raw]
    return cases


def cmd_run(scaffold_file, case_id, trace_out):
    scaffold = load_module(scaffold_file, "scaffold_under_test")
    cases = [c for c in load_cases(scaffold) if c["id"] == case_id]
    if not cases:
        sys.exit(f"no case with id {case_id!r} in test_set.json")
    error = None
    with tempfile.TemporaryDirectory() as tmp:
        try:
            rows = scaffold.run_test_set(client_for(scaffold), cases, patterns=(PATTERN,),
                                         runs=1, trace_dir=tmp)
        except Exception as e:  # keep the trace: it is the evidence of what happened
            error, rows = e, []
        trace = Path(tmp) / f"trace_{case_id}_{PATTERN}_1.jsonl"
        if not trace.exists():  # your run_test_set may name its trace files differently
            found = sorted(Path(tmp).glob("*.jsonl"))
            plan = [p for p in found if PATTERN in p.name]
            found = plan or found
            if len(found) != 1:
                if error:
                    raise error
                sys.exit(f"expected one trace file from run_test_set, found {[p.name for p in found]}")
            trace = found[0]
        shutil.copyfile(trace, trace_out)
    if error is not None:
        print(f"{case_id}: your harness raised {error!r} during the run")
        print(f"trace up to that point written to {trace_out} -- read it")
        sys.exit(1)
    row = next(r for r in rows if r["pattern"] == PATTERN)
    print(f"{case_id}: {'PASS' if row['passed'] else 'FAIL'} -- {row['detail']}")
    print(f"trace written to {trace_out}")


def cmd_diagnose(trace_file, diagnosis_out):
    diagnose = load_module(HERE / "diagnose.py", "diagnose")
    result = diagnose.diagnose_divergence(read_trace(trace_file), SHAPE)
    Path(diagnosis_out).write_text(json.dumps(
        {"trace": Path(trace_file).name, "expected_shape": SHAPE, "result": result},
        indent=2) + "\n")
    print(json.dumps(result))
    print(f"diagnosis written to {diagnosis_out}")


def cmd_sweep(scaffold_file, rows_out):
    scaffold = load_module(scaffold_file, "scaffold_under_test")
    cases = load_cases(scaffold)
    with tempfile.TemporaryDirectory() as tmp:
        rows = scaffold.run_test_set(client_for(scaffold), cases, patterns=(PATTERN,),
                                     runs=1, trace_dir=tmp)
    rows = [r for r in rows if r["pattern"] == PATTERN]
    Path(rows_out).write_text(json.dumps(
        {"scaffold": Path(scaffold_file).name, "rows": rows}, indent=2) + "\n")
    scaffold.compare_report(rows, cases)
    print(f"rows written to {rows_out}")


COMMANDS = {"run": (cmd_run, 3), "diagnose": (cmd_diagnose, 2), "sweep": (cmd_sweep, 2)}


def main(argv):
    if len(argv) < 1 or argv[0] not in COMMANDS or len(argv) - 1 != COMMANDS[argv[0]][1]:
        sys.exit(__doc__)
    fn, _ = COMMANDS[argv[0]]
    fn(*argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
