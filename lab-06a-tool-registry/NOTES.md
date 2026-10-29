# LAB 6a - 01-09-2026

### Initial Prompts

```
Impelent 

validate_arguments(schema, arguments) -- validate a dict of arguments against a JSON Schema like the ones in TOOL_REGISTRY ({"type": "object", "properties": {...}, "required": [...]}). Return (True, None) if every required field in schema["required"] is present in arguments, and every field that is present matches its declared type ("integer" -> int, "string" -> str, "number" -> int or float, "boolean" -> bool). Otherwise return (False, "<a specific, human-readable reason>"). Extra fields not mentioned in properties are fine -- don't reject them.

build_tools_desc(registry) -- generate the prompt text the model reads, from the registry, instead of hand-typing it. For each tool, produce a line like check_ticket_status(ticket_id: integer) -- Look up a ticket's status and age. (name, then each property name and its JSON Schema type in parentheses, then the description) and join them under a header telling the model it has these tools. After the tool list, add
"At each turn respond with ONLY a JSON object, no other text, in one "
    "of these shapes:\n"
    '{"action": "call_tool", "tool": "check_ticket_status", '
    '"arguments": {"ticket_id": <int>}}\n'
    '{"action": "call_tool", "tool": "escalate_ticket", '
    '"arguments": {"ticket_id": <int>, "reason": "<str>"}}\n'
    '{"action": "final_answer", "answer": "<your answer>"}'


Next implement 
dispatch_tool_call(decision, registry) --: unknown tool name returns {"error": "unknown tool: <name>"}. Known tool: validate decision.arguments against that tool's schema with validate_arguments first -- if invalid, return {"error": "invalid arguments: <reason>"} without calling the tool. Only if validation passes, call spec["fn"](**decision.arguments) and return its result; if that raises TypeError anyway, return {"error": "dispatch failed: <message>"}.
and
filter_relevant_tools(registry, task, max_tools=3) -- for "picking a tool from a longer menu") without building it. Build a simple version: split task into lowercase words (split on anything that isn't a letter or digit), and for each tool in registry, score it by how many of those words also appear in its name or description (also lowercased and word-split). Return a new dict containing only the max_tools highest-scoring entries (ties broken however you like, but never return more than max_tools). A tool that scores 0 should never be included even if fewer than max_tools tools scored above 0.

Now build two small tools
close_ticket(ticket_id) -- append ticket_id to CLOSED_TICKETS and return {"closed": True, "ticket_id": ticket_id}
and 
get_ticket_history(ticket_id) -- return TICKET_HISTORY.get(ticket_id, {"error": "no such ticket"}) (TICKET_HISTORY is already given). 
```

### Manual Tool Registry

After the prompts I manually added the tool registry

I realized aider had alredy added them 
Stil I have manually verified the tool registry

```json
    "close_ticket": {
        "fn": close_ticket,
        "description": "Close a ticket.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
    },
    "get_ticket_history": {
        "fn": get_ticket_history,
        "description": "Get the history of a ticket.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
    },
```

### Logging, Debugging and Testing 

After these steps I ran 
python scaffold.py


#### Output

```
finished: 5/5, exhausted: 0/5, included escalation: 3/5, avg steps: 4.20

--- Report over the demo fixture (see README) ---
finished: 1/2, exhausted: 1/2, included escalation: 1/2, avg steps: 7.50

--- filter_relevant_tools demo ---
task: 'Check the status of my support ticket and escalate it if needed.'
selected tools: ['check_ticket_status', 'escalate_ticket', 'get_ticket_history']
```

The output looked fine.


### Extra Logging for Better Understading

Prompt
```
Add Logging to the code 
When a user promt is received
when a model resposds with a action
- all tool calls - and what it recievd
till the final respose.
For every user query/ticket.
```

Now the output is good 
with better insight

