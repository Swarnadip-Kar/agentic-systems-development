# LAB 3b - 13-08-2026

## Part 1: Implementation

### Prompt 1
```diff
> see scaffold_old.py as reference. we will implement the TODO mar
> lers in the scaffold.py file one by one -> For the first one def
>  call_with_retry(client, messages): 
>     # TODO(Exercise 1): call client.chat.completions.create with
>  model="main", 
>     # catching RateLimitError and APIError. Retry up to MAX_ATTE
> MPTS times with 
>     # exponential backoff (time.sleep(2 ** attempt) between atte
> mpts). 
>     # Re-raise on the final failed attempt. -> Clealy state assu
> mptions and edge cases considered.                              

Certainly! Let's implement the call_with_retry function according 
to the requirements. Here are the assumptions and edge cases      
considered:                                                       

Assumptions:                                                      

 1 The client object has a method chat.completions.create that    
   takes model and messages as parameters.                        
 2 The RateLimitError and APIError exceptions are raised by the   
   client.chat.completions.create method.                         
 3 The MAX_ATTEMPTS constant is defined and specifies the maximum 
   number of retry attempts.                                      
 4 Exponential backoff is implemented using time.sleep(2 **       
   attempt) where attempt is the current attempt number starting  
   from 0.                                                        

Edge Cases Considered:                                            

 1 If the API call succeeds on the first attempt.                 
 2 If the API call fails on the first attempt and needs to be     
   retried.                                                       
 3 If the API call fails multiple times but succeeds before       
   reaching MAX_ATTEMPTS.                                         
 4 If the API call fails MAX_ATTEMPTS times and the exception is  
   re-raised.                                                     

Here is the updated scaffold.py file with the call_with_retry     
function implemented:                                             

scaffold.py                                                       

                                                                  
@@ -1,2 +1,3 @@                                                   
 import math                                                      
 from openai import OpenAI, APIError, RateLimitError              
                                                                  
                                                                  
 def call_with_retry(client, messages):                           
+    attempt = 0                                                  
+    while attempt < MAX_ATTEMPTS:                                
+        try:                                                     
+            response =                                           
client.chat.completions.create(model="main", messages=messages)   
+            return response                                      
-    # Re-raise on the final failed attempt.                      
-    raise NotImplementedError                                    
+    attempt = 0                                                  
+    while attempt < MAX_ATTEMPTS:                                
+        try:                                                     
+            response =                                           
client.chat.completions.create(model="main", messages=messages)   
+            return response                                      
+        except (RateLimitError, APIError) as e:                  
+            if attempt == MAX_ATTEMPTS - 1:                      
+                raise e                                          
+            time.sleep(2 ** attempt)                             
+            attempt += 1                                         
                                                                  
                                                                  
 def classify_batch(client, tickets, trim_fn=None):               
     # TODO(Exercise 2): process every ticket in `tickets` in ONE 
growing                                                           
     # conversation -- append each ticket as a user message to a  
shared                                                            
     # `history` list, call call_with_retry(client, history),     
append the                                                        
     # model's reply as an assistant message, and record          
     # (ticket["id"], category, len(history),                     
response.usage.total_tokens)                                      
message                                                           
can                                                               
     # ignore total_tokens here -- Exercise 4 uses it), then print
a                                                                 
     # final line connecting the growth to the Lab 2 bottleneck,  
e.g.:                                                             
+  67 / 131 lines [███████████████░░░░░░░░░░░░░░░]  51%           
                                                                  

Tokens: 3.1k sent, 1.7k received.
Applied edit to scaffold.py
Commit 567d38d feat(scaffold.py): Implement `call_with_retry` 
function with exponential backoff and error handling
You can use /undo to undo and discard each aider commit.
──────────────────────────────────────────────────────────────────
scaffold.py scaffold_old.py 
```

### Prompt 2

