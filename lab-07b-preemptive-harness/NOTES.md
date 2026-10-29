# LAB 7b -10-09-2026

### Initial Actions and Prompts

```
Implement 
agent_step_with_timeout(state, client, registry, tools, granted_permissions, model_call_timeout=DEFAULT_MODEL_CALL_TIMEOUT) -- Fix 1. Identical to the given agent_step except the model call passes timeout=model_call_timeout to client.chat.completions.create(...). That's the whole fix: the SDK enforces the deadline at the HTTP level and raises openai.APITimeoutError on its own.
```

```
Next Implement
PreemptiveRuntimeHarness.run(agent_step_fn, state) -- Fix 2. Same constructor, _log, result shapes, and trace entries as harness (inherited). The difference is where the bound is: run each step in a worker thread and wait on it with a deadline. For step in 1..max_steps:

remaining = self.timeout_seconds - (time.monotonic() - start). If remaining <= 0: log {"step", "elapsed_s", "status": "timeout"} and return {"status": "timeout", "steps_taken": step - 1}.
future = pool.submit(agent_step_fn, state) then state, done, output = future.result(timeout=remaining).
On concurrent.futures.TimeoutError: log {"step", "elapsed_s", "status": "step_hung"} and return {"status": "timeout", "steps_taken": step - 1, "elapsed_s": ..., "note": "step exceeded the deadline and was abandoned, not killed"}.

Any other exception, success, and exhaustion: exactly as `old_scaffold.py`

Do not write with ThreadPoolExecutor(...) as pool:. Leaving a with block calls shutdown(wait=True), which blocks until every submitted task finishes -- including the hung one -- so your return will not actually complete until the hang does, and the timeout is silently defeated. Create the pool as a plain object and never shut it down from inside run. The oracle test for this exercise hands your harness a step that sleeps for 3 seconds under a 1-second timeout and checks that run() returns in about 1 second; a with-based implementation fails it.
```

```
Next Implement
run_and_exit(harness, agent_step_fn, state) -- the consequence of "abandoned, not killed." A thread the harness gave up on is still running, and Python's normal interpreter shutdown waits for every ThreadPoolExecutor thread before it will exit -- so a script that just falls off the end sits there for the rest of the hang. This function runs harness.run(agent_step_fn, state), prints json.dumps(result), then ends the process immediately with os._exit(0). But os._exit skips the interpreter's normal cleanup, which is also what flushes stdout -- so call sys.stdout.flush() right before it, or your printed result silently never appears. This function never returns. The oracle test runs it in a subprocess with a step that sleeps 30 seconds under a 1-second timeout and requires the process to exit within a few seconds with the result on stdout -- forgetting either half fails it, just at a different line.
```

```
Implement
dispatch_with_timeout(tool_call, registry, granted_permissions, tool_timeout=DEFAULT_TOOL_TIMEOUT) and agent_step_with_tool_timeout(state, client, registry, tools, granted_permissions, tool_timeout=DEFAULT_TOOL_TIMEOUT) . Earlier fix saves the deadline but loses the run: the harness returns timeout and the user gets no answer. The bound was too coarse. Move it inside the step, around the one thing that hangs. dispatch_with_timeout submits dispatch_native_tool_call(tool_call, registry, granted_permissions) to a worker thread (same plain-pool rule as PreemptiveRuntimeHarness.run(agent_step_fn, state)) and waits future.result(timeout=tool_timeout). On success return the result unchanged -- permission, JSON, and schema errors still come back exactly as dispatch_native_tool_call produces them. On concurrent.futures.TimeoutError return {"error": f"tool '{name}' timed out after {tool_timeout}s"} -- an ordinary tool result, the same shape as the dispatcher's other errors. agent_step_with_tool_timeout is the given agent_step with that one substitution, so the timeout error lands in a tool message and the model sees it on the next turn and can answer around it.
```

