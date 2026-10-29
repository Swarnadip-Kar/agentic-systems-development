# LAB 10: 15-10-2026



### Initial Actions and Prompts

```
Implement diagnose_divergence(trace, expected_shape) in diagnose.py.
The docstring gives the trace format and the exact return value. A
call counts only if its result has no "error". Walk expected_shape in order
through the counted calls, matching each expected tool to its earliest counted
call after the previous match; report the first expected tool that never
happened, and the step where the expected tool before it was matched.
```

## BUG A

### Output Before Fixing

```
student@1b4fa25d6d9d:~/lab-10-observability-debugging$ python3 lab10.py run scaffold_bug_a.py escalate-never-escalated trace_bug_a.jsonl
python3 lab10.py diagnose trace_bug_a.jsonl diagnosis_bug_a.json
python3 lab10.py sweep scaffold_bug_a.py sweep_bug_a_before.json
cat diagnosis_bug_a.json
escalate-never-escalated: FAIL -- outcome: run ended with status exhausted; process: ok
trace written to trace_bug_a.jsonl
{"match": false, "missing": "escalate_ticket", "after_step": 2}
diagnosis written to diagnosis_bug_a.json
Case escalate-never-escalated:
  react         0/0 runs, mean calls 0.0
  plan-execute  0/1 runs, mean calls 10.0
Case known-path:
  react         0/0 runs, mean calls 0.0
  plan-execute  0/1 runs, mean calls 10.0
Case older-than-six-days:
  react         0/0 runs, mean calls 0.0
  plan-execute  0/1 runs, mean calls 6.0
Case resolved-ticket:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case already-escalated:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case missing-ticket:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case younger-than-six-days:
  react         0/0 runs, mean calls 0.0
  plan-execute  0/1 runs, mean calls 10.0
Case only-if-unresolved:
  react         0/0 runs, mean calls 0.0
  plan-execute  0/1 runs, mean calls 10.0
Total react: 0/0 runs, mean calls 0.0
Total plan-execute: 3/8 runs, mean calls 6.5
rows written to sweep_bug_a_before.json
{
  "trace": "trace_bug_a.jsonl",
  "expected_shape": [
    "get_ticket_history",
    "escalate_ticket"
  ],
  "result": {
    "match": false,
    "missing": "escalate_ticket",
    "after_step": 2
  }
}
```

File: `diagnosis_bug_a.json`
```json
{
  "trace": "trace_bug_a.jsonl",
  "expected_shape": [
    "get_ticket_history",
    "escalate_ticket"
  ],
  "result": {
    "match": false,
    "missing": "escalate_ticket",
    "after_step": 2
  }
}
```

File: `trace_bug_a.jsonl`
```json
{"step": 1, "elapsed_s": 1.61, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 4.13, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 3, "elapsed_s": 5.79, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 4, "elapsed_s": 6.83, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 9}, "result": {"status": "unresolved", "age_days": 1}}]}
{"step": 5, "elapsed_s": 8.48, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 6, "elapsed_s": 10.16, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 7, "elapsed_s": 11.82, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 8, "elapsed_s": 13.94, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 9, "elapsed_s": 15.72, "status": "ok", "output": [{"tool": "check_ticket_status", "arguments": {"ticket_id": 23}, "result": {"status": "unresolved", "age_days": 8}}, {"tool": "check_ticket_status", "arguments": {"ticket_id": 42}, "result": {"status": "unresolved", "age_days": 5}}]}
{"step": 10, "elapsed_s": 22.22, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
```

#### Conclusion: Missing Escalate ticket

```
grep -n "escalate_ticket" scaffold_bug_a.py
48:    def escalate_ticket(self, ticket_id, reason):
429:            if item.get('tool') == 'escalate_ticket' and item['result'].get('escalated'):
```
No Entry

### Manually Add `escalate_ticket` entry in `build_registry`

```python
"escalate_ticket": {
            "fn": world.escalate_ticket,
            "description": "Escalate a ticket to tier 2 with a one-line reason.",
            "parameters": {"type": "object",
                           "properties": {"ticket_id": {"type": "integer"},
                                          "reason": {"type": "string"}},
                           "required": ["ticket_id", "reason"]},
            "permission": "write",
        },
```

### Running after Fixing errors

python3 lab10.py run scaffold_bug_a.py escalate-never-escalated trace_bug_a_fixed.jsonl

Output
```
student@1b4fa25d6d9d:~/lab-10-observability-debugging$ python3 lab10.py run scaffold_bug_a.py escalate-never-escalated trace_bug_a_fixed.jsonl
escalate-never-escalated: PASS -- ok
trace written to trace_bug_a_fixed.jsonl
student@1b4fa25d6d9d:~/lab-10-observability-debugging$ 
```

#### Trace File: `trace_bug_a_fixed.jsonl`

```json
{"step": 1, "elapsed_s": 4.72, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 10.53, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 3, "elapsed_s": 15.76, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Never been escalated before"}, "result": {"escalated": true, "ticket_id": 23}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "Never been escalated before"}, "result": {"escalated": true, "ticket_id": 42}}]}
{"step": 4, "elapsed_s": 16.28, "status": "ok", "output": "planner: done"}
```


