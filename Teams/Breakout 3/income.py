import db


def add_income(amount: float, source: str = "", note: str = "", date: str = None):
    cols = "amount, source, note" + (", date" if date else "")
    placeholders = "?, ?, ?" + (", ?" if date else "")
    params = [amount, source, note] + ([date] if date else [])
    with db.get_conn() as conn:
        conn.execute(f"INSERT INTO income ({cols}) VALUES ({placeholders})", params)


def list_income(month: str = None):
    with db.get_conn() as conn:
        if month:
            return conn.execute(
                "SELECT * FROM income WHERE strftime('%Y-%m', date) = ? ORDER BY date DESC",
                (month,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM income ORDER BY date DESC LIMIT 50"
        ).fetchall()


def monthly_income_total(month: str) -> float:
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE strftime('%Y-%m', date) = ?",
            (month,),
        ).fetchone()
        return row["total"]
