import argparse
from datetime import date

import chart
import db
import expenses
import income


def cmd_add(args):
    expenses.add_expense(args.amount, args.category, args.note)
    note_str = f" — {args.note}" if args.note else ""
    print(f"Added: ${args.amount:.2f}  [{args.category}]{note_str}")


def cmd_list(args):
    rows = expenses.list_expenses(args.month)
    if not rows:
        print("No expenses found.")
        return
    for r in rows:
        note_str = f"  {r['note']}" if r['note'] else ""
        print(f"{r['date']}  ${r['amount']:>8.2f}  {r['category']:<15}{note_str}")


def cmd_income(args):
    income.add_income(args.amount, args.source, args.note)
    note_str = f" — {args.note}" if args.note else ""
    print(f"Income added: ${args.amount:.2f}  [{args.source}]{note_str}")


def cmd_report(args):
    month = args.month or date.today().strftime("%Y-%m")
    totals = expenses.monthly_totals(month)
    income_total = income.monthly_income_total(month)
    if not totals and income_total == 0:
        print(f"No data recorded for {month}.")
        return
    print(f"\n  Budget Report — {month}")
    print("  " + "-" * 36)
    if income_total > 0:
        print(f"  {'INCOME':<15}  ${income_total:>8.2f}")
        print("  " + "-" * 36)
    expense_total = 0.0
    for r in totals:
        print(f"  {r['category']:<15}  ${r['total']:>8.2f}")
        expense_total += r["total"]
    print("  " + "-" * 36)
    if income_total > 0:
        print(f"  {'EXPENSES':<15}  ${expense_total:>8.2f}")
        net = income_total - expense_total
        print(f"  {'NET':<15}  ${net:>8.2f}")
    else:
        print(f"  {'TOTAL':<15}  ${expense_total:>8.2f}")
    print()
    if totals:
        chart.pie_chart(totals)


def main():
    db.init_db()

    parser = argparse.ArgumentParser(prog="budget", description="Personal budget tracker")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Record an expense")
    p_add.add_argument("amount", type=float, help="Amount in dollars")
    p_add.add_argument("category", choices=expenses.CATEGORIES, help="Spending category")
    p_add.add_argument("note", nargs="?", default="", help="Optional description")

    p_income = sub.add_parser("income", help="Record income")
    p_income.add_argument("amount", type=float, help="Amount in dollars")
    p_income.add_argument("source", help="Income source (e.g. Salary, Freelance)")
    p_income.add_argument("note", nargs="?", default="", help="Optional description")

    p_list = sub.add_parser("list", help="List recent expenses")
    p_list.add_argument("--month", metavar="YYYY-MM", default=None)

    p_report = sub.add_parser("report", help="Monthly spending summary")
    p_report.add_argument("--month", metavar="YYYY-MM", default=None)

    args = parser.parse_args()
    {"add": cmd_add, "income": cmd_income, "list": cmd_list, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