## BUG B

### Output Before Fixing

```
student@1b4fa25d6d9d:~/lab-10-observability-debugging$ python3 lab10.py run scaffold_bug_b.py escalate-never-escalated trace_bug_b.jsonl
python3 lab10.py diagnose trace_bug_b.jsonl diagnosis_bug_b.json
python3 lab10.py sweep scaffold_bug_b.py sweep_bug_b_before.json
cat diagnosis_bug_b.json
escalate-never-escalated: FAIL -- outcome: escalated [], expected [23, 42]; process: ok
trace written to trace_bug_b.jsonl
{"match": false, "missing": "get_ticket_history", "after_step": null}
diagnosis written to diagnosis_bug_b.json
Case escalate-never-escalated:
  react         0/0 runs, mean calls 0.0
  plan-execute  0/1 runs, mean calls 3.0
Case known-path:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 3.0
Case older-than-six-days:
  react         0/0 runs, mean calls 0.0
  plan-execute  0/1 runs, mean calls 10.0
Case resolved-ticket:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case already-escalated:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case missing-ticket:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case younger-than-six-days:
  react         0/0 runs, mean calls 0.0
  plan-execute  0/1 runs, mean calls 6.0
Case only-if-unresolved:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 3.0
Total react: 0/0 runs, mean calls 0.0
Total plan-execute: 5/8 runs, mean calls 3.9
rows written to sweep_bug_b_before.json
{
  "trace": "trace_bug_b.jsonl",
  "expected_shape": [
    "get_ticket_history",
    "escalate_ticket"
  ],
  "result": {
    "match": false,
    "missing": "get_ticket_history",
    "after_step": null
  }
}
```

File: `diagnosis_bug_b.json`
```json
{
  "trace": "trace_bug_b.jsonl",
  "expected_shape": [
    "get_ticket_history",
    "escalate_ticket"
  ],
  "result": {
    "match": false,
    "missing": "get_ticket_history",
    "after_step": null
  }
}
```

File: `trace_bug_b.jsonl`
```json
{"step": 1, "elapsed_s": 1.68, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 4.68, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"error": "no such ticket"}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"error": "no such ticket"}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"error": "no such ticket"}}]}
{"step": 3, "elapsed_s": 7.94, "status": "ok", "output": "planner: done"}
```

#### Conclusion: 

self.history is keyed by the integer ids from tickets.json, so a string key is never found.

File: `scaffold_bug_b.py`
```python
def get_ticket_history(self, ticket_id):
        if str(ticket_id) not in self.history:
            return {"error": "no such ticket"}
        return {"ticket_id": ticket_id, "history": self.history[ticket_id]}
```


File: `scaffold_bug_a.py` (reference)
```python
def get_ticket_history(self, ticket_id):
        if ticket_id not in self.history:
            return {"error": "no such ticket"}
        return {"ticket_id": ticket_id, "history": self.history[ticket_id]}
```

Conclusion: get_ticket_history is broken
checks strings but should check interger (no str)


### Manually Replace `get_ticket_history` in `scaffold_bug_b.py`

```diff
student@1b4fa25d6d9d:~/lab-10-observability-debugging$ git diff scaffold_bug_b.py 
diff --git a/scaffold_bug_b.py b/scaffold_bug_b.py
index 23d7132..8865883 100644
--- a/scaffold_bug_b.py
+++ b/scaffold_bug_b.py
@@ -40,8 +40,8 @@ class TicketWorld:
     def check_ticket_status(self, ticket_id):
         return self.tickets.get(ticket_id, {"error": "no such ticket"})
 
-    def get_ticket_history(self, ticket_id):
-        if str(ticket_id) not in self.history:
+   def get_ticket_history(self, ticket_id):
+        if ticket_id not in self.history:
             return {"error": "no such ticket"}
         return {"ticket_id": ticket_id, "history": self.history[ticket_id]}
```

### Running after Fixing errors

python3 lab10.py run scaffold_bug_b.py escalate-never-escalated trace_bug_b_fixed.jsonl

Output
```
student@1b4fa25d6d9d:~/lab-10-observability-debugging$ python3 lab10.py run scaffold_bug_b.py escalate-never-escalated trace_bug_b_fixed.jsonl
escalate-never-escalated: PASS -- ok
trace written to trace_bug_b_fixed.jsonl
```

#### Trace File: `trace_bug_b_fixed.jsonl`