```diff
>     # model's reply as an assistant message, and record 
>     # (ticket["id"], category, len(history), response.usage.tota
> l_tokens) 
>     # for every ticket. `response.usage.total_tokens` is the rea
> l API's 
>     # own token count for that call -- no separate tokenizer nee
> ded. 
>     # Return the list of recorded tuples. 
>  
>     # `trim_fn` is used by Exercise 5 (see enforce_budget below)
>  -- when 
>     # it is not None, call trim_fn(history, MAX_CONTEXT_TOKENS, 
>     # running_tokens) BEFORE appending each new ticket's user me
> ssage 
>     # (running_tokens is 0 for the first ticket, then the previo
> us 
>     # ticket's total_tokens after that), and use its return valu
> e as the 
>     # new `history`. When trim_fn is None (Exercises 1-3), skip 
> this 
>     # entirely -- history grows unbounded, exactly as before.   

scaffold.py                                                       

                                                                  
@@ -1,2 +1,3 @@                                                   
 """Lab 3b: conversation state and retries, aider-assisted --     
build on                                                          
 what you wrote by hand in Lab 3a. Use aider freely here; the     
point of                                                          
 def classify_batch(client, tickets, trim_fn=None):               
-    # TODO(Exercise 2): process every ticket in `tickets` in ONE 
growing                                                           
-    # conversation -- append each ticket as a user message to a  
shared                                                            
-    # `history` list, call call_with_retry(client, history),     
append the                                                        
-    # model's reply as an assistant message, and record          
-    # (ticket["id"], category, len(history),                     
response.usage.total_tokens)                                      
-    # for every ticket. `response.usage.total_tokens` is the real
API's                                                             
-    # own token count for that call -- no separate tokenizer     
needed.                                                           
-    # Return the list of recorded tuples.                        
-    #                                                            
-    # `trim_fn` is used by Exercise 5 (see enforce_budget below) 
-- when                                                           
-    # it is not None, call trim_fn(history, MAX_CONTEXT_TOKENS,  
-    # running_tokens) BEFORE appending each new ticket's user    
message                                                           
-    # (running_tokens is 0 for the first ticket, then the        
previous                                                          
-    # ticket's total_tokens after that), and use its return value
as the                                                            
-    # new `history`. When trim_fn is None (Exercises 1-3), skip  
this                                                              
-    # entirely -- history grows unbounded, exactly as before.    
-    raise NotImplementedError                                    
+    history = []                                                 
+    recorded = []                                                
+    running_tokens = 0                                           
                                                                  
+    for ticket in tickets:                                       
+        if trim_fn is not None:                                  
+            history = trim_fn(history, MAX_CONTEXT_TOKENS,       
running_tokens)                                                   
                                                                  
-def token_growth_report(recorded):                               
-    # TODO(Exercise 3, tie-back): given the list of (id,         
category,                                                         
-    # history_length, total_tokens) tuples from classify_batch,  
print                                                             
-    # one line per ticket showing how history_length grows (you  
can                                                               
-    # ignore total_tokens here -- Exercise 4 uses it), then print
a                                                                 
-    # final line connecting the growth to the Lab 2 bottleneck,  
e.g.:                                                             
-    # "history grew from N to M messages across this batch --    
this is                                                           
-    # the same growth that filled the context window in Lab 2."  
-    raise NotImplementedError                                    
+        history.append({"role": "user", "content":               
ticket["text"]})                                                  
                                                                  
+        response = call_with_retry(client, history)              
+        running_tokens = response.usage.total_tokens             
                                                                  
-def check_budget(recorded):                                      
-    # TODO(Exercise 4): given the list of (id, category,         
history_length,                                                   
-    # total_tokens) tuples from classify_batch, find the first   
ticket                                                            
-    # whose total_tokens exceeds MAX_CONTEXT_TOKENS. Print a line
-    # reporting which ticket (if any) first crossed the budget,  
e.g.:                                                             
-    # "ticket 6 pushed the conversation to 338 tokens, over the  
300                                                               
-    # token budget -- this is the same growth that filled the    
context                                                           
-    # window in Lab 2, now happening fast enough to matter in one
batch."                                                           
-    # Return that ticket's id, or None if the budget was never   
+    text =                                                       
response.choices[0]['message']['content'].strip().lower()         
                                                                  
+    # Find the first occurrence (by position in the string) of   
any                                                               
+    # allowed category word/phrase, rather than requiring the    
whole                                                             
+    # response to equal one exactly.                             
+    best_pos = None                                              
+    best_category = None                                         
e.g.:                                                             
-    # "ticket 6 pushed the conversation to 338 tokens, over the  
300                                                               
-    # token budget -- this is the same growth that filled the    
context                                                           
-    # window in Lab 2, now happening fast enough to matter in one
batch."                                                           
-    # Return that ticket's id, or None if the budget was never   
exceeded.                                                         
-    raise NotImplementedError                                    
+    # Find the first occurrence (by position in the string) of   
any                                                               
+    # allowed category word/phrase, rather than requiring the    
whole                                                             
+    # response to equal one exactly.                             
+    best_pos = None                                              
+    best_category = None                                         
+    for category in ALLOWED_CATEGORIES:                          
+        pos = text.find(category.lower())                        
+        if pos != -1 and (best_pos is None or pos < best_pos):   
+            best_pos = pos                                       
+            best_category = category                             
                                                                  
+  88 / 136 lines [███████████████████░░░░░░░░░░░]  65%           
                                                                  

Tokens: 5.1k sent, 1.5k received.
Applied edit to scaffold.py
Commit fd40b14 feat(scaffold.py): Implement initial classification
logic for batch processing
```


