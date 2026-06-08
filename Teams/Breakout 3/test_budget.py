import argparse
import io
import sqlite3
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


def _make_in_memory_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


class _DBMixin(unittest.TestCase):
    def setUp(self):
        self._conn = _make_in_memory_conn()
        self._patch = patch("db.get_conn", return_value=self._conn)
        self._patch.start()
        import db
        db.init_db()

    def tearDown(self):
        self._patch.stop()
        self._conn.close()


class TestExpenses(_DBMixin):
    def test_valid_categories_are_accepted(self):
        import expenses
        for cat in expenses.CATEGORIES:
            expenses.add_expense(1.00, cat, "test")
        self.assertEqual(len(expenses.list_expenses()), len(expenses.CATEGORIES))

    def test_invalid_category_raises(self):
        import expenses
        with self.assertRaises(ValueError):
            expenses.add_expense(5.00, "Education", "tuition")

    def test_add_expense_records_correctly(self):
        import expenses
        expenses.add_expense(20.00, "Other", "learning how to code in claude")
        rows = expenses.list_expenses()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amount"], 20.00)
        self.assertEqual(rows[0]["category"], "Other")
        self.assertEqual(rows[0]["note"], "learning how to code in claude")

    def test_monthly_totals_aggregate_by_category(self):
        import expenses
        expenses.add_expense(10.00, "Food", "lunch", date="2026-06-01")
        expenses.add_expense(5.00, "Food", "coffee", date="2026-06-02")
        expenses.add_expense(20.00, "Other", "workshop", date="2026-06-03")
        totals = {r["category"]: r["total"] for r in expenses.monthly_totals("2026-06")}
        self.assertAlmostEqual(totals["Food"], 15.00)
        self.assertAlmostEqual(totals["Other"], 20.00)

    def test_note_is_optional(self):
        import expenses
        expenses.add_expense(8.50, "Transport")
        rows = expenses.list_expenses()
        self.assertEqual(rows[0]["note"], "")


class TestIncome(_DBMixin):
    def test_add_income_records_correctly(self):
        import income
        income.add_income(3000.00, "Salary", "June paycheck", date="2026-06-01")
        rows = income.list_income()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amount"], 3000.00)
        self.assertEqual(rows[0]["source"], "Salary")
        self.assertEqual(rows[0]["note"], "June paycheck")

    def test_monthly_income_total(self):
        import income
        income.add_income(3000.00, "Salary", date="2026-06-01")
        income.add_income(500.00, "Freelance", date="2026-06-15")
        income.add_income(200.00, "Salary", date="2026-05-01")
        self.assertAlmostEqual(income.monthly_income_total("2026-06"), 3500.00)
        self.assertAlmostEqual(income.monthly_income_total("2026-05"), 200.00)

    def test_monthly_income_total_zero_when_none(self):
        import income
        self.assertAlmostEqual(income.monthly_income_total("2026-06"), 0.00)

    def test_source_and_note_are_optional(self):
        import income
        income.add_income(100.00)
        rows = income.list_income()
        self.assertEqual(rows[0]["source"], "")
        self.assertEqual(rows[0]["note"], "")

    def test_net_calculation(self):
        import expenses, income
        income.add_income(3000.00, "Salary", date="2026-06-01")
        expenses.add_expense(12.50, "Food", "lunch", date="2026-06-01")
        expenses.add_expense(20.00, "Other", "workshop", date="2026-06-03")
        total_income = income.monthly_income_total("2026-06")
        total_expenses = sum(r["total"] for r in expenses.monthly_totals("2026-06"))
        self.assertAlmostEqual(total_income - total_expenses, 2967.50)