```
Next Implement
compare_harnesses(client, registry, granted_permissions, scenarios=COMPARE_SCENARIOS, trace_dir=".") -- measure the difference. For each scenario: pick the registry (registry_with_hanging_tool(registry, hang_tool, hang_seconds) if hang_tool is set, else registry as-is), build tools, and run the same task through three configurations:

cooperative: RuntimeHarness driving the given agent_step;
preemptive: PreemptiveRuntimeHarness driving the given agent_step;
tool_bounded: RuntimeHarness driving agent_step_with_tool_timeout with the scenario's tool_timeout_seconds.
Each harness is constructed with the scenario's timeout_seconds (default max_steps) and a trace file f"{trace_dir}/harness_trace_{name}_{label}.jsonl" (truncate it first). Time each run() with time.monotonic() around the call. A configuration "respected its deadline" if its wall-clock elapsed is <= timeout_seconds + 1.0. Print, per scenario and per configuration, status, elapsed_s (2 decimals), and respected_deadline; then an aggregate line per configuration: respected deadline in N/M scenarios. Return a list of {"name", "cooperative": {"status", "elapsed_s", "respected_deadline"}, "preemptive": {...same keys...}, "tool_bounded": {...same keys...}} in scenario order.
```

### Logging, Debugging and Testing 

After these steps I ran 
python scaffold.py


This the output 
```
student@1b4fa25d6d9d:~/lab-07b-preemptive-harness$ python scaffold.py 
Scenario: normal
  Cooperative: status=error, elapsed_s=0.02, respected_deadline=True
  Preemptive: status=error, elapsed_s=0.02, respected_deadline=True
  Tool Bounded: status=done, elapsed_s=3.31, respected_deadline=True
Scenario: hanging_tool
  Cooperative: status=error, elapsed_s=0.01, respected_deadline=True
  Preemptive: status=error, elapsed_s=0.01, respected_deadline=True
  Tool Bounded: status=done, elapsed_s=6.96, respected_deadline=True

Aggregate Results:
  Cooperative: respected deadline in 2/2 scenarios
  Preemptive: respected deadline in 2/2 scenarios
  Tool Bounded: respected deadline in 2/2 scenarios
```

Also 6 files

##### `harness_trace_normal_cooperative.jsonl`
```json
{"step": 1, "elapsed_s": 0.0, "status": "error", "error": "TypeError: agent_step_with_timeout() missing 4 required positional arguments: 'client', 'registry', 'tools', and 'granted_permissions'"}

```
##### `harness_trace_normal_preemptive.jsonl`
```json
{"step": 1, "elapsed_s": 0.0, "status": "error", "error": "TypeError: agent_step_with_timeout() missing 4 required positional arguments: 'client', 'registry', 'tools', and 'granted_permissions'"}

```
##### `harness_trace_normal_tool_bounded.jsonl`
```json
{"step": 1, "elapsed_s": 2.29, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 6}}]}
{"step": 2, "elapsed_s": 3.29, "status": "ok", "output": "The status of ticket 1 is unresolved and it has been open for 6 days."}

```
##### `harness_trace_hanging_cooperative.jsonl`
```json
{"step": 1, "elapsed_s": 0.0, "status": "error", "error": "TypeError: agent_step_with_timeout() missing 4 required positional arguments: 'client', 'registry', 'tools', and 'granted_permissions'"}
```
##### `harness_trace_hanging_preemptive.jsonl`
```json
{"step": 1, "elapsed_s": 0.0, "status": "error", "error": "TypeError: agent_step_with_timeout() missing 4 required positional arguments: 'client', 'registry', 'tools', and 'granted_permissions'"}

```
##### `harness_trace_hanging_tool_tool_bounded.jsonl`
```json
{"step": 1, "elapsed_s": 2.16, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"error": "tool 'check_ticket_status' timed out after 1s"}}]}
{"step": 2, "elapsed_s": 5.09, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"error": "tool 'check_ticket_status' timed out after 1s"}}]}
{"step": 3, "elapsed_s": 6.95, "status": "ok", "output": "I apologize for the inconvenience. It appears that there is currently an issue with accessing the ticket status. I recommend checking back later or contacting support directly if this persists. Is there anything else I can assist you with?"}
```



There were errors in the code
Fixed them by hand - easy fixes

