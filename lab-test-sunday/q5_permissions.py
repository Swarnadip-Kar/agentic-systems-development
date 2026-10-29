"""Q5: a permission gate with a hierarchy, in the style of Lab 5b's
dispatch_action_call -- but Lab 5b's version only checked for an exact
permission match. Here, higher permissions imply lower ones: "admin"
implies "write" implies "read".

Aider: NOT ALLOWED for this question. Using Aider, or any AI
code-generation assistant, to write your solution here means this
question will not be evaluated.
"""

PERMISSION_MAP = {
    "search_tickets": "read",
    "check_ticket_status": "read",
    "refund_ticket": "write",
    "escalate_ticket": "write",
    "delete_ticket": "admin",
}

PERMISSION_HIERARCHY = {
    "admin": {"admin", "write", "read"},
    "write": {"write", "read"},
    "read": {"read"},
}


def check_permission(action, granted_permissions):
    """Return (True, None) if `action` is a known action in
    PERMISSION_MAP and its required permission is implied by one of
    `granted_permissions` via PERMISSION_HIERARCHY (e.g. having
    "write" satisfies a "read" requirement). Otherwise return (False,
    error_message): error_message should mention "unknown action" if
    `action` isn't in PERMISSION_MAP at all, or mention "permission"
    if it is known but not satisfied by any granted permission.
    """
    if action not in PERMISSION_MAP:
        return {"error": f"unknown action: '{action}'"}
    
    required_permission = PERMISSION_MAP.get(action)
    if required_permission not in PERMISSION_HIERARCHY.get(granted_permissions):
        return {"error": f"permission denied: '{action}' requires '{required_permission}' permission"}
    raise NotImplementedError
