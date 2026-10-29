def calculate_gpa(grades: list) -> float:
    total_grade_points = 0.0
    total_credit_hours = 0.0

    for _, grade_points, credit_hours in grades:
        if credit_hours < 0:
            raise ValueError("Credit hours cannot be negative")
        if credit_hours > 0:
            total_grade_points += grade_points * credit_hours
            total_credit_hours += credit_hours

    if total_credit_hours == 0:
        return 0.0

    return total_grade_points / total_credit_hours
