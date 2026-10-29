# LAB 4a - 18-08-2026

### Initial Prompts
```
scaffold.py tickets_batch.json                                    
> In class TicketClassification(BaseModel): 
>     # TODO(Exercise 1): define the schema. Fields: 
>  
>     DEfine this schema" Classify this support ticket . Respond w
> ith " 
>     " ONLY a JSON object with exactly these fields : " 
>     " category ( one of billing , technical , account , " 
>     " feature - request , complaint ) , confidence (0.0 -1.0) , 
> " 
>     " reasoning ( a short string ) . " 
```

```
Implement system prompt in
In def classify_with_schema(client, ticket_text):
    # TODO(Exercise 2): prompt the model to classify `ticket_text` and
    # return ONLY a JSON object matching TicketClassification's shape
    # (spell out the exact field names and types in the prompt). Call
    # call_with_retry(client, messages) rather than
    # client.chat.completions.create directly, so network failures are
    # already handled at this layer
    Return the raw response text (str) -- do
    # NOT parse/validate here,

    The prompt = "Classify this support ticket . Respond with "
    " ONLY a JSON object with exactly these fields : "
    " category ( one of billing , technical , account , "
    " feature - request , complaint ) , confidence (0.0 -1.0) , "
    " reasoning ( a short string ) . "
```

```
In def validate_classification(raw_response_text):
# TODO(Exercise 3): parse raw_response_text as JSON, then construct
    # a TicketClassification from it. Two distinct failure modes:
    #   - json.JSONDecodeError: the text wasn't valid JSON at all
    #   - pydantic.ValidationError: it parsed as JSON but violates the
    #     schema (wrong category, confidence out of range, etc.)
    # Return (classification, error) -- on success, (classification,
    # None); on failure, (None, a human-readable message describing
    # what went wrong, distinguishing the two failure modes).
```


```
Next implement
def classify_batch_with_validation(client, tickets):
    # TODO(Exercise 4): for every ticket in `tickets`, call
    # classify_with_schema then validate_classification. Additionally
    # require `reasoning` to be non-empty (a schema-valid but
    # empty-string reasoning should count as a failure here -- treat it
    # as an extra check after validate_classification succeeds, not
    # inside the schema itself). Record (ticket["id"], classification,
    # error) for every ticket -- classification is None on failure,
    # error is None on success. After processing all tickets, print a
    # validation success rate, e.g. "6/8 tickets validated successfully
    # (75%)". Return the list of recorded tuples.
```

```
Next Implement
def strict_vs_lenient_report(tickets, strict_failures, lenient_failures):
    # TODO(Exercise 5): given the SAME batch run twice -- once through
    # TicketClassification (strict) and once through
    # LenientTicketClassification (lenient) -- both as lists of
    # (ticket_id, error) tuples for whichever tickets failed under each
    # schema, print a line comparing failure counts and, for any ticket
    # id present in strict_failures but NOT in lenient_failures, print
    # that it was recovered by lenient normalization.
```

### Debugging and Testing

The File ran at once
Output was also fine

```
student@1b4fa25d6d9d:~/lab-04a-structured-outputs$ python scaffold.py 
8/8 tickets validated successfully (100.00%)
Strict failures: 1
Lenient failures: 1
No tickets were recovered by lenient normalization.
```

I tried to give faulty system prompts 

```python
# Extremely vauge system prompt
prompt = ("JSON Object")
```

##### Output
```
student@1b4fa25d6d9d:~/lab-04a-structured-outputs$ python scaffold.py 
0/8 tickets validated successfully (0.00%)
Strict failures: 1
Lenient failures: 1
No tickets were recovered by lenient normalization.
```


#### Manual Logging
I could not see the specific faliures and outputs 
SO added manual logging
```python
    for ticket_id, classification, error in results:             
        print(f"Ticket ID: {ticket_id}")                         
        print(f"Raw Response: {raw_response_text}")              
        if error:                                                
            print(f"Error: {error}")                             
        else:                                                    
            print("Classification:")                             
            print(f"  Category: {classification.category}")      
            print(f"  Confidence: {classification.confidence}")  
            print(f"  Reasoning: {classification.reasoning}")    
        print("-" * 40)  
```

