def safe_get(d: dict, key, default=None):
    """Return d[key], or `default` if the key isn't present."""
    try:
        return d[key]
    except KeyError:
        return default
