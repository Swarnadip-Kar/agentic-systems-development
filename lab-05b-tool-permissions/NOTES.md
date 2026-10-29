# LAB 5b - 27-08-2026

### Initial Prompts

```
Implement
dispatch_tool_call(decision, tools, tool_permissions, granted_permissions) -- run the tool named by decision.tool (a dict: name -> callable) with decision.arguments. Never raise: an unknown tool name, or a bad-arguments call that raises TypeError internally, is real, reportable information -- catch it and return {"error": "<message>"} instead.
, with a new check: look up tool_permissions[decision.tool] ("read" or "write") and, if that permission isn't in granted_permissions, return {"error": "permission denied: '<tool>' requires '<permission>' permission"} without calling the tool at all. Check permission before attempting the call.
```


```
Next Implement

run_agent_loop(client, task, tools, tool_permissions, granted_permissions, max_steps=MAX_AGENT_STEPS) --  the bounded perceive-think-act-observe loop. Returns:
{
  "task": task,
  "steps": [{"tool": <name>, "result": <dict>}, ...],  # tool-call
                                                         # steps only
  "final_answer": <str> or None,  # None if max_steps exhausted
  "steps_taken": <int>,           # total model calls made
}
Each iteration: call the model with TOOLS_DESC as a system message plus the conversation so far; parse the decision with parse_agent_decision. If parsing fails, feed the specific error back to the model and retry
If the decision is "final_answer", stop and return it. Otherwise, dispatch the tool call via dispatch_tool_call, append its result to the conversation as the next turn, and continue. If max_steps is exhausted without a final answer, return with final_answer=None.

Threading tool_permissions and granted_permissions through to dispatch_tool_call at each tool call. A permission-denied result is recorded as a step exactly like any other tool result (same {"tool": <name>, "result": <dict>} shape) and fed back to the model as the next turn -- the model sees it was denied and has to decide what to do next, same as any other tool outcome.
```


```
Now Implement the two functions
permission_denial_report(results) -- print a summary over a list of run_agent_loop-shaped result dicts: total permission-denied steps, and which tool(s) they were for (check each result's "steps" for a "result" dict containing an "error" starting with "permission denied").

compare_permission_scopes(client, tasks, tools, tool_permissions) -- run run_agent_batch over tasks twice: once with GRANTED_READ_ONLY, once with GRANTED_FULL (both already defined). Print a comparison: how many escalate_ticket attempts were denied under read-only permission versus how many actually succeeded under full permission. This is the payoff -- same tasks, same model tendencies, different real-world outcome depending on what the harness actually allows.
```



### Logging, Debugging and Testing 

##### Initial Output

```
Escalate ticket attempts denied under read-only permission: 0
Escalate ticket attempts succeeded under full permission: 0

--- Permission-denial report over the demo fixture (see README) ---
Total permission-denied steps: 1
Tools with permission denied: escalate_ticke
```


### Final Output
With this we have the problem - we are not able to see the inner
working and verify what is actually the flow

We need a logging framemwork.
Like the last lab I promted a built a logging framework for this lab too

Things seemed fine
Output is is output.txt file.

