def merge_overlapping_intervals(intervals: list) -> list:
    if not intervals:
        return []

    # Filter out invalid intervals where the end is less than the start
    valid_intervals = [interval for interval in intervals if interval[0] <= interval[1]]

    # Sort intervals based on the start time
    valid_intervals.sort(key=lambda x: x[0])

    merged_intervals = []
    current_interval = valid_intervals[0]

    for next_interval in valid_intervals[1:]:
        if current_interval[1] >= next_interval[0]:
            # Merge the current interval with the next interval
            current_interval = (current_interval[0], max(current_interval[1], next_interval[1]))
        else:
            # Add the current interval to the merged list
            merged_intervals.append(current_interval)
            current_interval = next_interval

    # Add the last interval to the merged list
    merged_intervals.append(current_interval)

    return merged_intervals
