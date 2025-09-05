from datetime import datetime

def format_datetime(dt: datetime) -> str:
    """Форматирует дату и время в ISO-формат."""
    return dt.isoformat() if dt else None