### Prompt 3

```
> Next def token_growth_report(recorded): 
>     # TODO(Exercise 3, tie-back): given the list of (id, categor
> y, 
>     # history_length, total_tokens) tuples from classify_batch, 
> print 
>     # one line per ticket showing how history_length grows (you 
> can 
>     # ignore total_tokens here -- Exercise 4 uses it), then prin
> t a 
>     # final line connecting the growth to the Lab 2 bottleneck, 
> e.g.: 
>     # "history grew from N to M messages across this batch -- th
> is is 
>     # the same growth that filled the context window in Lab 2." 

scaffold.py                                                       

                                                                  
@@ -1,2 +1,3 @@                                                   
 """Lab 3b: conversation state and retries, aider-assisted --     
build on                                                          
 this session is automating what you understood by writing it     
                                                                  
 def token_growth_report(recorded):                               
-    # TODO(Exercise 3, tie-back): given the list of (id,         
category,                                                         
-    # history_length, total_tokens) tuples from classify_batch,  
print                                                             
-    # one line per ticket showing how history_length grows (you  
can                                                               
-    # ignore total_tokens here -- Exercise 4 uses it), then print
a                                                                 
-    # final line connecting the growth to the Lab 2 bottleneck,  
e.g.:                                                             
-    # "history grew from N to M messages across this batch --    
this is                                                           
-    # the same growth that filled the context window in Lab 2."  
-    raise NotImplementedError                                    
+    history_lengths = [record[2] for record in recorded]         
+    start_length = history_lengths[0]                            
+    end_length = history_lengths[-1]                             
+                                                                 
+    print(f"history grew from {start_length} to {end_length}     
messages across this batch -- this is the same growth that filled 
the context window in Lab 2.")                                    
                                                                  
                                                                  
 def check_budget(recorded):                                      
     # TODO(Exercise 4): given the list of (id, category,         
history_length,                                                   
     # total_tokens) tuples from classify_batch, find the first   
ticket                                                            
     # whose total_tokens exceeds MAX_CONTEXT_TOKENS. Print a line
     # reporting which ticket (if any) first crossed the budget,  
e.g.:                                                             
     # "ticket 6 pushed the conversation to 338 tokens, over the  
300                                                               
2), use                                                           
message,                                                          
     # and splice that in place of what it summarized. Keep the   
most                                                              
     # recent `keep_recent` messages untouched. This is closer to 
what                                                              
+ 133 / 159 lines [█████████████████████████░░░░░]  84%           
                                                                  

Tokens: 8.4k sent, 1.4k received.
Applied edit to scaffold.py
Commit 9294873 fix: implement token_growth_report function
You can use /undo to undo and discard each aider commit.
```


### Prompt 4

