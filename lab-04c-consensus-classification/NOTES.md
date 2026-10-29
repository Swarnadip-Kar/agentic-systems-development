# LAB 4c - 20-08-2026

### Initial Prompts
```
Implement 
get_consensus_classification(client, ticket_text, n_calls=CONSENSUS_CALLS) 
-- call classify_with_schema n_calls times independently (fresh calls, not retries of a failed one), 
and validate each raw response with validate_classification, discarding any that fail validation.

A consensus exists only if a strict majority of the valid responses agree on the same category 
-- with CONSENSUS_CALLS = 3, that means at least 2 of the 3 valid responses must share a category. 
If a consensus category exists: build a TicketClassification for it with confidence set to the average 
confidence of the responses that agreed, and reasoning taken from the first agreeing response. 
Return (classification, agree_count) where agree_count is how many of the n_calls responses 
agreed on that category (2 or 3).

If no category reaches a majority -- including when fewer than 2 responses even validated 
-- there is no consensus. 
Return (None, 0) in that case; do not guess or pick a highest-confidence single answer.
```


```
Now Implement
classify_batch_with_consensus(client, tickets, n_calls=CONSENSUS_CALLS) 
-- call get_consensus_classification for every ticket in tickets. 
Record (ticket["id"], classification, agree_count) for every ticket 
-- classification may legitimately be None when no consensus was reached; 
that's an expected outcome here, not an error. Return the list of recorded tuples.
```

```
Now Implement
consensus_report(recorded) 
-- given the recorded list from classify_batch_with_consensus(client, tickets, n_calls=CONSENSUS_CALLS), 
print a summary with three buckets: tickets with unanimous agreement (agree_count == 3), 
tickets with majority agreement (agree_count == 2), 
and tickets that need escalation (classification is None), 
e.g.: "5/8 unanimous, 2/8 majority, 1/8 needs escalation (no consensus)"
```

### Debugging and Testing 

The File ran at once

#### Sample Output
```
student@1b4fa25d6d9d:~/lab-04c-consensus-classification$ python scaffold.py 
2/8 unanimous, 4/8 majority, 2/8 needs escalation (no consensus)

--- Consensus-report demonstration (pre-built examples, see README) ---
1/3 unanimous, 1/3 majority, 1/3 needs escalation (no consensus)
student@1b4fa25d6d9d:~/lab-04c-consensus-classification$ 
```

Did Some Manual Check 
Output was also fine.
All Fine.

