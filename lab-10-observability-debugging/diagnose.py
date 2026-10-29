"""Lab 10, Exercise 1: find where a run left the path it should have taken.

A trace is the list `read_trace` returns: one entry per harness step, for
example

    {"step": 2, "elapsed_s": 3.1, "status": "ok", "output": [...]}

When `output` is a list, its items are the tool calls made in that step,
in order:

    {"tool": "get_ticket_history", "arguments": {"ticket_id": 23},
     "result": {"ticket_id": 23, "history": [...]}}

Some items have no "tool" key (for example {"not_run": ..., "why": ...});
skip them. Entries whose `output` is not a list (a string, or no output at
all) contain no tool calls.
"""


def diagnose_divergence(trace, expected_shape):
    """Compare the tool calls in `trace` with `expected_shape`, an ordered
    list of tool names the run should have made.

    A call counts only if its "result" is a dict with no "error" key.
    Walk `expected_shape` in order, matching each name against the counted
    calls in the order they happened (other calls may come in between).
    Each expected name matches the EARLIEST counted call with that name
    that comes after the previous match; repeats of a tool later in the
    trace do not move the match.

    Return:
      {"match": True,  "missing": None, "after_step": s}  if every expected
          tool was found, where s is the step of the call matched to the
          last expected name;
      {"match": False, "missing": name, "after_step": s}  otherwise, where
          name is the first expected tool that was never found, and s is
          the step of the call matched to the expected name before it, or
          None if the very first expected name was never found.
    """
    expected_index = 0
    last_matched_step = None

    for entry in trace:
        if isinstance(entry.get("output"), list):
            for call in entry["output"]:
                if "tool" in call and isinstance(call.get("result"), dict) and "error" not in call["result"]:
                    if expected_index < len(expected_shape) and call["tool"] == expected_shape[expected_index]:
                        last_matched_step = entry["step"]
                        expected_index += 1

        if expected_index == len(expected_shape):
            return {"match": True, "missing": None, "after_step": last_matched_step}

    if expected_index == 0:
        return {"match": False, "missing": expected_shape[expected_index], "after_step": None}
    else:
        return {"match": False, "missing": expected_shape[expected_index], "after_step": last_matched_step}