```
> For the next part implement 
> def check_budget(recorded): 
>     # TODO(Exercise 4): given the list of (id, category, history
> _length, 
>     # total_tokens) tuples from classify_batch, find the first t
> icket 
>     # whose total_tokens exceeds MAX_CONTEXT_TOKENS. Print a lin
> e 
>     # reporting which ticket (if any) first crossed the budget, 
> e.g.: 
>     # "ticket 6 pushed the conversation to 338 tokens, over the 
> 300 
>     # token budget -- this is the same growth that filled the co
> ntext 
>     # window in Lab 2, now happening fast enough to matter in on
> e batch." 
>     # Return that ticket's id, or None if the budget was never e
> xceeded. 
>     raise NotImplementedError                                   

scaffold.py                                                       

                                                                  
@@ -1,2 +1,3 @@                                                   
 """Lab 3b: conversation state and retries, aider-assisted --     
build on                                                          
 what you wrote by hand in Lab 3a. Use aider freely here; the     
point of                                                          
                                                                  
                                                                  
 def check_budget(recorded):                                      
+    for record in recorded:                                      
+        ticket_id, category, history_length, total_tokens =      
record                                                            
+        if total_tokens > MAX_CONTEXT_TOKENS:                    
-    # whose total_tokens exceeds MAX_CONTEXT_TOKENS. Print a line
-    # reporting which ticket (if any) first crossed the budget,  
e.g.:                                                             
-    # "ticket 6 pushed the conversation to 338 tokens, over the  
300                                                               
-    # token budget -- this is the same growth that filled the    
context                                                           
-    # window in Lab 2, now happening fast enough to matter in one
batch."                                                           
-    # Return that ticket's id, or None if the budget was never   
exceeded.                                                         
-    raise NotImplementedError                                    
+    for record in recorded:                                      
+        ticket_id, category, history_length, total_tokens =      
record                                                            
+        if total_tokens > MAX_CONTEXT_TOKENS:                    
+            print(f"ticket {ticket_id} pushed the conversation to
{total_tokens} tokens, over the {MAX_CONTEXT_TOKENS} token budget 
-- this is the same growth that filled the context window in Lab  
2, now happening fast enough to matter in one batch.")            
+            return ticket_id                                     
+    return None                                                  
                                                                  
                                                                  
 def enforce_budget(history, max_tokens, current_tokens):         
     # TODO(Exercise 5): if current_tokens <= max_tokens, return  
history                                                           
     # unchanged. Otherwise, estimate the average token cost per  
     # user/assistant pair as current_tokens / (len(history) //   
2), use                                                           
     # that to estimate how many of the OLDEST pairs to drop to   
get back                                                          
avg_per_pair)),                                                   
model                                                             
message,                                                          
     # and splice that in place of what it summarized. Keep the   
most                                                              
     # recent `keep_recent` messages untouched. This is closer to 
what                                                              
+ 130 / 157 lines [████████████████████████░░░░░░]  83%           
                                                                  

Tokens: 9.9k sent, 1.4k received.
Committing scaffold.py before applying edits.
Commit 650da87 chore: add debug print statement in main function
Applied edit to scaffold.py
Commit 01c9dcf fix(scaffold.py): implement check_budget function
```

### Prompt 5

```
scaffold.py scaffold_old.py                                       
> def enforce_budget(history, max_tokens, current_tokens): 
>     # TODO(Exercise 5): if current_tokens <= max_tokens, return 
> history 
>     # unchanged. Otherwise, estimate the average token cost per 
>     # user/assistant pair as current_tokens / (len(history) // 2
> ), use 
>     # that to estimate how many of the OLDEST pairs to drop to g
> et back 
>     # under budget (math.ceil((current_tokens - max_tokens) / av
> g_per_pair)), 
>     # and drop that many oldest pairs -- but never drop the last
>  
>     # remaining pair, even if the estimate says to. Return the 
>     # (possibly trimmed) history list. There's no tokenizer avai
> lable to 
>     # measure exact per-message cost, so this is an estimate, no
> t an 
>     # exact count -- the batch may stabilize slightly over budge
> t rather 
>     # than strictly under it, and that's expected. 
>     raise NotImplementedError                                   

scaffold.py                                                       

                                                                  
@@ -1,2 +1,3 @@                                                   
 """Lab 3b: conversation state and retries, aider-assisted --     
build on                                                          
 what you wrote by hand in Lab 3a. Use aider freely here; the     
     # default (2 retries), which would silently swallow the      
             print(f"ticket {ticket_id} pushed the conversation to
-    # TODO(Exercise 5): if current_tokens <= max_tokens, return  
history                                                           
-    # unchanged. Otherwise, estimate the average token cost per  
-    # user/assistant pair as current_tokens / (len(history) //   
2), use                                                           
-    # that to estimate how many of the OLDEST pairs to drop to   
get back                                                          
-    # under budget (math.ceil((current_tokens - max_tokens) /    
avg_per_pair)),                                                   
-    # and drop that many oldest pairs -- but never drop the last 
-    # remaining pair, even if the estimate says to. Return the   
-    # (possibly trimmed) history list. There's no tokenizer      
available to                                                      
-    # measure exact per-message cost, so this is an estimate, not
an                                                                
-    # exact count -- the batch may stabilize slightly over budget
rather                                                            
-    # than strictly under it, and that's expected.               
-    raise NotImplementedError                                    
+    if current_tokens <= max_tokens:                             
+        return history                                           
                                                                  
+    num_pairs = len(history) // 2                                
+    if num_pairs <= 1:                                           
+        return history  # Never drop the last remaining pair     
                                                                  
-def summarize_and_replace(history, client, keep_recent=2):       
-    # BONUS (ungraded, optional): if you have time left, try a   
more                                                              
-    # realistic mitigation than dropping messages -- ask the     
model                                                             
-    # itself to summarize the oldest turns into one condensed    
message,                                                          
-    # and splice that in place of what it summarized. Keep the   
most                                                              
-    # recent `keep_recent` messages untouched. This is closer to 
what                                                              
-    # production systems do; there's no single correct summary,  
so this                                                           
-    # part isn't graded -- try it and see how the behavior       
differs from                                                      
-    # enforce_budget's straightforward truncation. Not wired into
-    # classify_batch by default -- pass                          
trim_fn=summarize_and_replace                                     
-    # manually if you want to see it run end to end (note its    
signature                                                         
-    # differs from enforce_budget's: it needs `client` to make   
the                                                               
-    # summarization call, so you'll need a small wrapper, e.g.   
-    # `lambda h, mx, cur: summarize_and_replace(h, client,       
keep_recent=2)`).                                                 
-    raise NotImplementedError                                    
+    avg_per_pair = current_tokens / num_pairs                    
+    pairs_to_drop = math.ceil((current_tokens - max_tokens) /    
avg_per_pair)                                                     
                                                                  
                                                                  
 if __name__ == "__main__":                                       
     main()                                                       
                                                                  


Tokens: 11k sent, 1.3k received.
Applied edit to scaffold.py
Commit 4dec272 fix: implement enforce_budget function and update 
main to use it correctly
```