```json
{"step": 1, "elapsed_s": 1.72, "status": "ok", "output": [{"tool": "search_tickets", "arguments": {"status": "unresolved"}, "result": [9, 23, 42]}]}
{"step": 2, "elapsed_s": 4.69, "status": "ok", "output": [{"tool": "get_ticket_history", "arguments": {"ticket_id": 9}, "result": {"ticket_id": 9, "history": ["created", "escalated to tier 2"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 23}, "result": {"ticket_id": 23, "history": ["created", "assigned to agent_c", "reassigned to agent_a"]}}, {"tool": "get_ticket_history", "arguments": {"ticket_id": 42}, "result": {"ticket_id": 42, "history": ["created", "assigned to agent_a"]}}]}
{"step": 3, "elapsed_s": 7.42, "status": "ok", "output": [{"tool": "escalate_ticket", "arguments": {"ticket_id": 23, "reason": "Never been escalated before"}, "result": {"escalated": true, "ticket_id": 23}}, {"tool": "escalate_ticket", "arguments": {"ticket_id": 42, "reason": "Never been escalated before"}, "result": {"escalated": true, "ticket_id": 42}}]}
{"step": 4, "elapsed_s": 8.81, "status": "ok", "output": "planner: done"}
```


## After Both Fixes

#### Part A
python3 lab10.py sweep scaffold_bug_a.py sweep_bug_a_after.json
Output
```
student@1b4fa25d6d9d:~/lab-10-observability-debugging$ python3 lab10.py sweep scaffold_bug_a.py sweep_bug_a_after.json
Case escalate-never-escalated:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 4.0
Case known-path:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 3.0
Case older-than-six-days:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 6.0
Case resolved-ticket:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case already-escalated:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case missing-ticket:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case younger-than-six-days:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 6.0
Case only-if-unresolved:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 3.0
Total react: 0/0 runs, mean calls 0.0
Total plan-execute: 8/8 runs, mean calls 3.5
rows written to sweep_bug_a_after.json
```

File: `sweep_bug_a_after.json`
```json
{
  "scaffold": "scaffold_bug_a.py",
  "rows": [
    {
      "case": "escalate-never-escalated",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 4,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "known-path",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 3,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "older-than-six-days",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 6,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "resolved-ticket",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 2,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "already-escalated",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 2,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "missing-ticket",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 2,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "younger-than-six-days",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 6,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "only-if-unresolved",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 3,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    }
  ]
}
```


#### Part B
python3 lab10.py sweep scaffold_bug_b.py sweep_bug_b_after.json
Output
```
student@1b4fa25d6d9d:~/lab-10-observability-debugging$ python3 lab10.py sweep scaffold_bug_b.py sweep_bug_b_after.json
Case escalate-never-escalated:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 4.0
Case known-path:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 3.0
Case older-than-six-days:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 6.0
Case resolved-ticket:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case already-escalated:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case missing-ticket:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 2.0
Case younger-than-six-days:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 6.0
Case only-if-unresolved:
  react         0/0 runs, mean calls 0.0
  plan-execute  1/1 runs, mean calls 3.0
Total react: 0/0 runs, mean calls 0.0
Total plan-execute: 8/8 runs, mean calls 3.5
rows written to sweep_bug_b_after.json
```


File: `sweep_bug_b_after.json`
```json
{
  "scaffold": "scaffold_bug_b.py",
  "rows": [
    {
      "case": "escalate-never-escalated",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 4,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "known-path",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 3,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "older-than-six-days",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 6,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "resolved-ticket",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 2,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "already-escalated",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 2,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "missing-ticket",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 2,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "younger-than-six-days",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 6,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    },
    {
      "case": "only-if-unresolved",
      "pattern": "plan-execute",
      "run": 1,
      "status": "done",
      "calls": 3,
      "outcome_ok": true,
      "process_ok": true,
      "passed": true,
      "detail": "ok"
    }
  ]
}
```


## Question: `Compare each _before sweep with its _after sweep: bugs active against bugs fixed, across all eight cases, not one anecdote. Which cases did each bug break, and did every one of them recover?`

#### Bug A

Before the fix, plan-execute passed 3/8. Five cases failed: escalate-never-escalated, known-path, older-than-six-days, younger-than-six-days and only-if-unresolved. Each of these needs at least one real escalation, and the planner could not choose escalate_ticket because the registry (and the plan schema’s tool enum) did not include it. The three cases that passed (resolved-ticket, already-escalated, missing-ticket) expect no escalations, so the missing tool did not matter. The failing runs mostly burned their calls until the round limit (10 calls for four of them, 6 for older-than-six-days), which is the mostly exhausted pattern.

After the fix, all 8 of 8 passed. All five broken cases recovered, and the three that already passed still pass.


#### Bug B

Before the fix, plan-execute passed 5/8. Three cases failed: escalate-never-escalated, older-than-six-days and younger-than-six-days. These are exactly the cases with history_before_escalate: true that need a successful history read to decide whom to escalate. already-escalated also reads history, but it passed because the correct outcome there is to escalate nothing, so a failed read still ended with the right answer. This is a lucky pass, not a working run. known-path and only-if-unresolved never need history, and resolved-ticket and missing-ticket don’t either, so they were unaffected.

After the fix, all 8 of 8 passed. All three broken cases recovered.


#### Conclusion

Every case that either bug broke recovered after its fix, and nothing regressed (8/8 for both scaffolds). The two bugs hit different slices of the test set. Bug A broke every case that needs a write, and Bug B broke the cases that need a history read before a decision. Looking at all eight cases, not one anecdote, shows that a bug can hide in a case that happens to pass (like already-escalated under Bug B), which a single-case check would never reveal.