import db

CATEGORIES = ["Food", "Transport", "Housing", "Entertainment", "Health", "Utilities", "Other"]


def add_expense(amount: float, category: str, note: str = "", date: str = None):
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category '{category}'. Valid: {', '.join(CATEGORIES)}")
    cols = "amount, category, note" + (", date" if date else "")
    placeholders = "?, ?, ?" + (", ?" if date else "")
    params = [amount, category, note] + ([date] if date else [])
    with db.get_conn() as conn:
        conn.execute(f"INSERT INTO expenses ({cols}) VALUES ({placeholders})", params)


def list_expenses(month: str = None):
    with db.get_conn() as conn:
        if month:
            return conn.execute(
                "SELECT * FROM expenses WHERE strftime('%Y-%m', date) = ? ORDER BY date DESC",
                (month,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM expenses ORDER BY date DESC LIMIT 50"
        ).fetchall()


def monthly_totals(month: str):
    with db.get_conn() as conn:
        return conn.execute(
            "SELECT category, SUM(amount) AS total "
            "FROM expenses WHERE strftime('%Y-%m', date) = ? "
            "GROUP BY category ORDER BY total DESC",
            (month,),
        ).fetchall()