```diff
diff --git a/scaffold.py b/scaffold.py
index 14a4f11..3b9f971 100644
--- a/scaffold.py
+++ b/scaffold.py
@@ -438,7 +438,7 @@ def compare_harnesses(client, registry, granted_permissions, scenarios=COMPARE_S
             pass  # Truncate the file
         cooperative_harness = RuntimeHarness(timeout_seconds=timeout_seconds, trace_path=cooperative_trace_path)

         start_time = time.monotonic()
-        cooperative_result = cooperative_harness.run(agent_step_with_timeout, state)
+        cooperative_result = cooperative_harness.run(lambda state: agent_step_with_timeout(state, clien
t, current_registry, tools, granted_permissions), state)
         cooperative_elapsed = round(time.monotonic() - start_time, 2)
         cooperative_respected = cooperative_elapsed <= timeout_seconds + 1.0
 
@@ -448,7 +448,7 @@ def compare_harnesses(client, registry, granted_permissions, scenarios=COMPARE_S
             pass  # Truncate the file
         preemptive_harness = PreemptiveRuntimeHarness(timeout_seconds=timeout_seconds, trace_path=preemptive_trac
e_path)
         start_time = time.monotonic()
-        preemptive_result = preemptive_harness.run(agent_step_with_timeout, state)
+        preemptive_result = preemptive_harness.run(lambda state: agent_step_with_timeout(state, client,
 current_registry, tools, granted_permissions), state)
         preemptive_elapsed = round(time.monotonic() - start_time, 2)
         preemptive_respected = preemptive_elapsed <= timeout_seconds + 1.0
```


Now the output was okay


### Final Output

```
student@1b4fa25d6d9d:~/lab-07b-preemptive-harness$ python scaffold.py 
Scenario: normal
  Cooperative: status=done, elapsed_s=17.56, respected_deadline=True
  Preemptive: status=done, elapsed_s=5.17, respected_deadline=True
  Tool Bounded: status=done, elapsed_s=3.54, respected_deadline=True
Scenario: hanging_tool
  Cooperative: status=timeout, elapsed_s=11.8, respected_deadline=False
  Preemptive: status=timeout, elapsed_s=8.05, respected_deadline=True
  Tool Bounded: status=done, elapsed_s=6.45, respected_deadline=True

Aggregate Results:
  Cooperative: respected deadline in 1/2 scenarios
  Preemptive: respected deadline in 2/2 scenarios
  Tool Bounded: respected deadline in 2/2 scenarios
```

Also 6 files

##### `harness_trace_normal_cooperative.jsonl`
```json
{"step": 1, "elapsed_s": 15.11, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 6}}]}
{"step": 2, "elapsed_s": 17.55, "status": "ok", "output": "The status of ticket 1 is unresolved and it has been open for 6 days."}
```

##### `harness_trace_normal_preemptive.jsonl`
```json
{"step": 1, "elapsed_s": 1.09, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 6}}]}
{"step": 2, "elapsed_s": 5.13, "status": "ok", "output": "The status of ticket 1 is unresolved and it is 6 days old. Would you like to escalate this ticket or take any other action?"}
```

##### `harness_trace_normal_tool_bounded.jsonl`
```json
{"step": 1, "elapsed_s": 2.56, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 6}}]}
{"step": 2, "elapsed_s": 3.51, "status": "ok", "output": "The status of ticket 1 is unresolved and it has been open for 6 days."}
```

##### `harness_trace_hanging_cooperative.jsonl`
```json
{"step": 1, "elapsed_s": 11.76, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"error": "tool 'check_ticket_status' timed out after 5s"}}]}
{"step": 2, "elapsed_s": 11.78, "status": "timeout"}
```

##### `harness_trace_hanging_preemptive.jsonl`
```json
{"step": 1, "elapsed_s": 8.0, "status": "step_hung"}
```

##### `harness_trace_hanging_tool_tool_bounded.jsonl`
```json
{"step": 1, "elapsed_s": 4.71, "status": "ok", "output": [{"tool": "check_ticket_status", "result": {"error": "tool 'check_ticket_status' timed out after 1s"}}]}
{"step": 2, "elapsed_s": 6.43, "status": "ok", "output": "I'm sorry, but it seems that the `check_ticket_status` tool is not available or has encountered an issue. Could you please provide more details so I can assist you better?"}
```


All Good.