## Part 2: Testing

Sample Output after lot of dubugging.
All Working well.
```
student@1b4fa25d6d9d:~/lab-03b-conversation-state$ python scaffold.py 
Starting main function...
Client obtained
Tickets loaded
Processing ticket 1
Ticket 1 categorized as billing
History length after appending: 2
Processing ticket 2
Ticket 2 categorized as technical
History length after appending: 4
Processing ticket 3
Ticket 3 categorized as technical
History length after appending: 6
Processing ticket 4
Ticket 4 categorized as feature-request
History length after appending: 8
Processing ticket 5
Ticket 5 categorized as complaint
History length after appending: 10
Processing ticket 6
Ticket 6 categorized as technical
History length after appending: 12
Processing ticket 7
Ticket 7 categorized as feature-request
History length after appending: 14
Processing ticket 8
Ticket 8 categorized as billing
History length after appending: 16
Batch classified
history grew from 2 to 16 messages across this batch
ticket 1 pushed the conversation to 54 tokens, over the 30 token budget.
Processing ticket 1
Ticket 1 categorized as billing
History length after appending: 2
Processing ticket 2
Ticket 2 categorized as technical
History length after appending: 4
Dropping 2 oldest pairs from history. Ticket IDs: ['My invoice this month is double what I was quoted.']
Processing ticket 3
Ticket 3 categorized as technical
History length after appending: 4
Dropping 2 oldest pairs from history. Ticket IDs: ['The app crashes every time I open the settings page.']
Processing ticket 4
Ticket 4 categorized as feature-request
History length after appending: 4
Dropping 2 oldest pairs from history. Ticket IDs: ["I can't log in even though I reset my password twice."]
Processing ticket 5
Ticket 5 categorized as complaint
History length after appending: 4
Dropping 2 oldest pairs from history. Ticket IDs: ['It would be great if I could export my data as CSV.']
Processing ticket 6
Ticket 6 categorized as technical
History length after appending: 4
Dropping 2 oldest pairs from history. Ticket IDs: ['This is the third time support has ignored my email.']
Processing ticket 7
Ticket 7 categorized as feature-request
History length after appending: 4
Dropping 2 oldest pairs from history. Ticket IDs: ["The mobile app won't sync with my desktop account."]
Processing ticket 8
Ticket 8 categorized as billing
History length after appending: 4
history grew from 2 to 4 messages across this batch
Main function completed successfully
```