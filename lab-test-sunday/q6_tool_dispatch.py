"""Q6: a tool dispatcher with a per-tool call budget, plus one live
tool-calling call.

Aider: ALLOWED for this question.

Part A (graded): implement dispatch below -- it never touches the
network. It extends the permission-check-then-call-then-report pattern
with a budget: no single tool may be called more than 3 times in one
session, tracked via the `call_counts` dict you are given (the same
dict instance is reused across calls, so mutate it in place).

Part B (not graded, but required -- spend exactly 1 of your 5 live
calls here): using live_client.get_client() and the registry/tools
below, send one message to the model with tools enabled and tool_choice
"auto", and if it requests a tool call, run it through your dispatch()
(with a fresh {} call_counts) and print the result.
"""
from live_client import get_client

REGISTRY = {
    "lookup_price": {
        "permission": "read",
        "fn": lambda sku: {"sku": sku, "price": 9.99} if sku == "A1" else {"error": "no such sku"},
    },
}

TOOLS = [{
    "type": "function",
    "function": {
        "name": "lookup_price",
        "description": "Look up the price of a SKU.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
        },
    },
}]


def dispatch(name, arguments, registry, granted_permissions, call_counts):
    """Look up `name` in `registry` (a dict of {name: {"permission":
    str, "fn": callable}}). If `name` isn't in `registry`, return
    {"error": "unknown tool: <name>"} -- do not touch call_counts. If
    the registry entry's "permission" isn't in `granted_permissions`,
    return {"error": "permission denied: '<name>' requires
    '<permission>' permission"} -- do not touch call_counts either.
    Otherwise increment call_counts[name] (creating it at 0 first if
    absent); if the new count is more than 3, return {"error": "call
    budget exceeded for '<name>'"} without calling the tool. Otherwise
    call spec["fn"](**arguments) and return its result; if that call
    raises TypeError (e.g. wrong argument names), return {"error":
    "dispatch failed: <exception message>"} instead of raising.
    """
    if name not in registry:
        return {"error": f"unknown tool: {name}"}
    
    spec = registry[name]
    if spec["permission"] not in granted_permissions:
        return {"error": f"permission denied: '{name}' requires '{spec['permission']}' permission"}
    
    call_counts[name] = call_counts.get(name, 0) + 1
    if call_counts[name] > 3:
        return {"error": f"call budget exceeded for '{name}'"}
    
    try:
        return spec["fn"](**arguments)
    except TypeError as e:
        return {"error": f"dispatch failed: {str(e)}"}
    except Exception as e:
        return {"error": f"unexpected error: {str(e)}"}


def run_live_demo():
    import json
    client = get_client()
    response = client.chat.completions.create(
        model="main",
        messages=[{"role": "user", "content": "What's the price of SKU A1?"}],
        tools=TOOLS,
        tool_choice="auto",
    )
    message = response.choices[0].message
    if hasattr(message, "tool_calls"):
        for call in message.tool_calls:
            arguments = json.loads(call.function.arguments)
            result = dispatch(call.function.name, arguments, REGISTRY, {"read"}, {})
            print(result)
    else:
        print("model answered directly:", message.content)


if __name__ == "__main__":
    run_live_demo()
