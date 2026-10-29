# LAB 9b: 08-10-2026

### Initial Actions and Prompts

```
Implement the following in scaffold.py and report back any assumptions you made

regression_check(summary, cases, baseline, candidate) -- summary is what compare_report returns. Return the ids of the cases, in the order of cases, where the candidate's pass rate (passed / runs) is lower than the baseline's. A case that improved, or stayed the same, is not a regression.

run_regression(client, cases, baseline="plan-execute", candidate="plan-execute-on-aux", runs=1, trace_dir=".") -- run both versions over the test set with run_test_set, make the summary with compare_report, and find the regressions with regression_check. Print one line per case: its id, the baseline's and candidate's passed/runs, and REGRESSION or ok. Then print one verdict line: how many cases got worse, and Do not ship this change. if any did. Return {"summary": ..., "regressions": [...]}.

Label the answers yourself, before any grader runs.

load_labels(path="answers.json") -- return {answer_id: label}. Raise ValueError naming the answer's id if any label is not "pass" or "fail", or any reason is empty.
```


```
Then Write The Grader

build_verdict_schema() -- the JSON schema for the grader's reply: an object with a required "verdict" that must be "pass" or "fail" (use "enum") and a required string "reason". You may add a boolean for each of your criteria.
grade_answer(item, client, model) -- one model call with model=model, temperature=0, messages=grader_messages(item, RUBRIC), and response_format={"type": "json_schema", "json_schema": {"name": "grade", "schema": build_verdict_schema()}}. Return the parsed reply as a dict.

and then implement
grade_the_graders(client, answers, labels, graders=("aux", "main")) -- for each grader model, grade every answer with grade_answer, using CountingClient(client). Count how many verdicts match your labels, and list the ids where they differ, in the order of answers. Print each grader's agreement, and each disagreement with the answer's id, the grader's verdict, and yours. Return {model: {"agree": k, "total": n, "disagreements": [ids]}}.
```



### Manual Additions

After these steps I Hand Edited `answers.json`

#### answers.json
```json
[
 {
  "id": "r1",
  "question": "Ticket 23 is unresolved, 8 days old, and was never escalated. Should it be escalated?",
  "answer": "Yes. Escalate it to tier 2 with a one-line reason: it is older than 3 days and has never been escalated.",
  "label": "pass",
  "reason": "Agrees with the runbook escalation policy and correctly answers the question."
 },
 {
  "id": "r2",
  "question": "Ticket 23 is unresolved, 8 days old, and was never escalated. Should it be escalated?",
  "answer": "No. Tickets should only be escalated after 10 days without resolution.",
  "label": "fail",
  "reason": "Contradicts the runbook rule requiring escalation after 3 days."
 },
 {
  "id": "r3",
  "question": "How quickly must we send the first response to a customer?",
  "answer": "Within 1 day.",
  "label": "pass",
  "reason": "Accurately answers the question matching the service level targets in the runbook."
 },
 {
  "id": "r4",
  "question": "A customer wants a refund of 5000 rupees. What should I do?",
  "answer": "Send it to the billing team with the ticket id and order number. Agents can only approve refunds up to 2000 rupees.",
  "label": "pass",
  "reason": "Agrees with the refunds policy for amounts over 2000 rupees."
 },
 {
  "id": "r5",
  "question": "A customer wants a refund of 5000 rupees. What should I do?",
  "answer": "You can approve it yourself, since agents are allowed to issue refunds.",
  "label": "fail",
  "reason": "Contradicts the runbook policy that agents can only approve refunds up to 2000 rupees."
 },
 {
  "id": "r6",
  "question": "A ticket says the customer's password was leaked. What do I do?",
  "answer": "Reply to the customer asking them to reset their password, then close the ticket.",
  "label": "fail",
  "reason": "Violates the security policy prohibiting customer replies and requiring paging security on-call."
 },
 {
  "id": "r7",
  "question": "What is the office wifi password?",
  "answer": "According to the IT section of the runbook, the office wifi password is support2024.",
  "label": "fail",
  "reason": "Hallucinates information and sections not present in the runbook."
 },
 {
  "id": "r8",
  "question": "What are the resolution targets for tickets?",
  "answer": "Resolution within 2 days for normal tickets and within 5 days for urgent tickets.",
  "label": "fail",
  "reason": "Inverts the resolution targets for normal and urgent tickets."
 },
 {
  "id": "r9",
  "question": "A customer wants a refund of 5000 rupees. What should I do?",
  "answer": "The runbook does not cover refunds.",
  "label": "fail",
  "reason": "Incorrectly claims the runbook does not cover refunds when a refunds policy exists."
 },
 {
  "id": "r10",
  "question": "How quickly must we send the first response to a customer?",
  "answer": "Great question! Timely communication really matters in support work, because customers who hear back quickly tend to stay calm and trust the process. According to the runbook's service level targets, the first response must go out within 1 day of the ticket arriving, so it is worth checking your queue for new tickets regularly throughout the day.",
  "label": "fail",
  "reason": "Adds extraneous statements and commentary not found in the runbook."
 }
]
```


