def append_to_log(item, log=None):
    """Append `item` to a log list and return it.

    Meant to start a fresh log each time it's called without an explicit
    `log` argument.
    """
    if log is None:
        log = []
    log.append(item)
    return log
