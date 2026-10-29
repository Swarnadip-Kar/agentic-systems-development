# LAB 7a - 08-09-2026

### Initial Actions and Prompts

```
Implement 
agent_step(state, client, registry, tools, granted_permissions) -- exactly one perceive-think-act-observe cycle, and nothing else. state is {"messages": [...]}. Call client.chat.completions.create(model="main", messages=state["messages"], tools=tools, tool_choice="auto"). If response.choices[0].finish_reason != "tool_calls", return (state, True, message.content) -- the final answer. Otherwise: append the assistant turn to a new messages list (content plus "tool_calls": [tc.model_dump() for tc in message.tool_calls]), dispatch every tool call in message.tool_calls via dispatch_native_tool_call, append one {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)} per call, and return ({"messages": new_messages}, False, step_output) where step_output is a list of {"tool": name, "result": result} per call. No max_steps, no timing, no try/except anywhere in here -- if a tool raises, let it propagate. That is deliberate.
```

```
Next Implement
RuntimeHarness.run(agent_step_fn, state) -- the harness. The constructor and _log(entry) (appends one JSON line to self.trace_path) are given. agent_step_fn takes just state and returns (new_state, done, output) -- the caller wraps Exercise 1 in a lambda to bind the other arguments. Implement, in this order, for step in 1..max_steps:
Compute elapsed = time.monotonic() - start. If elapsed > self.timeout_seconds, log {"step": step, "elapsed_s": elapsed, "status": "timeout"} and return {"status": "timeout", "steps_taken": step - 1, "elapsed_s": elapsed}. This check runs between steps -- it will not catch a step that hangs mid-call (that is Lab 7b's problem; here, know that it's a limitation, don't try to solve it).
Call agent_step_fn(state) inside a single try/except Exception as e. On exception: log {"step": step, "elapsed_s": ..., "status": "error", "error": f"{type(e).__name__}: {e}"} and return {"status": "error", "steps_taken": step, "error": <same string>}.
On success: log {"step": step, "elapsed_s": ..., "status": "ok", "output": output}. If done, return {"status": "done", "steps_taken": step, "output": output}.
After the loop: return {"status": "exhausted", "steps_taken": self.max_steps} (no trace entry for this case). Round elapsed_s to 2 decimals in trace entries.
```

```
Next Implement these functions
read_trace(trace_path) -- read the JSONL file back into a list of dicts, one per non-blank line, in order.
trace_summary(entries) -- return {"total": <len>, "by_status": {<status>: <count>, ...}, "avg_elapsed_s": <mean of "elapsed_s" over all entries, 0.0 if empty>, "last_status": <entries[-1]["status"], or None if empty>}.
run_scenarios(client, registry, granted_permissions, trace_dir=".") -- for each scenario in SCENARIOS (given): pick the registry (registry_with_broken_tool(registry, break_tool) if break_tool is set, else registry as-is), build tools with build_native_tools, create a RuntimeHarness(max_steps=scenario["max_steps"], trace_path=f"{trace_dir}/harness_trace_{name}.jsonl"), truncate that trace file first (open(path, "w").close()), run it with state = {"messages": [{"role": "user", "content": task}]}, then print one line name: status=<...> steps_taken=<...> followed by the trace_summary of that scenario's trace. Return a list of {"name": name, "result": result, "summary": summary} in scenario order.
```

### Logging, Debugging and Testing 

After these steps I ran 
python scaffold.py


This the output 
```
student@1b4fa25d6d9d:~/lab-07a-runtime-harness$ python scaffold.py
normal: status=done steps_taken=2
broken_tool: status=error steps_taken=1
exhausted: status=exhausted steps_taken=1
```

Also three files

##### `harness_trace_normal.json`
```json
{"step": 1, "elapsed_s": 0.0, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 6}}]}
{"step": 2, "elapsed_s": 4.52, "status": "ok", "output": "The status of ticket 1 is unresolved and it has been open for 6 days. How would you like to proceed with this ticket?"}
```

##### `harness_trace_broken_tool`
```json
{"step": 1, "elapsed_s": 0.0, "status": "error", "error": "RuntimeError: escalate_ticket service is down"}
```

##### `harness_trace_exhausted`
```json
{"step": 1, "elapsed_s": 0.0, "status": "ok", "output": [{"tool": "search_tickets", "result": [1, 3, 4, 6]}]}
```

Tne output looked fine.

I tired to add summary too.

### Final Output

```json
student@1b4fa25d6d9d:~/lab-07a-runtime-harness$ python scaffold.py
normal: status=done steps_taken=2
{'total': 2, 'by_status': {'ok': 2}, 'avg_elapsed_s': 2.21, 'last_status': 'ok'}
broken_tool: status=error steps_taken=1
{'total': 1, 'by_status': {'error': 1}, 'avg_elapsed_s': 0.0, 'last_status': 'error'}
exhausted: status=exhausted steps_taken=1
{'total': 1, 'by_status': {'ok': 1}, 'avg_elapsed_s': 0.0, 'last_status': 'ok'}
```

All Good.