#### The Rubric
```python
RUBRIC = """
Grade the answer against the runbook ONLY. Check each:
1. Every claim in the answer is supported by the runbook (no contradictions).
2. The answer adds no facts, numbers, or steps the runbook does not state.
3. The answer addresses the question, or says plainly that the runbook does not cover it.
Verdict is "pass" only if ALL three hold. If any fails, verdict is "fail".
Give a one-line reason naming the failed criterion.
"""
```


### Logging, Debugging and Testing 

Then I ran
python scaffold.py

Many bugs had to fix them.

This the output after debugging
```
student@1b4fa25d6d9d:~/lab-09b-regressions-graders$ python scaffold.py 
== Is the change safe? (planner on main vs on aux)
case                                plan-execute   plan-execute-on-aux
escalate-never-escalated          1/1  4.0 calls        1/1  5.0 calls
known-path                        1/1  3.0 calls        1/1  3.0 calls
older-than-six-days               1/1  6.0 calls       0/1  10.0 calls
resolved-ticket                   1/1  2.0 calls        1/1  2.0 calls
already-escalated                 1/1  2.0 calls       0/1  10.0 calls
missing-ticket                    1/1  2.0 calls       0/1  10.0 calls
younger-than-six-days             1/1  6.0 calls       0/1  10.0 calls
only-if-unresolved                1/1  3.0 calls       0/1  10.0 calls
TOTAL                                        8/8                   3/8
escalate-never-escalated 1/1 1/1 ok
known-path 1/1 1/1 ok
older-than-six-days 1/1 0/1 REGRESSION
resolved-ticket 1/1 1/1 ok
already-escalated 1/1 0/1 REGRESSION
missing-ticket 1/1 0/1 REGRESSION
younger-than-six-days 1/1 0/1 REGRESSION
only-if-unresolved 1/1 0/1 REGRESSION
5 cases got worse. Do not ship this change.

== Does the grader agree with you?
aux agreement: 8/10
Disagreement: r4, grader: fail, your label: pass
Disagreement: r8, grader: pass, your label: fail
main agreement: 9/10
Disagreement: r10, grader: pass, your label: fail
```

Also many files


#### `trace_already-escalated_plan-execute-on-aux_1.jsonl`
```json
{"step": 1, "elapsed_s": 1.43, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 2, "elapsed_s": 2.88, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}]}
{"step": 3, "elapsed_s": 4.3, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "escalated"}, "result": []}]}
{"step": 4, "elapsed_s": 5.82, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 5, "elapsed_s": 7.37, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 6, "elapsed_s": 8.83, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 7, "elapsed_s": 10.28, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 8, "elapsed_s": 11.72, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 9, "elapsed_s": 13.54, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 10, "elapsed_s": 15.36, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
```

#### `trace_already-escalated_plan-execute_1.jsonl`
```json
{"step": 1, "elapsed_s": 2.68, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}]}
{"step": 2, "elapsed_s": 3.89, "status": "ok", "output": "planner: done"}
```

#### `trace_escalate-never-escalated_plan-execute-on-aux_1.jsonl`
```json
{"step": 1, "elapsed_s": 1.35, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 4.38, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 3, "elapsed_s": 7.4, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 4, "elapsed_s": 10.33, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Initial assignment took too long."}, "result": {"escalated": true, "ticket_id": 23}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "No action taken after creation."}, "result": {"escalated": true, "ticket_id": 42}}]}
{"step": 5, "elapsed_s": 10.96, "status": "ok", "output": "planner: done"}
```

