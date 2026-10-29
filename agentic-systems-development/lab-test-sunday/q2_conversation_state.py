"""Q2: conversation state, plus one live call.

Aider: ALLOWED for this question.

Part A (graded): implement append_turn below.

Part B (not graded, but required -- spend exactly 1 of your 5 live
calls here): using live_client.get_client(), send a short conversation
built with your append_turn function (a system turn plus one user
turn) to the model, append the assistant's reply with append_turn too,
and save the full message list to conversation.json in this directory
so a TA can see you did it.
"""
from live_client import get_client


def append_turn(history, role, content):
    """Return a NEW list: history with one more {"role": role,
    "content": content} turn appended. Do not modify `history` in
    place. Raise ValueError if role is not one of "system", "user",
    "assistant".
    """
    if role not in ["system", "user", "assistant"]:
        raise ValueError("Role must be one of 'system', 'user', 'assistant'.")
    return history + [{"role": role, "content": content}]


def run_live_demo():
    client = get_client()
    history = append_turn([], "system", "You are a terse support agent.")
    history = append_turn(history, "user", "My order #42 never arrived.")
    response = client.chat.completions.create(model="main", messages=history)
    history = append_turn(history, "assistant", response.choices[0].message.content)
    import json
    with open("conversation.json", "w") as f:
        json.dump(history, f, indent=2)


if __name__ == "__main__":
    run_live_demo()
