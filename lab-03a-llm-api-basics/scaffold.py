"""Lab 3a: LLM API basics. Fill in each TODO yourself -- no aider for
this file's core logic (aider is fine for debugging help only). Run
`python3 scaffold.py` after each TODO to check your progress; the
grading tests are in test_scaffold.py (do not open that file until
you've finished -- it contains the expected behavior, not hints)."""
import json
import os
from pathlib import Path

from openai import OpenAI, APIError, APITimeoutError, RateLimitError

ALLOWED_CATEGORIES = {"billing", "technical", "account", "feature-request", "complaint"}

# Tickets 7-8 deliberately mix two intents (e.g. a bug report plus a refund
# ask) so the model's real answer tends to hedge/explain rather than return
# a clean label -- see Exercise 6 / REPORT.md.
TRAP_TICKET_IDS = [7, 8]


def assigned_trap_ticket_id():
    # Deterministic per student: same student always gets the same trap
    # ticket, different students are spread across TRAP_TICKET_IDS.
    who = os.environ.get("USER", "unknown")
    return TRAP_TICKET_IDS[sum(ord(c) for c in who) % len(TRAP_TICKET_IDS)]


def load_tickets():
    data = json.loads(Path(__file__).with_name("tickets.json").read_text())
    return data


def get_client():
    client = OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
    )
    return client


def classify_ticket(client, ticket_text):
    response = client.chat.completions.create(
        model="main",
        messages=[
            {"role": "system", "content": "Based on the Request Reply with only one of the allowed catagory words nothing else: billing, technical, account, feature-request, complaint"},
            {"role": "user", "content": ticket_text},
        ],
    )
    return response


def extract_category(response):
    if not response.choices:
        raise RuntimeError("empty choices in response")

    text = response.choices[0]['message']['content'].strip().lower()

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

    return response.choices[0]['message']['content'].strip()


def main():
    client = get_client()
    for ticket in load_tickets():
        category = classify_ticket_safely(client, ticket["text"])
        print(f"ticket {ticket['id']}: {category}")


if __name__ == "__main__":
    main()
