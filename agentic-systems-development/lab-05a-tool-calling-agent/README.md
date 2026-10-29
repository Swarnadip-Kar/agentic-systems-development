# Lab 5a: A Two-Tool Agent Loop

Builds on Week 5's lecture (`week05-assistants-to-agents.pdf`) and the
same ticket-support domain as Weeks 3-4, extended with a status/age
lookup a single classification call could never answer on its own.
`aider` is available for this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

**This gateway's model does not have native `tools=`/`tool_choice`
function calling enabled.** Both tools are described in `TOOLS_DESC`
(already written for you) and the model's decision comes back as plain
JSON that you parse by hand -- exactly what Tuesday's lecture did live.

## Exercises

1. **`AgentDecision`** -- a Pydantic schema for the model's per-step
   decision. Fields: `action` (`Literal["call_tool", "final_answer"]`),
   `tool: Optional[str]`, `arguments: Optional[dict]`,
   `answer: Optional[str]`. Add a `model_validator` that enforces:
   `action == "call_tool"` requires both `tool` and `arguments` to be
   set; `action == "final_answer"` requires `answer` to be set. Raise
   `ValueError` from the validator on violation.
2. **`parse_agent_decision`** -- parse and validate one raw model
   response into an `AgentDecision`. Call `_strip_code_fence` first,
   then `json.loads`, then validate. Return `(decision, None)` on
   success, `(None, error_message)` on failure -- same two-outcome
   shape as Lab 4b's `validate_classification`, distinguishing "not
   valid JSON" from "valid JSON, wrong shape."
3. **`dispatch_tool_call(decision, tools)`** -- run the tool named by
   `decision.tool` (a dict: name -> callable) with
   `decision.arguments`. Never raise: an unknown tool name, or a
   bad-arguments call that raises `TypeError` internally, is real,
   reportable information -- catch it and return
   `{"error": "<message>"}` instead.
4. **`run_agent_loop(client, task, tools, max_steps=MAX_AGENT_STEPS)`**
   -- the bounded perceive-think-act-observe loop. Returns:
   ```python
   {
     "task": task,
     "steps": [{"tool": <name>, "result": <dict>}, ...],  # tool-call
                                                            # steps only
     "final_answer": <str> or None,  # None if max_steps exhausted
     "steps_taken": <int>,           # total model calls made
   }
   ```
   Each iteration: call the model with `TOOLS_DESC` as a system
   message plus the conversation so far; parse the decision with
   `parse_agent_decision`. If parsing fails, feed the specific error
   back to the model and retry -- same discipline as Lab 4b's
   deterministic wrapper, and it still counts toward `max_steps`. If
   the decision is `"final_answer"`, stop and return it. Otherwise,
   dispatch the tool call via `dispatch_tool_call`, append its result
   to the conversation as the next turn, and continue. If `max_steps`
   is exhausted without a final answer, return with
   `final_answer=None`.
5. **`escalate_ticket(ticket_id, reason)`** -- the second tool. Append
   `{"ticket_id": ticket_id, "reason": reason}` to `ESCALATIONS`, and
   return `{"escalated": True, "ticket_id": ticket_id}`.
6. **`run_agent_batch(client, tasks, tools, max_steps=MAX_AGENT_STEPS)`**
   -- run `run_agent_loop` over every task in `tasks`. Return the list
   of per-task result dicts, same shape as `run_agent_loop`'s return
   value, in task order.
7. **`agent_summary_report(results)`** -- print a summary over a list
   of `run_agent_loop`-shaped result dicts (from `run_agent_batch` or
   `AGENT_DEMO_RESULTS`): how many finished with a final answer vs.
   exhausted `max_steps` with none, how many included an
   `escalate_ticket` call (check each result's `"steps"` for
   `tool == "escalate_ticket"`), and the average `steps_taken` across
   all results. `main()` runs this over both the live batch
   (`AGENT_TASKS`) and the demo fixture (`AGENT_DEMO_RESULTS`, which
   guarantees the budget-exhausted branch actually gets exercised --
   see the comment above it in `scaffold.py`).

Run `python3 scaffold.py` to check your progress.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
