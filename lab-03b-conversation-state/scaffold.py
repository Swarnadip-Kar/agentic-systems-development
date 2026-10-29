"""Lab 3b: conversation state and retries, aider-assisted -- build on
what you wrote by hand in Lab 3a. Use aider freely here; the point of
this session is automating what you understood by writing it manually
last time."""
import json
import math
import os
import time
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError, APITimeoutError

ALLOWED_CATEGORIES = {"billing", "technical", "account", "feature-request", "complaint"}
MAX_ATTEMPTS = 4
MAX_CONTEXT_TOKENS = 30  # synthetic budget -- see README's "why so low" note; live-verified 2026-08-13


def load_tickets_batch():
    data = json.loads(Path(__file__).with_name("tickets_batch.json").read_text())
    return data


def get_client():
    # max_retries=0: the openai SDK retries transient errors internally by
    # default (2 retries), which would silently swallow the failures this
    # exercise needs YOUR call_with_retry to actually see and handle.
    return OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
        max_retries=0,
    )


def call_with_retry(client, messages):
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        try:
            response = client.chat.completions.create(
                model="main",
                messages=[
                    {"role": "system", "content": "Based on the Request Reply with only one of the allowed catagory words nothing else: billing, technical, account, feature-request, complaint"},
                    {"role": "user", "content": messages[-1]["content"]},
                ],
            )
            return response
        except RateLimitError as e:
            if attempt == MAX_ATTEMPTS - 1:
                print(f"RateLimitError: {e}. Max attempts reached.")
                raise e
            print(f"RateLimitError: {e}. Retrying in {2 ** attempt} seconds...")
            time.sleep(2 ** attempt)
            attempt += 1
        except APITimeoutError as e:
            if attempt == MAX_ATTEMPTS - 1:
                print(f"APITimeoutError: {e}. Max attempts reached.")
                raise e
            print(f"APITimeoutError: {e}. Retrying in {2 ** attempt} seconds...")
            time.sleep(2 ** attempt)
            attempt += 1
        except APIError as e:
            if attempt == MAX_ATTEMPTS - 1:
                print(f"APIError: {e}. Max attempts reached.")
                raise e
            print(f"APIError: {e}. Retrying in {2 ** attempt} seconds...")
            time.sleep(2 ** attempt)
            attempt += 1


def classify_batch(client, tickets, trim_fn=None):
    history = []
    recorded = []
    running_tokens = 0

    for ticket in tickets:
        if trim_fn is not None:
            history = trim_fn(history, MAX_CONTEXT_TOKENS, running_tokens)

        history.append({"role": "user", "content": ticket["text"]})
        print(f"Processing ticket {ticket['id']}")  # Debugging statement

        response = call_with_retry(client, history)
        running_tokens = response.usage.total_tokens

        category = extract_category(response)
        print(f"Ticket {ticket['id']} categorized as {category}")  # Debugging statement

        history.append({"role": "assistant", "content": response.choices[0].message.content.strip()})
        print(f"History length after appending: {len(history)}")  # Debugging statement

        recorded.append((ticket["id"], category, len(history), running_tokens))

    return recorded


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


def token_growth_report(recorded):
    history_lengths = [record[2] for record in recorded]
    start_length = history_lengths[0]
    end_length = history_lengths[-1]

    print(f"history grew from {start_length} to {end_length} messages across this batch")


def check_budget(recorded):
    for record in recorded:
        ticket_id, category, history_length, total_tokens = record
        if total_tokens > MAX_CONTEXT_TOKENS:
            print(f"ticket {ticket_id} pushed the conversation to {total_tokens} tokens, over the {MAX_CONTEXT_TOKENS} token budget.")
            return ticket_id
    return None


def enforce_budget(history, max_tokens, current_tokens):
    if current_tokens <= max_tokens:
        return history

    num_pairs = len(history) // 2
    if num_pairs <= 1:
        return history  # Never drop the last remaining pair

    avg_per_pair = current_tokens / num_pairs
    pairs_to_drop = math.ceil((current_tokens - max_tokens) / avg_per_pair)

    # Ensure we don't drop the last remaining pair
    pairs_to_drop = min(pairs_to_drop, num_pairs - 1)

    # Drop the oldest pairs
    dropped_pairs = pairs_to_drop * 2
    dropped_ticket_ids = [history[i]["content"] for i in range(0, dropped_pairs, 2)]
    print(f"Dropping {dropped_pairs} oldest pairs from history. Tickets Dropped: {dropped_ticket_ids}")  # Debugging statement
    return history[dropped_pairs:]


def main():
    print("Starting main function...")
    client = get_client()
    print("Client obtained")
    tickets = load_tickets_batch()
    print("Tickets loaded")
    recorded = classify_batch(client, tickets)
    print("Batch classified")
    token_growth_report(recorded)
    check_budget(recorded)

    # Re-run the batch with truncation enabled to demonstrate Exercise 5
    # (note: this doubles API calls on the ticket batch, acceptable at 8 tickets)
    trimmed = classify_batch(client, tickets, trim_fn=lambda h, mx, cur: enforce_budget(h, mx, cur))
    token_growth_report(trimmed)
    print("Main function completed successfully")


if __name__ == "__main__":
    main()