class TestPieChart(unittest.TestCase):
    def _render(self, rows):
        data = [{"category": cat, "total": amt} for cat, amt in rows]
        buf = io.StringIO()
        with redirect_stdout(buf):
            import chart
            chart.pie_chart(data)
        return buf.getvalue()

    def test_bar_is_correct_width(self):
        out = self._render([("Food", 50.0), ("Other", 50.0)])
        bar_line = [l for l in out.splitlines() if l.strip().startswith("[")][0]
        inner = bar_line.strip()[1:-1]
        self.assertEqual(len(inner), 40)

    def test_percentages_sum_to_100(self):
        out = self._render([("Food", 30.0), ("Transport", 20.0), ("Other", 50.0)])
        pcts = [float(w.rstrip("%")) for w in out.split() if w.endswith("%")]
        self.assertAlmostEqual(sum(pcts), 100.0, places=0)

    def test_all_categories_appear_in_legend(self):
        rows = [("Food", 10.0), ("Housing", 20.0), ("Other", 70.0)]
        out = self._render(rows)
        for cat, _ in rows:
            self.assertIn(cat, out)

    def test_empty_totals_prints_nothing(self):
        out = self._render([])
        self.assertEqual(out, "")

    def test_single_category_fills_bar(self):
        out = self._render([("Food", 100.0)])
        bar_line = [l for l in out.splitlines() if l.strip().startswith("[")][0]
        inner = bar_line.strip()[1:-1]
        self.assertEqual(len(set(inner)), 1)


class TestBudgetCLI(_DBMixin):
    def _capture(self, fn, args_ns):
        buf = io.StringIO()
        with redirect_stdout(buf):
            fn(args_ns)
        return buf.getvalue()

    def test_cmd_add_prints_confirmation(self):
        import budget
        args = argparse.Namespace(amount=12.50, category="Food", note="lunch")
        out = self._capture(budget.cmd_add, args)
        self.assertIn("12.50", out)
        self.assertIn("Food", out)
        self.assertIn("lunch", out)

    def test_cmd_add_no_note(self):
        import budget
        args = argparse.Namespace(amount=5.00, category="Transport", note="")
        out = self._capture(budget.cmd_add, args)
        self.assertIn("5.00", out)
        self.assertNotIn("—", out)

    def test_cmd_list_shows_expenses(self):
        import expenses, budget
        expenses.add_expense(8.00, "Food", "breakfast", date="2026-06-01")
        out = self._capture(budget.cmd_list, argparse.Namespace(month=None))
        self.assertIn("8.00", out)
        self.assertIn("Food", out)

    def test_cmd_list_empty(self):
        import budget
        out = self._capture(budget.cmd_list, argparse.Namespace(month=None))
        self.assertIn("No expenses", out)

    def test_cmd_income_prints_confirmation(self):
        import budget
        args = argparse.Namespace(amount=3000.00, source="Salary", note="June paycheck")
        out = self._capture(budget.cmd_income, args)
        self.assertIn("3000.00", out)
        self.assertIn("Salary", out)
        self.assertIn("June paycheck", out)

    def test_cmd_report_expense_only(self):
        import expenses, budget
        expenses.add_expense(12.50, "Food", date="2026-06-01")
        out = self._capture(budget.cmd_report, argparse.Namespace(month="2026-06"))
        self.assertIn("Food", out)
        self.assertIn("12.50", out)
        self.assertIn("TOTAL", out)
        self.assertNotIn("INCOME", out)

    def test_cmd_report_with_income_shows_net(self):
        import expenses, income, budget
        income.add_income(1000.00, "Salary", date="2026-06-01")
        expenses.add_expense(200.00, "Housing", date="2026-06-01")
        out = self._capture(budget.cmd_report, argparse.Namespace(month="2026-06"))
        self.assertIn("INCOME", out)
        self.assertIn("1000.00", out)
        self.assertIn("EXPENSES", out)
        self.assertIn("NET", out)
        self.assertIn("800.00", out)

    def test_cmd_report_no_data(self):
        import budget
        out = self._capture(budget.cmd_report, argparse.Namespace(month="2099-01"))
        self.assertIn("No data", out)


if __name__ == "__main__":
    unittest.main()