##### Output
```
student@1b4fa25d6d9d:~/lab-04a-structured-outputs$ python scaffold.py 
8/8 tickets validated successfully (100.00%)
Ticket ID: 1
Raw Response: {
  "category": "billing",
  "confidence": 0.9,
  "reasoning": "The issue involves an unexpected charge which is related to billing."
}
Classification:
  Category: billing
  Confidence: 0.9
  Reasoning: The issue involves an amount charged on an invoice, which is related to billing.
----------------------------------------
Ticket ID: 2
Raw Response: {
  "category": "billing",
  "confidence": 0.9,
  "reasoning": "The issue involves an unexpected charge which is related to billing."
}
Classification:
  Category: technical
  Confidence: 0.95
  Reasoning: The issue described is related to the functionality of the app crashing on a specific page, which is a technical problem.
----------------------------------------
Ticket ID: 3
Raw Response: {
  "category": "billing",
  "confidence": 0.9,
  "reasoning": "The issue involves an unexpected charge which is related to billing."
}
Classification:
  Category: technical
  Confidence: 0.9
  Reasoning: The issue involves logging into an account and resetting the password, which is typically a technical problem related to the system's functionality.
----------------------------------------
Ticket ID: 4
Raw Response: {
  "category": "billing",
  "confidence": 0.9,
  "reasoning": "The issue involves an unexpected charge which is related to billing."
}
Classification:
  Category: feature-request
  Confidence: 0.9
  Reasoning: The request is for an additional functionality that the system does not currently offer.
----------------------------------------
Ticket ID: 5
Raw Response: {
  "category": "billing",
  "confidence": 0.9,
  "reasoning": "The issue involves an unexpected charge which is related to billing."
}
Classification:
  Category: complaint
  Confidence: 0.9
  Reasoning: The user mentions multiple instances of ignoring emails, indicating dissatisfaction and a complaint.
----------------------------------------
Ticket ID: 6
Raw Response: {
  "category": "billing",
  "confidence": 0.9,
  "reasoning": "The issue involves an unexpected charge which is related to billing."
}
Classification:
  Category: technical
  Confidence: 0.9
  Reasoning: The issue pertains to the functionality of an application, which falls under technical support.
----------------------------------------
Ticket ID: 7
Raw Response: {
  "category": "billing",
  "confidence": 0.9,
  "reasoning": "The issue involves an unexpected charge which is related to billing."
}
Classification:
  Category: feature-request
  Confidence: 0.9
  Reasoning: The request is for a new feature (dark mode) in an existing product (dashboard).
----------------------------------------
Ticket ID: 8
Raw Response: {
  "category": "billing",
  "confidence": 0.9,
  "reasoning": "The issue involves an unexpected charge which is related to billing."
}
Classification:
  Category: billing
  Confidence: 0.9
  Reasoning: The issue involves an unexpected charge which is related to billing.
----------------------------------------
Strict failures: 1
Lenient failures: 1
No tickets were recovered by lenient normalization.
```

##### Invalid JSON structure Check
Next to trigger invalid JSON structure check I gave a system prompt with wrong structure
```python
# Wrong Structure -> Confidence removed.
    prompt = (
        "Classify this support ticket. Respond with "
        "ONLY a JSON object with exactly these fields: "
        "category (one of billing, technical, account, feature-request, complaint), "
        "reasoning (a short string)."
    )
```

##### Output 
As Expected Validation Error.
```
student@1b4fa25d6d9d:~/lab-04a-structured-outputs$ python scaffold.py 
0/8 tickets validated successfully (0.00%)
Ticket ID: 1
Raw Response: {"category": "billing", "reasoning": "Double charging indicates a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
confidence
  Field required [type=missing, input_value={'category': 'billing', '... their recent invoice.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Ticket ID: 2
Raw Response: {"category": "billing", "reasoning": "Double charging indicates a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
confidence
  Field required [type=missing, input_value={'category': 'technical',... on a specific action.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Ticket ID: 3
Raw Response: {"category": "billing", "reasoning": "Double charging indicates a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
confidence
  Field required [type=missing, input_value={'category': 'technical',... or software problems.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Ticket ID: 4
Raw Response: {"category": "billing", "reasoning": "Double charging indicates a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
confidence
  Field required [type=missing, input_value={'category': 'feature-req...to export data as CSV.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Ticket ID: 5
Raw Response: {"category": "billing", "reasoning": "Double charging indicates a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
confidence
  Field required [type=missing, input_value={'category': 'complaint',...nding to their emails.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Ticket ID: 6
Raw Response: {"category": "billing", "reasoning": "Double charging indicates a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
confidence
  Field required [type=missing, input_value={'category': 'technical',...ation between devices.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Ticket ID: 7
Raw Response: {"category": "billing", "reasoning": "Double charging indicates a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
confidence
  Field required [type=missing, input_value={'category': 'feature-req...ure for the dashboard.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Ticket ID: 8
Raw Response: {"category": "billing", "reasoning": "Double charging indicates a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
confidence
  Field required [type=missing, input_value={'category': 'billing', '...cates a billing issue.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Strict failures: 1
Lenient failures: 1
No tickets were recovered by lenient normalization.
```


