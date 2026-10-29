# Sunday Lab Test -- 2026-10-11, 10:30 AM, 120 minutes

**Scope: Labs 1 through 7b** -- matches what was announced in class.
Nothing on this test requires anything from Lab 8 or Lab 9.

Six independent questions. Each is its own file -- work in exactly that
file for that question, don't share code between questions. Grading is
entirely offline except where a question explicitly asks you to spend
some of your live-call budget; you have **5 live calls total** for the
whole test (1 on Q2, 3 on Q4, 1 on Q6) -- the shared, pre-paced client
in `live_client.py` is already rate-limited for you, so just import and
use `get_client()` where a question asks for it.

| Question | Topic | Aider | Live calls |
|---|---|---|---|
| Q1 `q1_parse_price.py` | Lab 2 -- parsing model output | **NOT ALLOWED** | 0 |
| Q2 `q2_conversation_state.py` | Lab 3b -- conversation state | **ALLOWED** | 1 |
| Q3 `q3_validate_decision.py` | Lab 4a -- structured output validation | **NOT ALLOWED** | 0 |
| Q4 `q4_consensus.py` | Lab 4c -- consensus classification | **ALLOWED** | 3 |
| Q5 `q5_permissions.py` | Lab 5b -- tool permissions | **NOT ALLOWED** | 0 |
| Q6 `q6_tool_dispatch.py` | Lab 5b/6b -- tool dispatch (native tool calling) | **ALLOWED** | 1 |

Each file's own docstring repeats its Aider status and states the
penalty: **using Aider, or any AI code-generation assistant, on a
NOT ALLOWED question means that question will not be evaluated.**
Gateway usage is logged and checked after the test.
