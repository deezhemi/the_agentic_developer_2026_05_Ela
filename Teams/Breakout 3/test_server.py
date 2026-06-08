"""
test_server.py — Flask route tests for server.py

Testing strategy
----------------
1. Framework: unittest.TestCase exclusively (project convention — no pytest).
2. Database isolation: patch("db.get_conn") with an in-memory SQLite connection so
   every test starts with a clean schema and no file I/O touches budget.db.
3. Flask test client: app.test_client() — no live server is started.
4. server.py calls db.init_db() at module import time, so we must ensure the
   in-memory DB patch is active before the Flask app processes any request.
   We achieve this by patching get_conn in setUp *before* creating the client,
   which patches the underlying module that server.py (and expenses/income) import.
5. Template rendering (GET /): Flask resolves templates relative to the app's
   template_folder. The real templates/ directory exists next to server.py, so
   render_template works as-is under the test client.
"""

import io
import json
import os
import sqlite3
import sys
import unittest
from unittest.mock import patch

# Ensure the source directory is on the path so imports resolve regardless of
# where the test runner is invoked from.
sys.path.insert(0, os.path.dirname(__file__))


# ---------------------------------------------------------------------------
# Shared DB helper (mirrors _DBMixin in test_budget.py)
# ---------------------------------------------------------------------------

def _make_in_memory_conn():
    """Return a fresh in-memory SQLite connection with Row factory set."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


class _ServerDBMixin(unittest.TestCase):
    """
    Base class that:
      - swaps db.get_conn() for an in-memory connection for every test
      - initialises the schema (expenses + income tables)
      - provides self.client (Flask test client) ready to use
    """

    def setUp(self):
        self._conn = _make_in_memory_conn()
        self._patch = patch("db.get_conn", return_value=self._conn)
        self._patch.start()

        # init_db() was already called at module import time with whatever
        # connection existed then; call it again now so our in-memory DB
        # has the schema.
        import db
        db.init_db()

        import server
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()

    def tearDown(self):
        self._patch.stop()
        self._conn.close()


# ---------------------------------------------------------------------------
# GET /api/report
# ---------------------------------------------------------------------------

class TestApiReport(_ServerDBMixin):
    """Tests for GET /api/report?month=YYYY-MM"""

    def test_report_returns_correct_json_structure(self):
        """A month with data returns the expected keys and types."""
        import expenses, income
        expenses.add_expense(12.50, "Food", "lunch", date="2026-06-01")
        expenses.add_expense(20.00, "Transport", "bus pass", date="2026-06-05")
        income.add_income(3000.00, "Salary", date="2026-06-01")

        resp = self.client.get("/api/report?month=2026-06")
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertIn("month", data)
        self.assertIn("income", data)
        self.assertIn("totals", data)
        self.assertEqual(data["month"], "2026-06")
        self.assertAlmostEqual(data["income"], 3000.00)
        self.assertIsInstance(data["totals"], list)

    def test_report_totals_aggregate_by_category(self):
        """Multiple expenses in the same category are summed."""
        import expenses
        expenses.add_expense(10.00, "Food", "breakfast", date="2026-06-01")
        expenses.add_expense(5.00, "Food", "snack", date="2026-06-02")
        expenses.add_expense(50.00, "Housing", "rent", date="2026-06-01")

        resp = self.client.get("/api/report?month=2026-06")
        data = json.loads(resp.data)

        totals_by_cat = {row["category"]: row["total"] for row in data["totals"]}
        self.assertAlmostEqual(totals_by_cat["Food"], 15.00)
        self.assertAlmostEqual(totals_by_cat["Housing"], 50.00)

    def test_report_empty_month_returns_zero_income_and_empty_totals(self):
        """A month with no data returns income=0.0 and totals=[]."""
        resp = self.client.get("/api/report?month=2099-01")
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertEqual(data["month"], "2099-01")
        self.assertAlmostEqual(data["income"], 0.0)
        self.assertEqual(data["totals"], [])

    def test_report_defaults_to_current_month_when_param_omitted(self):
        """Omitting ?month must not raise an error and must return valid JSON."""
        resp = self.client.get("/api/report")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        # month key must be present and look like YYYY-MM
        self.assertRegex(data["month"], r"^\d{4}-\d{2}$")

    def test_report_totals_each_have_category_and_total_keys(self):
        """Every item in totals must expose 'category' (str) and 'total' (float)."""
        import expenses
        expenses.add_expense(30.00, "Entertainment", "movie", date="2026-06-10")

        resp = self.client.get("/api/report?month=2026-06")
        data = json.loads(resp.data)
        for item in data["totals"]:
            self.assertIn("category", item)
            self.assertIn("total", item)
            self.assertIsInstance(item["category"], str)
            self.assertIsInstance(item["total"], float)

    def test_report_excludes_other_months(self):
        """Expenses from a different month must not appear in the requested month's totals."""
        import expenses
        expenses.add_expense(99.00, "Food", "big dinner", date="2026-05-31")  # May
        expenses.add_expense(10.00, "Food", "lunch", date="2026-06-01")       # June

        resp = self.client.get("/api/report?month=2026-06")
        data = json.loads(resp.data)
        totals_by_cat = {r["category"]: r["total"] for r in data["totals"]}
        # Only the June expense should appear
        self.assertAlmostEqual(totals_by_cat.get("Food", 0), 10.00)


# ---------------------------------------------------------------------------
# POST /api/expense
# ---------------------------------------------------------------------------

