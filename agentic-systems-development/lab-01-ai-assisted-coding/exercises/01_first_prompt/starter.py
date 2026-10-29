def parse_duration(s: str) -> int:
    """Parse a duration string like "1h30m", "45m", or "2h" into total minutes."""
    hours = 0
    minutes = 0
    parts = s.split('h')
    
    if len(parts) > 1:
        hours = int(parts[0])
        s = parts[1]
    
    parts = s.split('m')
    if len(parts) > 0 and parts[0].isdigit():
        minutes = int(parts[0])
    
    return hours * 60 + minutes
