"""Q4: consensus classification with an abstention threshold, plus
three live calls.

Aider: ALLOWED for this question.

Part A (graded): implement consensus_vote below.

Part B (not graded, but required -- spend exactly 3 of your 5 live
calls here): using live_client.get_client(), ask the model to classify
the ticket text below into exactly one of "billing", "technical",
"shipping" three separate times (three separate calls, temperature 0.7
so they can actually disagree), collect the three labels, and print
the result of consensus_vote on them.
"""
from live_client import get_client

TICKET_TEXT = (
    "My card was charged twice for the same order and the app also "
    "won't let me log in to check my order history."
)

# Extra text for testing if its actually working
# TICKET_TEXT = (
#     "My card was charged twice for the same order and the app also "
#     "won't let me log in to check my order history. This is technical issue"
# )


def consensus_vote(labels):
    """Return the label that appears most often in `labels`, but ONLY
    if it has a strict majority (more than half of len(labels)) --
    otherwise return the string "no_consensus". Break a tie among
    equally-frequent labels by whichever appeared FIRST in the list
    (this only matters for choosing which label to check against the
    threshold; a tied label can never itself reach a strict majority).
    Raise ValueError if `labels` is empty.
    """
    if not labels:
        raise ValueError("Labels list is empty")

    label_count = {}
    first_occurrence = {}

    for index, label in enumerate(labels):
        if label not in label_count:
            label_count[label] = 0
            first_occurrence[label] = index
        label_count[label] += 1

    max_count = 0
    best_label = None

    for label in labels:
        count = label_count[label]
        if count > max_count:
            max_count = count
            best_label = label
        elif count == max_count:
            if first_occurrence[label] < first_occurrence[best_label]:
                best_label = label

    if max_count > len(labels) / 2:
        return best_label
    else:
        return "no_consensus"


def run_live_demo():
    client = get_client()
    labels = []
    for _ in range(3):
        response = client.chat.completions.create(
            model="main",
            temperature=0.7,
            messages=[
                {"role": "system", "content": "Reply with exactly one word: "
                 "billing, technical, or shipping."},
                {"role": "user", "content": TICKET_TEXT},
            ],
        )
        labels.append(response.choices[0].message.content.strip().lower())
    print("votes:", labels)
    print("result:", consensus_vote(labels))


if __name__ == "__main__":
    run_live_demo()
