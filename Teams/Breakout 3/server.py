"""
server.py — Flask web UI for the personal budget tracker.

Architecture note: this file is intentionally thin.
- All SQL lives in db.py
- All business logic lives in expenses.py / income.py
- This file only handles HTTP: routing, JSON serialization, and error responses.
"""

from datetime import date

from flask import Flask, jsonify, render_template, request

import db
import expenses
import income

# Initialize the database schema before any request can arrive.
# This is the web-server equivalent of the `db.init_db()` call in budget.py's main().
db.init_db()

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page dashboard."""
    return render_template("index.html")


# ---------------------------------------------------------------------------
# API — read
# ---------------------------------------------------------------------------

@app.route("/api/report")
def api_report():
    """
    GET /api/report?month=YYYY-MM

    Returns JSON:
      { "month": "YYYY-MM", "income": float, "totals": [{"category": str, "total": float}, ...] }

    Defaults to the current month if ?month is omitted.
    """
    month = request.args.get("month") or date.today().strftime("%Y-%m")

    # monthly_totals() returns sqlite3.Row objects.
    # sqlite3.Row is dict-like but not JSON-serializable, so we convert explicitly.
    totals = [
        {"category": row["category"], "total": row["total"]}
        for row in expenses.monthly_totals(month)
    ]

    income_total = income.monthly_income_total(month)

    return jsonify({
        "month": month,
        "income": income_total,
        "totals": totals,
    })


# ---------------------------------------------------------------------------
# API — write
# ---------------------------------------------------------------------------

@app.route("/api/expense", methods=["POST"])
def api_add_expense():
    """
    POST /api/expense
    Body: { "amount": float, "category": str, "note": str }

    Validates that category is in expenses.CATEGORIES (add_expense raises ValueError if not).
    Returns: {"ok": true} or HTTP 400 with {"error": "..."}.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    amount = data.get("amount")
    category = data.get("category", "")
    note = data.get("note", "")

    if amount is None:
        return jsonify({"error": "amount is required"}), 400

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a number"}), 400

    # Validate category upfront for a clearer error message.
    # (add_expense also validates, but catching ValueError here lets us return 400.)
    if category not in expenses.CATEGORIES:
        return jsonify({
            "error": f"Invalid category '{category}'. Valid options: {', '.join(expenses.CATEGORIES)}"
        }), 400

    expenses.add_expense(amount, category, note)
    return jsonify({"ok": True})


@app.route("/api/income", methods=["POST"])
def api_add_income():
    """
    POST /api/income
    Body: { "amount": float, "source": str, "note": str }

    Returns: {"ok": true} or HTTP 400 with {"error": "..."}.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    amount = data.get("amount")
    source = data.get("source", "")
    note = data.get("note", "")

    if amount is None:
        return jsonify({"error": "amount is required"}), 400

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a number"}), 400

    income.add_income(amount, source, note)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # debug=True gives auto-reload on file changes — handy during development.
    # Never use debug=True in production.
    app.run(debug=True, port=5000)