#### `trace_escalate-never-escalated_plan-execute_1.jsonl`
```json
{"step": 1, "elapsed_s": 4.05, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 12.87, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 3, "elapsed_s": 23.8, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Never been escalated before"}, "result": {"escalated": true, "ticket_id": 23}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "Never been escalated before"}, "result": {"escalated": true, "ticket_id": 42}}]}
{"step": 4, "elapsed_s": 24.91, "status": "ok", "output": "planner: done"}
```

#### `trace_known-path_plan-execute-on-aux_1.jsonl`
```json
{"step": 1, "elapsed_s": 2.24, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 2, "elapsed_s": 5.34, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "older than 3 days and never escalated"}, "result": {"escalated": true, "ticket_id": 23}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "older than 3 days and never escalated"}, "result": {"escalated": true, "ticket_id": 42}}]}
{"step": 3, "elapsed_s": 5.97, "status": "ok", "output": "planner: done"}
```

#### `trace_known-path_plan-execute_1.jsonl`
```json
{"step": 1, "elapsed_s": 5.61, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 2, "elapsed_s": 11.23, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "older than 3 days and never escalated"}, "result": {"escalated": true, "ticket_id": 23}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "older than 3 days and never escalated"}, "result": {"escalated": true, "ticket_id": 42}}]}
{"step": 3, "elapsed_s": 12.24, "status": "ok", "output": "planner: done"}
```

#### `trace_missing-ticket_plan-execute-on-aux_1.jsonl`
```json
{"step": 1, "elapsed_s": 2.57, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 99}, "result": {"error": "no such ticket"}}]}
{"step": 2, "elapsed_s": 3.99, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "open"}, "result": []}]}
{"step": 3, "elapsed_s": 5.77, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "pending"}, "result": []}]}
{"step": 4, "elapsed_s": 7.21, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "all"}, "result": []}]}
{"step": 5, "elapsed_s": 9.54, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "closed"}, "result": []}]}
{"step": 6, "elapsed_s": 12.63, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "all"}, "result": []}]}
{"step": 7, "elapsed_s": 16.93, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "all"}, "result": []}]}
{"step": 8, "elapsed_s": 21.54, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "all"}, "result": []}]}
{"step": 9, "elapsed_s": 22.9, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "all"}, "result": []}]}
{"step": 10, "elapsed_s": 24.24, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "all"}, "result": []}]}
```

#### `trace_missing-ticket_plan-execute_1.jsonl`
```json
{"step": 1, "elapsed_s": 5.38, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 99}, "result": {"error": "no such ticket"}}]}
{"step": 2, "elapsed_s": 7.48, "status": "ok", "output": "planner: done"}
```

#### `trace_older-than-six-days_plan-execute-on-aux_1.jsonl`
```json
{"step": 1, "elapsed_s": 1.42, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 4.5, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 3, "elapsed_s": 6.01, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}]}
{"step": 4, "elapsed_s": 8.3, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 5, "elapsed_s": 11.42, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 6, "elapsed_s": 15.7, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}]}
{"step": 7, "elapsed_s": 19.93, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}]}
{"step": 8, "elapsed_s": 21.42, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 9, "elapsed_s": 22.83, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 10, "elapsed_s": 24.22, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
```

#### `trace_older-than-six-days_plan-execute_1.jsonl`
```json
{"step": 1, "elapsed_s": 2.45, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 7.91, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 3, "elapsed_s": 10.61, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}]}
{"step": 4, "elapsed_s": 14.78, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 5, "elapsed_s": 18.54, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Ticket is older than 6 days and has never been escalated before."}, "result": {"escalated": true, "ticket_id": 23}}]}
{"step": 6, "elapsed_s": 19.6, "status": "ok", "output": "planner: done"}
```

