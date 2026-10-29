def moving_average(data: list[float], window: int) -> list[float]:
    """Return the average of each consecutive `window`-sized slice of data.

    moving_average([1, 2, 3, 4], 2) -> [1.5, 2.5, 3.5]
    """
    result = []
    for i in range(len(data) - window + 1):  # Adjusted range to include the last possible window
        chunk = data[i:i + window]
        result.append(sum(chunk) / window)
    return result