class TestApiExpense(_ServerDBMixin):
    """Tests for POST /api/expense"""

    def _post(self, payload, content_type="application/json"):
        return self.client.post(
            "/api/expense",
            data=json.dumps(payload),
            content_type=content_type,
        )

    def test_valid_expense_returns_ok_true(self):
        """A well-formed request must return {"ok": true} with HTTP 200."""
        resp = self._post({"amount": 25.00, "category": "Food", "note": "lunch"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get("ok"))

    def test_valid_expense_is_persisted(self):
        """After a successful POST, the expense must appear in list_expenses()."""
        self._post({"amount": 15.50, "category": "Transport", "note": "bus"})
        import expenses
        rows = expenses.list_expenses()
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["amount"], 15.50)
        self.assertEqual(rows[0]["category"], "Transport")
        self.assertEqual(rows[0]["note"], "bus")

    def test_all_valid_categories_are_accepted(self):
        """Every value in expenses.CATEGORIES must be accepted by the endpoint."""
        import expenses
        for cat in expenses.CATEGORIES:
            resp = self._post({"amount": 1.00, "category": cat})
            self.assertEqual(resp.status_code, 200, f"Category '{cat}' was rejected unexpectedly")

    def test_invalid_category_returns_400(self):
        """An unknown category must return HTTP 400."""
        resp = self._post({"amount": 10.00, "category": "Education", "note": "tuition"})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_invalid_category_error_mentions_valid_options(self):
        """The 400 error message should hint at valid categories."""
        resp = self._post({"amount": 5.00, "category": "Nonsense"})
        data = json.loads(resp.data)
        # The error should reference valid categories
        self.assertIn("category", data.get("error", "").lower())

    def test_missing_amount_returns_400(self):
        """Omitting 'amount' must return HTTP 400, not a 500."""
        resp = self._post({"category": "Food", "note": "no amount"})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_non_numeric_amount_returns_400(self):
        """A non-numeric 'amount' must return HTTP 400."""
        resp = self._post({"amount": "lots", "category": "Food"})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_missing_category_returns_400(self):
        """Omitting 'category' causes it to default to '' which is not valid — must be 400."""
        resp = self._post({"amount": 5.00, "note": "forgot category"})
        self.assertEqual(resp.status_code, 400)

    def test_non_json_body_returns_400(self):
        """Sending a non-JSON body must return HTTP 400."""
        resp = self.client.post(
            "/api/expense",
            data="not json at all",
            content_type="text/plain",
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_note_is_optional(self):
        """A valid request without 'note' must still succeed."""
        resp = self._post({"amount": 8.00, "category": "Health"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get("ok"))

    def test_string_amount_that_is_numeric_is_accepted(self):
        """The server coerces string amounts to float — '12.50' should succeed."""
        resp = self._post({"amount": "12.50", "category": "Other"})
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# POST /api/income
# ---------------------------------------------------------------------------

class TestApiIncome(_ServerDBMixin):
    """Tests for POST /api/income"""

    def _post(self, payload, content_type="application/json"):
        return self.client.post(
            "/api/income",
            data=json.dumps(payload),
            content_type=content_type,
        )

    def test_valid_income_returns_ok_true(self):
        """A well-formed request must return {"ok": true} with HTTP 200."""
        resp = self._post({"amount": 3000.00, "source": "Salary", "note": "June"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get("ok"))

    def test_valid_income_is_persisted(self):
        """After a successful POST, the income must appear in list_income()."""
        self._post({"amount": 500.00, "source": "Freelance", "note": "side project"})
        import income
        rows = income.list_income()
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["amount"], 500.00)
        self.assertEqual(rows[0]["source"], "Freelance")
        self.assertEqual(rows[0]["note"], "side project")

    def test_missing_amount_returns_400(self):
        """Omitting 'amount' must return HTTP 400, not a 500."""
        resp = self._post({"source": "Salary"})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_non_numeric_amount_returns_400(self):
        """A non-numeric 'amount' must return HTTP 400."""
        resp = self._post({"amount": "many", "source": "Salary"})
        self.assertEqual(resp.status_code, 400)

    def test_source_and_note_are_optional(self):
        """Sending only 'amount' must succeed — source and note default to ''."""
        resp = self._post({"amount": 100.00})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get("ok"))

    def test_non_json_body_returns_400(self):
        """Sending a non-JSON body must return HTTP 400."""
        resp = self.client.post(
            "/api/income",
            data="plain text",
            content_type="text/plain",
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_multiple_income_entries_accumulate(self):
        """Two valid POSTs must result in two stored rows."""
        self._post({"amount": 1000.00, "source": "Salary"})
        self._post({"amount": 200.00, "source": "Freelance"})
        import income
        rows = income.list_income()
        self.assertEqual(len(rows), 2)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestIndexPage(_ServerDBMixin):
    """Tests for GET / (the single-page dashboard)."""

    def test_index_returns_200(self):
        """The index route must respond with HTTP 200."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_index_content_type_is_html(self):
        """Response must be HTML."""
        resp = self.client.get("/")
        self.assertIn("text/html", resp.content_type)

    def test_index_contains_budget_dashboard_title(self):
        """The rendered page must include the page title from index.html."""
        resp = self.client.get("/")
        body = resp.data.decode("utf-8")
        self.assertIn("Budget Dashboard", body)

    def test_index_contains_api_report_reference(self):
        """The page JS should reference the /api/report endpoint."""
        resp = self.client.get("/")
        body = resp.data.decode("utf-8")
        self.assertIn("/api/report", body)

    def test_index_contains_doctype(self):
        """Rendered HTML must start with a DOCTYPE declaration."""
        resp = self.client.get("/")
        body = resp.data.decode("utf-8").lstrip()
        self.assertTrue(
            body.lower().startswith("<!doctype"),
            "Expected HTML to start with <!DOCTYPE ...>",
        )


if __name__ == "__main__":
    unittest.main()