#### `trace_only-if-unresolved_plan-execute-on-aux_1.jsonl`
```json
{"step": 1, "elapsed_s": 1.46, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 3.8, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 31}, "result": {"status": "resolved", "age_days": 12}}]}
{"step": 3, "elapsed_s": 5.29, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}]}
{"step": 4, "elapsed_s": 7.19, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "urgent issue requiring immediate attention"}, "result": {"escalated": true, "ticket_id": 23}}]}
{"step": 5, "elapsed_s": 8.66, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 31}, "result": {"status": "resolved", "age_days": 12}}]}
{"step": 6, "elapsed_s": 10.14, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 31}, "result": {"status": "resolved", "age_days": 12}}]}
{"step": 7, "elapsed_s": 11.55, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 8, "elapsed_s": 13.05, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 31}, "result": {"status": "resolved", "age_days": 12}}]}
{"step": 9, "elapsed_s": 14.55, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 31}, "result": {"status": "resolved", "age_days": 12}}]}
{"step": 10, "elapsed_s": 16.01, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
```

#### `trace_only-if-unresolved_plan-execute_1.jsonl`
```json
{"step": 1, "elapsed_s": 4.47, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 31}, "result": {"status": "resolved", "age_days": 12}}]}
{"step": 2, "elapsed_s": 9.8, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Ticket is still unresolved after 8 days."}, "result": {"escalated": true, "ticket_id": 23}}]}
{"step": 3, "elapsed_s": 10.98, "status": "ok", "output": "planner: done"}
```

#### `trace_resolved-ticket_plan-execute-on-aux_1.jsonl`
```json
{"step": 1, "elapsed_s": 1.46, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 17}, "result": {"status": "resolved", "age_days": 2}}]}
{"step": 2, "elapsed_s": 2.02, "status": "ok", "output": "planner: done"}
```

#### `trace_resolved-ticket_plan-execute_1.jsonl`
```json
{"step": 1, "elapsed_s": 5.56, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 17}, "result": {"status": "resolved", "age_days": 2}}]}
{"step": 2, "elapsed_s": 6.78, "status": "ok", "output": "planner: done"}
```

#### `trace_younger-than-six-days_plan-execute-on-aux_1.jsonl`
```json
{"step": 1, "elapsed_s": 1.38, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 3.68, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}]}
{"step": 3, "elapsed_s": 7.67, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 4, "elapsed_s": 14.04, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 5, "elapsed_s": 15.46, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 6, "elapsed_s": 21.13, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 7, "elapsed_s": 22.57, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 8, "elapsed_s": 23.98, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 9, "elapsed_s": 29.46, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 10, "elapsed_s": 30.87, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
```

#### `trace_younger-than-six-days_plan-execute_1.jsonl`
```json
{"step": 1, "elapsed_s": 16.97, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 26.42, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 3, "elapsed_s": 37.84, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 4, "elapsed_s": 40.44, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}]}
{"step": 5, "elapsed_s": 43.79, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "Younger than 6 days and never escalated"}, "result": {"escalated": true, "ticket_id": 42}}]}
{"step": 6, "elapsed_s": 44.84, "status": "ok", "output": "planner: done"}
```


The Output Looks Fine.
All Good.


### Conclusion


**Prediction 2 held.**

How the aux planner failed (from the traces): every regressed case ended at
10 calls, so the run was `exhausted` (hit MAX_ROUNDS) rather than finishing
with a wrong answer.

#### Grader agreement

| Grader | Agreement | Disagreements |
|--------|-----------|---------------|
| aux    | 8/10      | r4, r8        |
| main   | 9/10      | r10           |

**Prediction 3 held, weakly.** Main agreed more than aux, but the gap is one
answer out of ten, so this is consistent with the prediction, not proof.


- r8 (aux pass, me fail): GRADER WRONG. The answer swaps the normal (5 day)
  and urgent (2 day) targets in sla-targets. The smaller model missed a
  swapped-number contradiction.
- r4 (aux fail, me pass): GRADER WRONG. The 2000 limit, billing team, ticket
  id and order number are all in the refunds entry. False negative.
- r10 (main pass, me fail): RUBRIC AMBIGUOUS. The one fact (1 day) is
  correct, but the answer adds commentary not in the runbook. Criterion 2
  only bans extra "facts, numbers, or steps", so main passed it on a literal
  reading. My label follows my labelling rule; the rubric did not match it.



All good.