from datetime import datetime

def format_datetime(dt: datetime) -> str:
    """Форматирует дату и время в ISO-формат."""
    return dt.isoformat() if dt else None

def calculate_sum_grade(soft: float, tech: float) -> float:
    """Вычисляет общий балл на основе soft и tech навыков."""
    return (soft or 0) + (tech or 0)