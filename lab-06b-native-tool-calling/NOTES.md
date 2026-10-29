# LAB 6b - 06-09-2026

### Initial Actions and Prompts

copy "build_tools_desc" from Lab 6a

Then I gave these Prompts
```
Implement 
dispatch_native_tool_call(tool_call, registry, granted_permissions) -- tool_call is one entry from message.tool_calls (has .id, .function.name, .function.arguments -- the last one is a JSON string, not a dict, so parse it with json.loads first; if that fails, return {"error": "invalid arguments JSON: <message>"} without raising). Unknown tool name: {"error": "unknown tool: <name>"}. Known tool: check registry[name]["permission"] against granted_permissions first -- if not granted, return {"error": "permission denied: '<name>' requires '<permission>' permission"} without calling anything. Only then validate the parsed arguments with validate_arguments-- invalid arguments return {"error": "invalid arguments: <reason>"}. Only if everything passes, call the tool and return its result. Never raise, for any of these reasons.

Next Implement
run_native_loop(client, task, registry, granted_permissions, max_steps=MAX_AGENT_STEPS) -- the native version of run_agent_loop. Each turn: call client.chat.completions.create(model="main", messages=messages, tools=build_native_tools(registry), tool_choice="auto"). If response.choices[0].finish_reason != "tool_calls", that's the final answer -- return it. Otherwise, the response may contain more than one tool call in message.tool_calls -- dispatch every one of them, not just the first, appending one {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)} message per call (matching each call by its id), plus one {"tool": name, "result": result} entry per call to the returned "steps" list. "steps_taken" counts model calls (turns), not individual tool dispatches -- a turn with 3 parallel tool calls still only costs 1 step. 
Append the assistant's own turn to messages before the tool results.

Next Implement
compare_traces(client, tasks, registry, granted_permissions) -- for each task in tasks, run it through both run_agent_loop (hand-rolled, given) and run_native_loop implemented above, under the same granted_permissions. Print, per task, both approaches' steps_taken. Then print an aggregate: how many tasks took fewer steps natively, and how many native runs included at least one turn with more than one tool call (a capability the hand-rolled protocol doesn't have).
```


### Logging, Debugging and Testing 

After these steps I ran 
python scaffold.py

Errors
Some debugging

Prompt
```
1. System Message Content Issue:
In `run_native_loop`:
`messages` is initialized with `{"role": "system", "content": tools_desc}` where `tools_desc` is a list of tool dictionaries. System message content MUST be a string, not a list. Remove `tools_desc` from `messages` (native OpenAI tool calling receives tools via the `tools` parameter in `chat.completions.create`, so a system message explaining the tools is not required).

2. Assistant Message History Formatting Bug:
When appending assistant responses to `messages` after tool calls, OpenAI API requires appending the assistant message with its `tool_calls` field (e.g., `messages.append(response.choices[0].message)`). Adding a dummy text message like `{"role": "assistant", "content": "Tool results processed."}` breaks the conversation structure expected by litellm/OpenAI.

Please update `run_native_loop` in `scaffold.py` so that:
- `messages` is initialized without `tools_desc` as the content (e.g., `messages = [{"role": "user", "content": task}]` or a standard string system message).
- The assistant's `message` object from `response.choices[0].message` is appended to `messages` before appending `tool` messages.
- Remove the `"Tool results processed."` dummy assistant message.
```


#### Output

Initial Output looked fine
but rate limit hit
```
student@1b4fa25d6d9d:~/lab-06b-native-tool-calling$ python scaffold.py 
Task: Check the status of ticket 1.
Hand-rolled steps taken: 2
Native steps taken: 2
Task: Check ticket 4. If it is unresolved and older than 3 days, escalate it with a short reason.
Hand-rolled steps taken: 3
Native steps taken: 3
Task: Find all unresolved tickets and escalate any older than 3 days, with a short reason.
Hand-rolled steps taken: 10
Native steps taken: 3
Task: Which ticket has been open longer: ticket 2 or ticket 5? Answer with the ticket ID and its age in days.
Hand-rolled steps taken: 3
Native steps taken: 2
Traceback (most recent call last):
  File "/home/student/lab-06b-native-tool-calling/scaffold.py", line 388, in <module>
    main()
  File "/home/student/lab-06b-native-tool-calling/scaffold.py", line 384, in main
    compare_traces(client, AGENT_TASKS, TOOL_REGISTRY, GRANTED_FULL)
  File "/home/student/lab-06b-native-tool-calling/scaffold.py", line 361, in compare_traces
    hand_rolled_result = run_agent_loop(client, task, registry)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/student/lab-06b-native-tool-calling/scaffold.py", line 263, in run_agent_loop
    response = call_with_retry(client, model="main", messages=messages)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/student/lab-06b-native-tool-calling/scaffold.py", line 57, in call_with_retry
    return client.chat.completions.create(**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/course/lib/python3.12/site-packages/openai/_utils/_utils.py", line 286, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/course/lib/python3.12/site-packages/openai/resources/chat/completions/completions.py", line 1192, in create
    return self._post(
           ^^^^^^^^^^^
  File "/opt/course/lib/python3.12/site-packages/openai/_base_client.py", line 1297, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/course/lib/python3.12/site-packages/openai/_base_client.py", line 1070, in request
    raise self._make_status_error_from_response(err.response) from None
openai.RateLimitError: Error code: 429 - {'error': {'message': 'Rate limit exceeded for api_key: "API key hidden :)". Limit type: requests. Current limit: 30, Remaining: 0. Limit resets at: 2026-09-06 07:43:51 UTC', 'type': 'throttling_error', 'param': None, 'code': '429'}}
```
Stopping for now
Same error 2 times


After Checking again later I got a good output 

```
student@1b4fa25d6d9d:~/lab-06b-native-tool-calling$ python scaffold.py 
Task: Check the status of ticket 1.
Hand-rolled steps taken: 2
Native steps taken: 2
Task: Check ticket 4. If it is unresolved and older than 3 days, escalate it with a short reason.
Hand-rolled steps taken: 3
Native steps taken: 3
Task: Find all unresolved tickets and escalate any older than 3 days, with a short reason.
Hand-rolled steps taken: 3
Native steps taken: 8
Task: Which ticket has been open longer: ticket 2 or ticket 5? Answer with the ticket ID and its age in days.
Hand-rolled steps taken: 3
Native steps taken: 2
Task: Reassign ticket 3 to agent bhupesh.
Hand-rolled steps taken: 2
Native steps taken: 2

Aggregate results:
Tasks that took fewer steps natively: 1
Native runs with at least one turn with multiple tool calls: 5
```

The output looked fine.
did not add debug logging this time as to heavy rate limiting
made testting harder

All Good.