```
student@1b4fa25d6d9d:~/lab-06a-tool-registry$ python scaffold.py 
2026-09-01 10:00:49,820 - INFO - User prompt received: Check the status of ticket 1.
2026-09-01 10:00:53,184 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:00:53,193 - INFO - Model responded with action: {"action": "call_tool", "tool": "check_ticket_status", "arguments": {"ticket_id": 1}}
2026-09-01 10:00:53,193 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 1} resulted in {'status': 'unresolved', 'age_days': 6}
2026-09-01 10:00:54,883 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:00:54,928 - INFO - Model responded with action: {"action": "call_tool", "tool": "escalate_ticket", "arguments": {"ticket_id": 1, "reason": "Unresolved for over 5 days"}}
2026-09-01 10:00:54,929 - INFO - Tool call: escalate_ticket with arguments {'ticket_id': 1, 'reason': 'Unresolved for over 5 days'} resulted in {'escalated': True, 'ticket_id': 1}
2026-09-01 10:00:56,231 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:00:56,276 - INFO - Model responded with action: {"action": "final_answer", "answer": "Ticket 1 has been escalated due to being unresolved for more than 5 days."}
2026-09-01 10:00:56,276 - INFO - Final answer: Ticket 1 has been escalated due to being unresolved for more than 5 days.
2026-09-01 10:00:56,276 - INFO - User prompt received: Check ticket 4. If it is unresolved and older than 3 days, escalate it with a short reason.
2026-09-01 10:00:57,933 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:00:57,980 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "check_ticket_status",
  "arguments": {
    "ticket_id": 4
  }
}
```
2026-09-01 10:00:57,980 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 4} resulted in {'status': 'unresolved', 'age_days': 8}
2026-09-01 10:01:00,135 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:01:00,176 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "escalate_ticket",
  "arguments": {
    "ticket_id": 4,
    "reason": "Unresolved for over 3 days"
  }
}
```
2026-09-01 10:01:00,176 - INFO - Tool call: escalate_ticket with arguments {'ticket_id': 4, 'reason': 'Unresolved for over 3 days'} resulted in {'escalated': True, 'ticket_id': 4}
2026-09-01 10:01:03,880 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:01:03,924 - INFO - Model responded with action: ```json
{
  "action": "final_answer",
  "answer": "Ticket 4 has been escalated."
}
```
2026-09-01 10:01:03,925 - INFO - Final answer: Ticket 4 has been escalated.
2026-09-01 10:01:03,925 - INFO - User prompt received: Find all unresolved tickets and escalate any older than 3 days, with a short reason.
2026-09-01 10:01:06,030 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:01:06,072 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "search_tickets",
  "arguments": {
    "status": "unresolved"
  }
}
```
2026-09-01 10:01:06,073 - INFO - Tool call: search_tickets with arguments {'status': 'unresolved'} resulted in [1, 3, 4, 6]
2026-09-01 10:01:18,830 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:01:18,872 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "check_ticket_status",
  "arguments": {
    "ticket_id": 1
  }
}
```
2026-09-01 10:01:18,873 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 1} resulted in {'status': 'unresolved', 'age_days': 6}
2026-09-01 10:01:36,913 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:01:36,957 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "escalate_ticket",
  "arguments": {
    "ticket_id": 1,
    "reason": "Old unresolved ticket"
  }
}
```
2026-09-01 10:01:36,957 - INFO - Tool call: escalate_ticket with arguments {'ticket_id': 1, 'reason': 'Old unresolved ticket'} resulted in {'escalated': True, 'ticket_id': 1}
2026-09-01 10:01:38,755 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:01:38,800 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "check_ticket_status",
  "arguments": {
    "ticket_id": 3
  }
}
```
2026-09-01 10:01:38,800 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 3} resulted in {'status': 'unresolved', 'age_days': 1}
2026-09-01 10:01:41,963 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:01:42,004 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "check_ticket_status",
  "arguments": {
    "ticket_id": 4
  }
}
```
2026-09-01 10:01:42,005 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 4} resulted in {'status': 'unresolved', 'age_days': 8}
2026-09-01 10:01:46,578 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:01:46,620 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "escalate_ticket",
  "arguments": {
    "ticket_id": 4,
    "reason": "Old unresolved ticket"
  }
}
```
2026-09-01 10:01:46,620 - INFO - Tool call: escalate_ticket with arguments {'ticket_id': 4, 'reason': 'Old unresolved ticket'} resulted in {'escalated': True, 'ticket_id': 4}
2026-09-01 10:02:14,952 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:14,997 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "check_ticket_status",
  "arguments": {
    "ticket_id": 6
  }
}
```
2026-09-01 10:02:14,997 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 6} resulted in {'status': 'unresolved', 'age_days': 9}
2026-09-01 10:02:18,756 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:18,800 - INFO - Model responded with action: ```json
{
  "action": "call_tool",
  "tool": "escalate_ticket",
  "arguments": {
    "ticket_id": 6,
    "reason": "Old unresolved ticket"
  }
}
```
2026-09-01 10:02:18,800 - INFO - Tool call: escalate_ticket with arguments {'ticket_id': 6, 'reason': 'Old unresolved ticket'} resulted in {'escalated': True, 'ticket_id': 6}
2026-09-01 10:02:21,675 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:21,716 - INFO - Model responded with action: ```json
{
  "action": "final_answer",
  "answer": "All old unresolved tickets have been escalated."
}
```
2026-09-01 10:02:21,716 - INFO - Final answer: All old unresolved tickets have been escalated.
2026-09-01 10:02:21,716 - INFO - User prompt received: Which ticket has been open longer: ticket 2 or ticket 5? Answer with the ticket ID and its age in days.
2026-09-01 10:02:24,424 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:24,468 - INFO - Model responded with action: {"action": "call_tool", "tool": "check_ticket_status", "arguments": {"ticket_id": 2}}
2026-09-01 10:02:24,469 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 2} resulted in {'status': 'resolved', 'age_days': 4}
2026-09-01 10:02:26,906 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:26,948 - INFO - Model responded with action: {"action": "call_tool", "tool": "check_ticket_status", "arguments": {"ticket_id": 5}}
2026-09-01 10:02:26,948 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 5} resulted in {'status': 'resolved', 'age_days': 2}
2026-09-01 10:02:36,920 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:36,964 - ERROR - Error in response: response was not valid JSON: Expecting ':' delimiter: line 1 column 16 (char 15)
2026-09-01 10:02:43,783 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:43,828 - INFO - Model responded with action: {"action": "call_tool", "tool": "check_ticket_status", "arguments": {"ticket_id": 5}}
2026-09-01 10:02:43,829 - INFO - Tool call: check_ticket_status with arguments {'ticket_id': 5} resulted in {'status': 'resolved', 'age_days': 2}
2026-09-01 10:02:47,559 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:47,604 - INFO - Model responded with action: {"action": "final_answer", "answer": "Ticket 2 has been open longer with an age of 4 days."}
2026-09-01 10:02:47,604 - INFO - Final answer: Ticket 2 has been open longer with an age of 4 days.
2026-09-01 10:02:47,604 - INFO - User prompt received: Reassign ticket 3 to agent bhupesh.
2026-09-01 10:02:51,565 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:51,612 - INFO - Model responded with action: {
  "action": "call_tool",
  "tool": "reassign_ticket",
  "arguments": {
    "ticket_id": 3,
    "assignee": "bhupesh"
  }
}
2026-09-01 10:02:51,612 - INFO - Tool call: reassign_ticket with arguments {'ticket_id': 3, 'assignee': 'bhupesh'} resulted in {'reassigned': True, 'ticket_id': 3, 'assignee': 'bhupesh'}
2026-09-01 10:02:53,047 - INFO - HTTP Request: POST http://127.0.0.1:8890/chat/completions "HTTP/1.1 200 OK"
2026-09-01 10:02:53,088 - INFO - Model responded with action: {
  "action": "final_answer",
  "answer": "Ticket 3 has been reassigned to agent Bhupesh."
}
2026-09-01 10:02:53,089 - INFO - Final answer: Ticket 3 has been reassigned to agent Bhupesh.
finished: 5/5, exhausted: 0/5, included escalation: 3/5, avg steps: 4.40

--- Report over the demo fixture (see README) ---
finished: 1/2, exhausted: 1/2, included escalation: 1/2, avg steps: 7.50

--- filter_relevant_tools demo ---
task: 'Check the status of my support ticket and escalate it if needed.'
selected tools: ['check_ticket_status', 'escalate_ticket', 'get_ticket_history']
```

All Looks Good.
