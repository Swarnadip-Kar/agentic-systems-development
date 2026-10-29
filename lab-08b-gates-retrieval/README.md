# Lab 8b: Approval Gates and Retrieval

Builds directly on Lab 8a and Week 8's lecture. Lab 8a's planner pieces
(`build_plan_schema`, `cut_before_unobserved_writes`, `execute_until_stuck`,
and `plan_decision`, which makes one planning call) are given as finished
code, along with everything Lab 8a gave you. `aider` is available for this
session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` and `temperature=0`. As in Lab 8a, wrap
clients in the given `CountingClient` to stay under the gateway's 30 calls a
minute.

## A map of the code

`call-flow.pdf` in this repo draws what `python3 scaffold.py` runs and who
calls whom, one round of the gated step, the gate over a whole run, inside
`retrieve`, the two ways of answering from the runbook, and how synonym
expansion feeds the hit rate. Keep it open while you work.

## Two problems from the lecture

**Writes need a person.** In the lecture, a reviewer denied the planner's
escalations and told it not to propose them again. It proposed them again
anyway. A rule you *ask* the model to follow is a suggestion; the gate has to
be code.

**Retrieval can miss.** Asked *"How long can a customer wait before somebody
first gets back to them?"*, keyword search missed the article that answers it
("First response within 1 day"), because the question and the article use
different words. The fixed workflow answered "not covered"; the agent
guessed. Neither fixed the miss.

`runbook.json` holds eight short policy articles. `questions.json` holds
twelve questions, each with the id of the article that answers it.

## Exercises

1. **`make_gated_step(client, registry, granted_permissions, approver)`** --
   return a step function for the Week 7 harness. Its state is
   `{"task": str, "observations": list, "denied": list}`, as made by
   `gated_initial_state`. `approver(writes)` is called with a list of write
   steps and returns `True` to allow them. Each round:
   - Call `plan_decision(state, client, registry)` once. If `done` is true,
     return `(state, True, "planner: done")`.
   - Apply `cut_before_unobserved_writes` to its steps. If nothing is left,
     add `{"not_run": "anything", "why": "You said the task is not done but
     planned no steps."}` as in Lab 8a.
   - Collect the plan's write steps (the given `is_write`). If there are
     none, run the plan with `execute_until_stuck`.
   - If there are writes, make a key with `json.dumps(writes,
     sort_keys=True)`.
     - If that key is already in `state["denied"]`, **do not call the
       approver**. Add `{"not_run": "writes", "why": "These writes were
       already denied by a human reviewer. Do not propose them again."}`.
     - Otherwise call `approver(writes)` exactly once. If it returns `False`,
       add `{"not_run": "writes", "why": "A human reviewer denied these
       writes. Do not propose them again."}` and add the key to `denied`.
     - If it returns `True`, run the plan with `execute_until_stuck`.
   - Return the new state, `False`, and the list of new observations. Never
     modify the state you were given; `denied` in the new state is a new
     list.

2. **`retrieve(query, k=2)`** -- keyword retrieval over `RUNBOOK`. Score each
   article by how many of the given `tokens(query)` also appear in
   `tokens(article_text)`. Sort by score, highest first, breaking ties by
   article id in alphabetical order. Return up to `k` ids, leaving out any
   article that scored 0.

3. **`retrieve_then_answer(question, client, retriever=retrieve)`** -- the
   fixed workflow. Call `retriever(question)`. If it returns nothing, return
   `([], NOT_COVERED)` **without calling the model**: there is nothing to
   ground an answer in, so the code decides. Otherwise make one call with
   `model="main"`, `temperature=0`, and
   `messages=answer_messages(question, doc_ids)`, and return
   `(doc_ids, <the reply's content>)`.

4. **Retrieval as a tool.**
   - **`build_runbook_registry(retriever=retrieve)`** -- a registry with one
     tool, `"search_runbook"`: a non-empty description, parameters taking a
     required string `query`, permission `"read"`, and an `fn` that returns
     `[{"id": d, "text": RUNBOOK[d]} for d in retriever(query)]`.
   - **`answer_with_search_tool(question, client, retriever=retrieve,
     trace_path="trace_search.jsonl")`** -- run the given `react_step` with
     that registry and `{"read"}` under a `RuntimeHarness` with `max_steps=6`
     and this `trace_path` (start the file empty), from
     `retrieval_agent_state(question)`. Return `(searches, answer)`:
     `searches` lists `(query, [ids])` for every `search_runbook` call in the
     trace, in order; `answer` is the harness's `output` if its status is
     `"done"`, otherwise `None`.

5. **Close the vocabulary gap.**
   - **`expand_query(query, synonyms=SYNONYMS)`** -- for each word of the
     query, in order (lowercase, `[a-z0-9]+`), add that word's synonyms from
     the dictionary. Return the query followed by a space and the added
     words separated by spaces, or the query unchanged if nothing was added.
   - **`hit_rate(questions, retriever)`** -- return `(hits, total)`, where a
     question is a hit if its `expected` id is in `retriever(question)`.
   - **Fill in `SYNONYMS`** so that `retrieve_expanded` answers more
     questions than `retrieve` does, without losing any that `retrieve`
     already answered. Keys are words a person might say; values are the
     words the runbook uses.

   The graders also check your `SYNONYMS` on questions you have not seen.
   A table written only for the twelve questions here will fail that check.
   Write synonyms that are true in general ("money" and "refund"), not
   patches for one sentence. Some misses cannot be fixed with synonyms alone;
   when you find one, look at which other article it ties with, and why.

Run `python3 scaffold.py` to see the hit rates before and after your
synonyms, both answering styles, the search agent with plain and expanded
retrieval, and the approval gate with a reviewer who denies everything and
one who approves everything. Things to look for in the output and traces:

- The agent chooses its own search words. Compare them with the article
  text. If a search finds nothing, what does the agent say anyway?
- With the reviewer who denies everything, count how often the reviewer is
  asked, and how the run ends. A planner that keeps proposing the same denied
  writes is stopped by the harness's round limit, not by good sense.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
