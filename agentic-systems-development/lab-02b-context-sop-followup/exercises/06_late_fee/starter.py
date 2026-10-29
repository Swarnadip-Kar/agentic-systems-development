from datetime import datetime

def compute_late_fee(due_date: str, paid_date: str, daily_rate: float) -> float:
    # Validate input dates
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d")
        paid = datetime.strptime(paid_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Please use 'YYYY-MM-DD'")
    
    # Ensure paid date is after due date
    if paid < due:
        raise ValueError("Paid date cannot be before due date")
    
    # Ensure paid date is not in the future
    if paid > datetime.now():
        raise ValueError("Paid date cannot be in the future")
    
    # Calculate the number of days late
    days_late = (paid - due).days
    
    # Calculate the late fee
    late_fee = days_late * daily_rate
    
    return late_fee