##### Not a JSON Object Check

Modified System Prompt to
```python
# Wrong Structure -> Not a JSON Object
    prompt = (
        "Classify this support ticket. Respond with "
        "with exactly these fields: "
        "category (one of billing, technical, account, feature-request, complaint), "
    )
```

##### Output
Expected and Got JSON Error
```
student@1b4fa25d6d9d:~/lab-04a-structured-outputs$ python scaffold.py 
0/8 tickets validated successfully (0.00%)
Ticket ID: 1
Raw Response: category: billing
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
----------------------------------------
Ticket ID: 2
Raw Response: category: billing
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
----------------------------------------
Ticket ID: 3
Raw Response: category: billing
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
----------------------------------------
Ticket ID: 4
Raw Response: category: billing
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
----------------------------------------
Ticket ID: 5
Raw Response: category: billing
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
----------------------------------------
Ticket ID: 6
Raw Response: category: billing
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
----------------------------------------
Ticket ID: 7
Raw Response: category: billing
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
----------------------------------------
Ticket ID: 8
Raw Response: category: billing
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
----------------------------------------
Strict failures: 1
Lenient failures: 1
No tickets were recovered by lenient normalization.
```

## Conclusion 
With correct System prompt and checks we can avoid faliures.
All works as expected.

### Sample Respose 

```
student@1b4fa25d6d9d:~/lab-04a-structured-outputs$ python scaffold.py 
7/8 tickets validated successfully (87.50%)
Ticket ID: 1
Raw Response: {"category": "billing", "confidence": 0.95, "reasoning": "User reports double charging, which is a billing issue."}
Classification:
  Category: billing
  Confidence: 0.9
  Reasoning: The customer mentions an unexpected increase in their monthly invoice compared to the quote they received.
----------------------------------------
Ticket ID: 2
Raw Response: {"category": "billing", "confidence": 0.95, "reasoning": "User reports double charging, which is a billing issue."}
Classification:
  Category: technical
  Confidence: 0.9
  Reasoning: The issue described is related to the application's functionality and performance.
----------------------------------------
Ticket ID: 3
Raw Response: {"category": "billing", "confidence": 0.95, "reasoning": "User reports double charging, which is a billing issue."}
Classification:
  Category: technical
  Confidence: 0.95
  Reasoning: The user is experiencing an issue logging in, which is typically a technical problem.
----------------------------------------
Ticket ID: 4
Raw Response: {"category": "billing", "confidence": 0.95, "reasoning": "User reports double charging, which is a billing issue."}
Classification:
  Category: feature-request
  Confidence: 1.0
  Reasoning: The user is requesting a new feature to export data as CSV.
----------------------------------------
Ticket ID: 5
Raw Response: {"category": "billing", "confidence": 0.95, "reasoning": "User reports double charging, which is a billing issue."}
Classification:
  Category: complaint
  Confidence: 0.95
  Reasoning: User expresses frustration with repeated ignored emails.
----------------------------------------
Ticket ID: 6
Raw Response: {"category": "billing", "confidence": 0.95, "reasoning": "User reports double charging, which is a billing issue."}
Classification:
  Category: technical
  Confidence: 0.9
  Reasoning: The issue pertains to the functionality of an application and its integration with another service.
----------------------------------------
Ticket ID: 7
Raw Response: {"category": "billing", "confidence": 0.95, "reasoning": "User reports double charging, which is a billing issue."}
Error: Validation error: 1 validation error for TicketClassification
reasoning
  Field required [type=missing, input_value={'category': 'feature-req...ode for the dashboard.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/missing
----------------------------------------
Ticket ID: 8
Raw Response: {"category": "billing", "confidence": 0.95, "reasoning": "User reports double charging, which is a billing issue."}
Classification:
  Category: billing
  Confidence: 0.95
  Reasoning: User reports double charging, which is a billing issue.
----------------------------------------
Strict failures: 1
Lenient failures: 1
No tickets were recovered by lenient normalization.
```


