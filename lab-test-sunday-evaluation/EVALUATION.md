# Lab test evaluation: Swarnadip Kar (swarnadipk)

**CSP352 · AI-Augmented Software Development · lab test of Sunday 11 October 2026**

## Your result

**Total: 27 / 50**  ·  class median 28.6 / 50  ·  class mean 30.1 / 50

## How the marks were set

- **Marks per question** were fixed from the questions themselves, judged by two independent examiners who saw no student results: Q1 9, Q2 4, Q3 13, Q4 6, Q5 8.5, Q6 9.5 (total 50).
- **Partial credit:** each question has a set of grader tests. You earn that question's marks in proportion to the tests your answer passed, so passing 7 of 10 tests on a 13-mark question earns 9.1 marks.
- **What counted as submitted:** for each question file, your latest commit made by **13:30 IST** (the end of the test) that reached the course Gitea server by **14:00 IST**. Commits made after 13:30 were not graded.
- **Aider:** on questions where Aider was not allowed (Q1, Q3, Q5), the paper stated that an answer made with Aider would not be evaluated.
- An answer that does not run (for example, a syntax or import error) passes no tests and earns 0 for that question.

## Summary

| Question | Aider | Marks | Result |
|---|---|---|---|
| Q1 Parsing a price from model output | not allowed | 7.5 / 9 | partial: 5 of 6 tests |
| Q2 Conversation state | allowed | 4 / 4 | full marks |
| Q3 Validating a structured decision | not allowed | 0 / 13 | partial: 0 of 10 tests |
| Q4 Consensus vote | allowed | 6 / 6 | full marks |
| Q5 Tool permissions | not allowed | 0 / 8.5 | partial: 0 of 7 tests |
| Q6 Tool dispatch with a call budget | allowed | 9.5 / 9.5 | full marks |

## Q1: Parsing a price from model output

**Marks: 7.5 / 9**  ·  Aider **not allowed**

Graded version: commit `b9ea882`, on the server by 12:14 IST.

You passed **5 of 6** grader tests, earning 7.5 of 9 marks (1.5 lost). The tests that failed:

- `test_extracts_a_whole_dollar_amount_with_no_cents`: ValueError: Invalid price string: '9 toda'. The string should represent a valid number.

<!-- RESPONSE Q1 START -->
> If you think this question was marked wrongly, explain here: which test, why your answer is correct, and which commit.

<!-- RESPONSE Q1 END -->

## Q2: Conversation state

**Marks: 4 / 4**  ·  Aider allowed

Graded version: commit `7bab1d3`, on the server by 12:36 IST.

All 4 grader tests passed. Full marks.

<!-- RESPONSE Q2 START -->
> If you think this question was marked wrongly, explain here: which test, why your answer is correct, and which commit.

<!-- RESPONSE Q2 END -->

## Q3: Validating a structured decision

**Marks: 0 / 13**  ·  Aider **not allowed**

Graded version: commit `a35ff1e`, on the server by 13:22 IST.

You passed **0 of 10** grader tests, earning 0 of 13 marks (13 lost). The tests that failed:

- `test_accepts_well_formed_decision`: NameError: name 'raw_response_text' is not defined
- `test_rejects_unknown_action`: NameError: name 'raw_response_text' is not defined
- `test_rejects_confidence_above_one`: NameError: name 'raw_response_text' is not defined
- `test_accepts_confidence_boundary_values_for_a_non_refund_action`: NameError: name 'raw_response_text' is not defined
- `test_reports_malformed_json_distinctly_from_schema_violation`: NameError: name 'raw_response_text' is not defined
- `test_rejects_refund_decision_with_low_confidence`: NameError: name 'raw_response_text' is not defined
- `test_accepts_refund_decision_at_the_confidence_boundary`: NameError: name 'raw_response_text' is not defined
- `test_rejects_refund_decision_just_below_the_confidence_boundary`: NameError: name 'raw_response_text' is not defined
- `test_rejects_top_level_json_that_is_not_an_object`: NameError: name 'raw_response_text' is not defined
- `test_ignores_unknown_extra_fields`: NameError: name 'raw_response_text' is not defined

<!-- RESPONSE Q3 START -->
I am not disputing that the graded version (commit `a35ff1e`) failed the grader tests. After the test I reviewed my submission and identified the bugs:

