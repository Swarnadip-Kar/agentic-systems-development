# LAB 4b - 20-08-2026

### Initial Prompts
```
In 
def get_validated_classification(client, ticket_text):
    raise NotImplementedError
First Implement the the deterministic wrapper: retry with 
the specific validation error fed back to the model,
up to MAX_VALIDATION_ATTEMPTS times, then raise clearly.

Then implement
def classify_batch_deterministic(client, tickets):
    raise NotImplementedError
to run get_validated_classification on entire batch
```

```
Now Implement 
def routing_report(recorded):
group validated tickets by category, 
and
def escalation_export(recorded, out_path="escalation_queue.json"):
flag low-confidence ones for human review instead of auto-routing, and 
export those to a separate JSON file 
```

```
Now implement
def retry_stats_report(recorded):
report how many tickets needed a retry, 
concrete evidence of whether the error-feedback retry is helping.
```

```
In the routing report and escalation report also return the text of 
the ticket and give a heading before printing "Routing Report" 
Also add confidence paramenter in the output of both reports
```

### Debugging and Testing

The File did not run at once
Some Dubugging

Prompt
```
Investigate and explain this
  File "/home/student/lab-04b-deterministic-pipelines/scaffold.py", line 170, in retry_stats_report
    total_attempts = sum(attempts for _, _, attempts in recorded)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/student/lab-04b-deterministic-pipelines/scaffold.py", line 170, in <genexpr>
    total_attempts = sum(attempts for _, _, attempts in recorded)
                                      ^^^^^^^^^^^^^^
ValueError: too many values to unpack (expected 3)
```

and some more debugging..
and some manual debugging also..

Custom Changes

Before
```python
def retry_stats_report(recorded):
    total_attempts = sum(item[2] for item in recorded)
    successful_classifications = sum(1 for item in recorded if item[1] is not None)
```

After 
```python
def retry_stats_report(recorded):
    total_attempts = sum(item[2] for item in recorded)
    successful_classifications = sum(1 for item in recorded if item[1] is not None)
```



After this The code was correct 
Output was also fine

#### Sample Output
```
student@1b4fa25d6d9d:~/lab-04b-deterministic-pipelines$ git commit -m "Manual Debugging"
[main 9aa08b0] Manual Debugging
 1 file changed, 2 insertions(+), 2 deletions(-)
student@1b4fa25d6d9d:~/lab-04b-deterministic-pipelines$ python scaffold.py 
Routing Report:
Category: billing
  Ticket ID: 1, Confidence: 0.95, Reasoning: The ticket mentions an invoice and being quoted, which are typical billing issues., Ticket Text: My invoice this month is double what I was quoted....
  Ticket ID: 8, Confidence: 0.95, Reasoning: The user mentions being charged twice, which is a billing issue., Ticket Text: I was charged twice for the same subscription....
Category: technical
  Ticket ID: 2, Confidence: 0.90, Reasoning: The issue described involves an application crashing, which is typically related to technical problems., Ticket Text: The app crashes every time I open the settings page....
  Ticket ID: 3, Confidence: 0.95, Reasoning: The issue described is related to logging into an account, which falls under technical support., Ticket Text: I can't log in even though I reset my password twice....
  Ticket ID: 6, Confidence: 0.90, Reasoning: The issue pertains to the functionality of a mobile app syncing with a desktop account, which is a technical problem., Ticket Text: The mobile app won't sync with my desktop account....
Category: feature-request
  Ticket ID: 4, Confidence: 0.95, Reasoning: The user is requesting a new feature to export data as CSV., Ticket Text: It would be great if I could export my data as CSV....
  Ticket ID: 7, Confidence: 0.95, Reasoning: The user is requesting the addition of a new feature, specifically dark mode for the dashboard., Ticket Text: Can you add dark mode to the dashboard?...
Category: complaint
  Ticket ID: 5, Confidence: 0.90, Reasoning: The ticket expresses frustration with repeated unresponsive emails from support., Ticket Text: This is the third time support has ignored my email....
Total Tickets Processed: 8
Successful Classifications: 8
Average Attempts per Ticket: 1.00

--- Retry-stats demonstration (synthetic responses, see README) ---
Total Tickets Processed: 3
Successful Classifications: 3
Average Attempts per Ticket: 2.00
student@1b4fa25d6d9d:~/lab-04b-deterministic-pipelines$ 
```


All Fine.

