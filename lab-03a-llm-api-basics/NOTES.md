# LAB 3a - 11-08-2026

## 1. get_client -- construct the API client.

### Code
```python
def get_client():
    client = OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
    )
    return client
```

### Test Output
```
student@1b4fa25d6d9d:~/lab-03a-llm-api-basics$ python -c "from scaffold import get_client; print(get_client())"
<openai.OpenAI object at 0x7f021c3114f0>
```


## 2. classify_ticket -- make the raw request/response call.

### Code
```python
def classify_ticket(client, ticket_text):
    response = client.chat.completions.create(
        model="main",
        messages=[
            {"role": "system", "content": "Based on the Request Reply with only one of the allowed catagory words nothing else: billing, technical, account, feature-request, complaint"},
            {"role": "user", "content": ticket_text},
        ],
    )
    return response
```

### Test Output
```
student@1b4fa25d6d9d:~/lab-03a-llm-api-basics$ python
Python 3.12.3 (main, Jun 19 2026, 12:46:00) [GCC 13.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> ticket_text = "I have accidentlay paid 10000 instead of 1000. Need a refund"
>>> from scaffold import get_client;
>>> from scaffold import classify_ticket;
>>> print(classify_ticket(get_client(), ticket_text))
ChatCompletion(id='chatcmpl-a25b8eb82e85d551', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='billing', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None, provider_specific_fields={'refusal': None, 'reasoning': None}), provider_specific_fields={'routed_experts': None, 'stop_reason': None, 'token_ids': None})], created=1786442572, model='main', object='chat.completion', service_tier=None, system_fingerprint='vllm-0.25.1-1acda35a', usage=CompletionUsage(completion_tokens=2, prompt_tokens=63, total_tokens=65, completion_tokens_details=None, prompt_tokens_details=None))
>>> 
```

## 3. extract_category 
parse the category out of the response. Some tickets get the model to hedge or explain rather than answer with a bare word (e.g. "I'd say this is billing, though it's technical too") -- a plain equality check will fail on these; you need to search the response text for whichever ALLOWED_CATEGORIES word appears.

### Code
```python
def extract_category(response):
    if not response.choices:
        raise RuntimeError("empty choices in response")

    text = response.choices[0].message.content.strip().lower()

    # Find the first occurrence (by position in the string) of any
    # allowed category word/phrase, rather than requiring the whole
    # response to equal one exactly.
    best_pos = None
    best_category = None
    for category in ALLOWED_CATEGORIES:
        pos = text.find(category.lower())
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos = pos
            best_category = category

    return best_category  # None if no category word appears
```

### Test Output
```
student@1b4fa25d6d9d:~/lab-03a-llm-api-basics$ python
Python 3.12.3 (main, Jun 19 2026, 12:46:00) [GCC 13.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from scaffold import get_client;
>>> from scaffold import classify_ticket;
>>> from scaffold import extract_category;
>>> ticket_text = "I have accidentlay paid 10000 instead of 1000. Need a refund"
>>> print(extract_category(classify_ticket(get_client(), ticket_text)))
billing
>>> 
```

## 4. classify_ticket_safely
handle empty input, malformed responses, and real openai SDK errors (RateLimitError, APITimeoutError, APIError) without crashing.

### Code
```python
def classify_ticket_safely(client, ticket_text):
    if not ticket_text:
        return None

    try:
        response = classify_ticket(client, ticket_text)
    except (RateLimitError, APITimeoutError, APIError):
        return None

    if not response.choices:
        return None

    return extract_category(response)
```

### Test Output
```
student@1b4fa25d6d9d:~/lab-03a-llm-api-basics$ python
Python 3.12.3 (main, Jun 19 2026, 12:46:00) [GCC 13.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from scaffold import get_client;
>>> from scaffold import classify_ticket_safely;
>>> ticket_text = "I have accidentaly paid 10000 instead of 1000. Need a refund"
>>> print(classify_ticket_safely(get_client(), ticket_text))
billing
>>> 
```

## 5. suggest_next_action
ask the model for a next-action suggestion. No grading weight beyond attempting it; a preview of Week 5.

### Code
```python
def suggest_next_action(client, ticket_text):
    if not ticket_text:
        return None

    try:
        response = client.chat.completions.create(
            model="main",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a support triage assistant. Given a "
                        "customer ticket, respond with ONE short next "
                        "action (a few words), e.g. 'escalate to billing "
                        "team' or 'request order number'. No explanation."
                    ),
                },
                {"role": "user", "content": ticket_text},
            ],
        )
    except (RateLimitError, APITimeoutError, APIError):
        return None

    if not response.choices:
        return None

    return response.choices[0].message.content.strip()
```

### Test Output
```
student@1b4fa25d6d9d:~/lab-03a-llm-api-basics$ python
Python 3.12.3 (main, Jun 19 2026, 12:46:00) [GCC 13.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from scaffold import get_client;
>>> from scaffold import suggest_next_action;
>>> ticket_text = "I have accidentaly paid 10000 instead of 1000. Need a refund"
>>> print(suggest_next_action(get_client(), ticket_text))
Request transaction details.
>>> 
```


## Test Case Generation

First Asked it to generate test cases.
Then after some debugging.. it was failing on some.

### Main Prompt
To fix the persistent error - provide the structure of the dictionary.
```
Based on thid dummy prompt sturecture
 print(classify_ticket(get_client(), ticket_text))
ChatCompletion(id='chatcmpl-a25b8eb82e85d551', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='billing', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None, provider_specific_fields={'refusal': None, 'reasoning': None}), provider_specific_fields={'routed_experts': None, 'stop_reason': None, 'token_ids': None})], created=1786442572, model='main', object='chat.completion', service_tier=None, system_fingerprint='vllm-0.25.1-1acda35a', usage=CompletionUsage(completion_tokens=2, prompt_tokens=63, total_tokens=65, completion_tokens_details=None, prompt_tokens_details=None))

Fix the errors
scaffold.py:112: AttributeError
==================== short test summary info =====================
FAILED test_scaffold.py::TestScaffold::test_classify_ticket_safely_with_valid_response - AttributeError: 'dict' object has no attribute 'message'
FAILED test_scaffold.py::TestScaffold::test_extract_category - AttributeError: 'dict' object has no attribute 'message'
FAILED test_scaffold.py::TestScaffold::test_suggest_next_action_with_valid_response - AttributeError: 'dict' object has no attribute 'message'
================== 3 failed, 5 passed in 1.07s ===================
```


## 6 REPORT.md 
See Report.md file