- `validate_decision` referenced an undefined name, `raw_response_text`, instead of its parameter `raw`. This caused the `NameError` shown in all 10 failing tests.
- In `refund_needs_high_confidence`, I used `action` and `confidence` instead of `self.action` and `self.confidence`.
- I did not handle top-level JSON that is not an object (for example `[1, 2, 3]`).

The grader tests were not available to students during the test, and I did not run my own example inputs through `validate_decision` before committing, which would have exposed the first bug. The schema itself (`Literal` for the action, `Field(ge=0.0, le=1.0)` for confidence, the refund/confidence rule and the separate handling of `JSONDecodeError` and `ValidationError`) was written to match the question, but I understand that marks follow the tests. If any partial credit for the underlying logic is possible, I would be grateful for it.
<!-- RESPONSE Q3 END -->

## Q4: Consensus vote

**Marks: 6 / 6**  ·  Aider allowed

Graded version: commit `ae90929`, on the server by 12:36 IST.

All 7 grader tests passed. Full marks.

<!-- RESPONSE Q4 START -->
> If you think this question was marked wrongly, explain here: which test, why your answer is correct, and which commit.

<!-- RESPONSE Q4 END -->

## Q5: Tool permissions

**Marks: 0 / 8.5**  ·  Aider **not allowed**

Graded version: commit `a35ff1e`, on the server by 13:22 IST.

You passed **0 of 7** grader tests, earning 0 of 8.5 marks (8.5 lost). The tests that failed:

- `test_allows_an_action_whose_exact_permission_is_granted`: TypeError: unhashable type: 'set'
- `test_write_permission_implies_read`: TypeError: unhashable type: 'set'
- `test_admin_permission_implies_write_and_read`: TypeError: unhashable type: 'set'
- `test_read_permission_does_not_imply_write`: TypeError: unhashable type: 'set'
- `test_rejects_an_unknown_action`: ValueError: not enough values to unpack (expected 2, got 1)
- `test_empty_granted_set_denies_any_permissioned_action`: TypeError: unhashable type: 'set'
- `test_write_permission_does_not_imply_admin`: TypeError: unhashable type: 'set'

<!-- RESPONSE Q5 START -->
I am not disputing that the graded version (commit `a35ff1e`) failed the grader tests. After the test I reviewed my submission and identified the bugs:

- `check_permission` returned a dict (`{"error": ...}`) instead of the `(ok, error)` tuple the question specifies. This caused the "not enough values to unpack" failure on the unknown-action test.
- I called `PERMISSION_HIERARCHY.get(granted_permissions)` with a set as the dictionary key, which caused the "unhashable type: 'set'" failures. I should have checked each granted permission individually.
- The function still ended with a leftover `raise NotImplementedError`, so it never returned `(True, None)`.

The grader tests were not available to students during the test, and I did not run my own example calls before committing. The error message formats ("unknown action" and "permission denied") did follow the question, but I understand that marks follow the tests. If any partial credit for the underlying logic is possible, I would be grateful for it.
<!-- RESPONSE Q5 END -->

## Q6: Tool dispatch with a call budget

**Marks: 9.5 / 9.5**  ·  Aider allowed

Graded version: commit `96b2c60`, on the server by 13:22 IST.

All 7 grader tests passed. Full marks.

<!-- RESPONSE Q6 START -->
> If you think this question was marked wrongly, explain here: which test, why your answer is correct, and which commit.

<!-- RESPONSE Q6 END -->

## Check a result yourself

The `grader-tests/` folder in this repository holds the six test files your answers were marked with, and `live_client.py`, which they need. To run a question's tests against your graded version, for example Q3 with graded commit `abc1234`:

```
cd ~/lab-test-sunday
git show abc1234:q3_validate_decision.py > ~/lab-test-sunday-evaluation/grader-tests/q3_validate_decision.py
cd ~/lab-test-sunday-evaluation/grader-tests
python3 -m pytest -q test_q3_validate_decision.py
```

Use the commit shown under each question above. You should see the same tests pass and fail as listed here.

## If you disagree with a mark

1. Write your explanation **only inside** the response block under that question, between `<!-- RESPONSE Qn START -->` and `<!-- RESPONSE Qn END -->`. Changes anywhere else in this file are ignored.
2. Commit and push to this repository.
3. Your instructors compare what you pushed with the original and decide. Their decision will be added to this file.

Please be specific: name the test, explain why your answer meets it, and give the commit.
