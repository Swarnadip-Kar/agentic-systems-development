# LAB 8b: 01-10-2026

### Initial Actions and Prompts

```
Implement 
make_gated_step(client, registry, granted_permissions, approver) -- return a step function for the harness. Its state is {"task": str, "observations": list, "denied": list}, as made by gated_initial_state. approver(writes) is called with a list of write steps and returns True to allow them. Each round:

Call plan_decision(state, client, registry) once. If done is true, return (state, True, "planner: done").
Apply cut_before_unobserved_writes to its steps. If nothing is left, add {"not_run": "anything", "why": "You said the task is not done but planned no steps."}.
Collect the plan's write steps (the given is_write). If there are none, run the plan with execute_until_stuck.
If there are writes, make a key with json.dumps(writes, sort_keys=True).
If that key is already in state["denied"], do not call the approver. Add {"not_run": "writes", "why": "These writes were already denied by a human reviewer. Do not propose them again."}.
Otherwise call approver(writes) exactly once. If it returns False, add {"not_run": "writes", "why": "A human reviewer denied these writes. Do not propose them again."} and add the key to denied.
If it returns True, run the plan with execute_until_stuck.
Return the new state, False, and the list of new observations. Never modify the state you were given; denied in the new state is a new list.
```

```
Next Implement the functions
retrieve(query, k=2) -- keyword retrieval over RUNBOOK. Score each article by how many of the given tokens(query) also appear in tokens(article_text). Sort by score, highest first, breaking ties by article id in alphabetical order. Return up to k ids, leaving out any article that scored 0.

retrieve_then_answer(question, client, retriever=retrieve) -- the fixed workflow. Call retriever(question). If it returns nothing, return ([], NOT_COVERED) without calling the model: there is nothing to ground an answer in, so the code decides. Otherwise make one call with model="main", temperature=0, and messages=answer_messages(question, doc_ids), and return (doc_ids, <the reply's content>).
```

```
Implement
Retrieval as a tool.

build_runbook_registry(retriever=retrieve) -- a registry with one tool, "search_runbook": a non-empty description, parameters taking a required string query, permission "read", and an fn that returns [{"id": d, "text": RUNBOOK[d]} for d in retriever(query)].

answer_with_search_tool(question, client, retriever=retrieve, trace_path="trace_search.jsonl") -- run the given react_step with that registry and {"read"} under a RuntimeHarness with max_steps=6 and this trace_path (start the file empty), from retrieval_agent_state(question). Return (searches, answer): searches lists (query, [ids]) for every search_runbook call in the trace, in order; answer is the harness's output if its status is "done", otherwise None.
```

```
Then Implement these

expand_query(query, synonyms=SYNONYMS) -- for each word of the query, in order (lowercase, [a-z0-9]+), add that word's synonyms from the dictionary. Return the query followed by a space and the added words separated by spaces, or the query unchanged if nothing was added.

hit_rate(questions, retriever) -- return (hits, total), where a question is a hit if its expected id is in retriever(question).
Fill in SYNONYMS so that retrieve_expanded answers more questions than retrieve does, without losing any that retrieve already answered. Keys are words a person might say; values are the words the runbook uses.
```



### Logging, Debugging and Testing 

After these steps I ran 
python scaffold.py

Many bugs had to fix them.

This the output after debugging
```
student@1b4fa25d6d9d:~/lab-08b-gates-retrieval$ python scaffold.py 
== retrieval hit rate on questions.json (top 2)
   plain keywords:  7/12
   with SYNONYMS:   12/12

== retrieve, then answer
   When am I allowed to close a ticket?
     retrieved ['closing-criteria']: You are allowed to close a ticket only after the customer confirms the fix, or after 7 days without a customer reply. You should never close an escalated ticket yourself.
   What is the office wifi password?
     retrieved []: The runbook does not cover this.

== the agent searches for itself
   plain keywords:
     searched "money back request" -> []
     answer: It seems there is no specific entry for "money back request" in the runbook. However, typically such requests are handled by the Customer Service or Refunds department. I recommend checking with them 
   with SYNONYMS:
     searched "money back request" -> ['data-requests', 'refunds']
     answer: According to the runbook, if a customer wants their money back and the refund amount is larger than 2000 rupees, it should be forwarded to the billing team with the ticket ID and order number. For ref

== the approval gate
   reviewer sees: [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Never been escalated before"}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "Never been escalated before"}}] -> DENIED
   deny_all: status exhausted, escalated []
   reviewer sees: [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Never been escalated before"}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "Never been escalated before"}}] -> approved
   approve_all: status done, escalated [23, 42]
```

Also 4 files

#### `trace_gate_approve_all.jsonl`
```json
{"step": 1, "elapsed_s": 1.54, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 4.9, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 3, "elapsed_s": 8.21, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Never been escalated before"}, "result": {"escalated": true, "ticket_id": 23}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "Never been escalated before"}, "result": {"escalated": true, "ticket_id": 42}}]}
{"step": 4, "elapsed_s": 8.94, "status": "ok", "output": "planner: done"}
```

#### `trace_gate_deny_all.jsonl`
```json
{"step": 1, "elapsed_s": 1.38, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 4.42, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 3, "elapsed_s": 7.21, "status": "ok", "output": [{"not_run": "writes", "why": "A human reviewer denied these writes. Do not propose them again."}]}
{"step": 4, "elapsed_s": 10.02, "status": "ok", "output": [{"not_run": "writes", "why": "These writes were already denied by a human reviewer. Do not propose them again."}]}
{"step": 5, "elapsed_s": 12.3, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 6, "elapsed_s": 15.48, "status": "ok", "output": [{"not_run": "writes", "why": "These writes were already denied by a human reviewer. Do not propose them again."}]}
{"step": 7, "elapsed_s": 18.92, "status": "ok", "output": [{"not_run": "writes", "why": "These writes were already denied by a human reviewer. Do not propose them again."}]}
{"step": 8, "elapsed_s": 22.49, "status": "ok", "output": [{"not_run": "writes", "why": "These writes were already denied by a human reviewer. Do not propose them again."}]}
{"step": 9, "elapsed_s": 25.62, "status": "ok", "output": [{"not_run": "writes", "why": "These writes were already denied by a human reviewer. Do not propose them again."}]}
{"step": 10, "elapsed_s": 28.76, "status": "ok", "output": [{"not_run": "writes", "why": "These writes were already denied by a human reviewer. Do not propose them again."}]}
```

#### `trace_search_retrieve.jsonl`
```json
{"step": 1, "elapsed_s": 0.95, "status": "ok", "output": [{"tool": "search_runbook", "arguments": {"query": "money back request"}, "result": []}]}
{"step": 2, "elapsed_s": 3.12, "status": "ok", "output": "It seems there is no specific entry for \"money back request\" in the runbook. However, typically such requests are handled by the Customer Service or Refunds department. I recommend checking with them for the appropriate procedure to handle the customer's request for a refund. If you need more specific information, please provide additional details about the context of the request."}
```

#### `trace_search_retrieve_expanded.jsonl`
```json
{"step": 1, "elapsed_s": 0.89, "status": "ok", "output": [{"tool": "search_runbook", "arguments": {"query": "money back request"}, "result": [{"id": "data-requests", "text": "Personal data requests. If a customer asks for a copy of their personal data, or asks for their account to be deleted, forward the ticket to the privacy team within 1 day."}, {"id": "refunds", "text": "Refunds. Support agents may approve refunds up to 2000 rupees. Larger refunds go to the billing team with the ticket id and order number."}]}]}
{"step": 2, "elapsed_s": 2.91, "status": "ok", "output": "According to the runbook, if a customer wants their money back and the refund amount is larger than 2000 rupees, it should be forwarded to the billing team with the ticket ID and order number. For refunds up to 2000 rupees, support agents may approve them directly."}
```
The Output Looks Fine.
All Good.