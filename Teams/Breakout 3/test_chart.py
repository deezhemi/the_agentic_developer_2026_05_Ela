"""
Unit tests for chart.py — ASCII segmented bar chart.

Conventions used in this project:
  - unittest.TestCase (no pytest)
  - io.StringIO + contextlib.redirect_stdout for capturing print output
  - unittest.mock.patch('builtins.print') to assert print is never called
"""

import io
import sys
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch, call

# Ensure the directory containing chart.py is on the path so the import
# works regardless of where the test runner is invoked from.
sys.path.insert(0, os.path.dirname(__file__))

import chart
from chart import _FILLS, _WIDTH


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rows(*pairs):
    """Build a list of {'category': ..., 'total': ...} dicts from (name, amount) pairs."""
    return [{"category": cat, "total": amt} for cat, amt in pairs]


def _render(rows):
    """Call pie_chart and return all printed output as a single string."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        chart.pie_chart(rows)
    return buf.getvalue()


def _extract_bar(output):
    """Return the inner content of the '[...]' bar line (without brackets)."""
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return stripped[1:-1]
    return None


def _extract_legend_lines(output):
    """Return the non-empty, non-bar output lines (the category legend rows)."""
    lines = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("[") and stripped.endswith("]")):
            lines.append(line)
    return lines


# ---------------------------------------------------------------------------
# Early-return / zero-grand-total cases
# ---------------------------------------------------------------------------

class TestPieChartEarlyReturn(unittest.TestCase):
    """pie_chart must produce no output when grand total is zero."""

    def test_empty_list_prints_nothing(self):
        """An empty input list must not call print at all."""
        with patch("builtins.print") as mock_print:
            chart.pie_chart([])
        mock_print.assert_not_called()

    def test_all_zero_totals_prints_nothing(self):
        """Rows whose totals are all 0.0 must not call print."""
        with patch("builtins.print") as mock_print:
            chart.pie_chart(_rows(("Food", 0.0), ("Transport", 0.0)))
        mock_print.assert_not_called()

    def test_single_zero_total_prints_nothing(self):
        with patch("builtins.print") as mock_print:
            chart.pie_chart(_rows(("Food", 0.0)))
        mock_print.assert_not_called()

    def test_mix_of_zero_and_nonzero_does_produce_output(self):
        """As long as at least one row has a non-zero total the chart renders."""
        out = _render(_rows(("Food", 0.0), ("Transport", 50.0)))
        self.assertGreater(len(out), 0)

    def test_returns_none_on_zero_grand(self):
        """pie_chart must explicitly return None (no value) for zero grand total."""
        result = chart.pie_chart([])
        self.assertIsNone(result)

    def test_returns_none_on_nonzero_grand(self):
        """pie_chart has no return value — must return None for non-zero input too."""
        result = chart.pie_chart(_rows(("Food", 10.0)))
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# Bar width
# ---------------------------------------------------------------------------

class TestBarWidth(unittest.TestCase):
    """The bar between [ and ] must always be exactly _WIDTH characters."""

    def _assert_bar_width(self, rows):
        out = _render(rows)
        bar = _extract_bar(out)
        self.assertIsNotNone(bar, "No bar line found in output")
        self.assertEqual(
            len(bar),
            _WIDTH,
            f"Expected bar width {_WIDTH}, got {len(bar)}: {bar!r}",
        )

    def test_two_equal_categories(self):
        self._assert_bar_width(_rows(("Food", 50.0), ("Other", 50.0)))

    def test_two_unequal_categories(self):
        self._assert_bar_width(_rows(("Food", 30.0), ("Other", 70.0)))

    def test_three_categories(self):
        self._assert_bar_width(_rows(("Food", 10.0), ("Housing", 20.0), ("Other", 70.0)))

    def test_seven_categories(self):
        """Exactly as many categories as fill characters."""
        self._assert_bar_width(
            _rows(
                ("A", 10.0), ("B", 10.0), ("C", 10.0), ("D", 10.0),
                ("E", 10.0), ("F", 10.0), ("G", 40.0),
            )
        )

    def test_eight_categories_wraps_fill(self):
        """More categories than fill chars — fill cycling must not break bar width."""
        self._assert_bar_width(
            _rows(
                ("A", 5.0), ("B", 5.0), ("C", 5.0), ("D", 5.0),
                ("E", 5.0), ("F", 5.0), ("G", 5.0), ("H", 65.0),
            )
        )

    def test_single_category(self):
        self._assert_bar_width(_rows(("Food", 100.0)))

    def test_small_fractions_that_round_to_zero(self):
        """A very small category may round to 0 chars — bar must still be _WIDTH."""
        self._assert_bar_width(_rows(("Tiny", 0.1), ("Huge", 999.9)))

    def test_many_categories_with_awkward_totals(self):
        """Prime-like totals stress the rounding remainder logic."""
        self._assert_bar_width(
            _rows(
                ("A", 13.0), ("B", 17.0), ("C", 7.0),
                ("D", 3.0), ("E", 60.0),
            )
        )

    def test_large_amounts_do_not_overflow_bar(self):
        self._assert_bar_width(_rows(("Food", 12345.67), ("Other", 9876.54)))


# ---------------------------------------------------------------------------
# Single-category behaviour
# ---------------------------------------------------------------------------

class TestSingleCategory(unittest.TestCase):
    """With one category the entire bar must use the first fill character."""

    def test_bar_is_entirely_first_fill_char(self):
        out = _render(_rows(("Food", 100.0)))
        bar = _extract_bar(out)
        self.assertIsNotNone(bar)
        # All characters in the bar must be the same (the first fill char).
        self.assertEqual(len(set(bar)), 1)
        self.assertEqual(bar[0], _FILLS[0])

    def test_bar_is_full_width(self):
        out = _render(_rows(("Food", 999.99)))
        bar = _extract_bar(out)
        self.assertEqual(len(bar), _WIDTH)

    def test_legend_shows_100_percent(self):
        out = _render(_rows(("Food", 42.0)))
        self.assertIn("100.0%", out)

    def test_legend_shows_correct_amount(self):
        out = _render(_rows(("Food", 42.0)))
        self.assertIn("42.00", out)


# ---------------------------------------------------------------------------
# Legend / category lines
# ---------------------------------------------------------------------------

class TestLegendLines(unittest.TestCase):
    """Each category must appear in the legend with the right fill, amount, and %."""

    def test_category_name_appears(self):
        out = _render(_rows(("Housing", 200.0), ("Food", 100.0)))
        self.assertIn("Housing", out)
        self.assertIn("Food", out)

    def test_dollar_amount_formatted_to_two_decimal_places(self):
        out = _render(_rows(("Food", 12.5)))
        self.assertIn("12.50", out)

    def test_zero_cents_formatted_correctly(self):
        out = _render(_rows(("Food", 100.0)))
        self.assertIn("100.00", out)

    def test_percentage_for_equal_split(self):
        out = _render(_rows(("Food", 50.0), ("Other", 50.0)))
        # Both categories are 50 % each.
        pct_values = [w.rstrip("%") for w in out.split() if w.endswith("%")]
        self.assertEqual(len(pct_values), 2)
        for v in pct_values:
            self.assertAlmostEqual(float(v), 50.0, places=1)

    def test_percentage_for_single_category_is_100(self):
        out = _render(_rows(("Food", 999.0)))
        pct_values = [w.rstrip("%") for w in out.split() if w.endswith("%")]
        self.assertEqual(len(pct_values), 1)
        self.assertAlmostEqual(float(pct_values[0]), 100.0, places=1)

    def test_percentages_sum_to_100(self):
        out = _render(
            _rows(("Food", 30.0), ("Transport", 20.0), ("Housing", 15.0), ("Other", 35.0))
        )
        pct_values = [float(w.rstrip("%")) for w in out.split() if w.endswith("%")]
        self.assertAlmostEqual(sum(pct_values), 100.0, places=0)

    def test_correct_number_of_legend_lines(self):
        """There must be exactly one legend line per input category."""
        rows = _rows(("Food", 10.0), ("Housing", 20.0), ("Transport", 30.0))
        out = _render(rows)
        legend = _extract_legend_lines(out)
        self.assertEqual(len(legend), len(rows))

    def test_fill_prefix_in_legend(self):
        """Each legend line must start (after whitespace) with two copies of its fill char."""
        categories = [("A", 10.0), ("B", 20.0), ("C", 70.0)]
        out = _render(_rows(*categories))
        legend = _extract_legend_lines(out)
        for i, line in enumerate(legend):
            expected_fill = _FILLS[i % len(_FILLS)] * 2
            self.assertTrue(
                line.strip().startswith(expected_fill),
                f"Legend line {i} expected to start with {expected_fill!r}, got: {line!r}",
            )


# ---------------------------------------------------------------------------
# Fill character cycling
# ---------------------------------------------------------------------------

class TestFillCharacterCycling(unittest.TestCase):
    """Fill characters must wrap around _FILLS for more than len(_FILLS) categories."""

    def _build_equal_rows(self, n):
        """Return n equal-weight rows."""
        amount = 100.0 / n
        return _rows(*[(f"Cat{i}", amount) for i in range(n)])

    def test_first_seven_categories_use_distinct_fills(self):
        rows = self._build_equal_rows(len(_FILLS))
        out = _render(rows)
        legend = _extract_legend_lines(out)
        for i, line in enumerate(legend):
            expected = _FILLS[i] * 2
            self.assertTrue(
                line.strip().startswith(expected),
                f"Category {i}: expected fill {expected!r}, line: {line!r}",
            )

    def test_eighth_category_wraps_to_first_fill(self):
        rows = self._build_equal_rows(len(_FILLS) + 1)
        out = _render(rows)
        legend = _extract_legend_lines(out)
        # The 8th line (index 7) should wrap back to _FILLS[0].
        eighth_line = legend[len(_FILLS)].strip()
        expected_fill = _FILLS[0] * 2
        self.assertTrue(
            eighth_line.startswith(expected_fill),
            f"8th category: expected fill {expected_fill!r}, got: {eighth_line!r}",
        )

    def test_bar_fill_chars_cycle_for_many_categories(self):
        """The bar itself must also cycle fills — verify via first char of each segment."""
        n = len(_FILLS) + 3
        rows = self._build_equal_rows(n)
        out = _render(rows)
        bar = _extract_bar(out)
        self.assertIsNotNone(bar)
        # Each expected fill char (in order) should appear somewhere in the bar.
        seen = set(bar)
        for fill in _FILLS:
            self.assertIn(
                fill,
                seen,
                f"Fill char {fill!r} expected in bar but not found: {bar!r}",
            )

    def test_double_wrap_at_fourteen_categories(self):
        """14 categories = 2 full cycles through 7 fills; no IndexError should occur."""
        rows = self._build_equal_rows(14)
        out = _render(rows)
        legend = _extract_legend_lines(out)
        self.assertEqual(len(legend), 14)
        # Category 14 (index 13) maps to _FILLS[13 % 7] = _FILLS[6].
        last_line = legend[13].strip()
        expected_fill = _FILLS[13 % len(_FILLS)] * 2
        self.assertTrue(
            last_line.startswith(expected_fill),
            f"14th category: expected {expected_fill!r}, got: {last_line!r}",
        )


# ---------------------------------------------------------------------------
# Rounding / remainder absorption
# ---------------------------------------------------------------------------

class TestRoundingRemainder(unittest.TestCase):
    """The last segment must absorb any rounding remainder so the bar is always _WIDTH."""

    def _bar_width(self, rows):
        out = _render(rows)
        bar = _extract_bar(out)
        self.assertIsNotNone(bar)
        return len(bar)

    def test_thirds_sum_to_full_width(self):
        """Three equal thirds (100/3 each) cannot divide _WIDTH evenly; bar must still be 40."""
        w = self._bar_width(_rows(("A", 100 / 3), ("B", 100 / 3), ("C", 100 / 3)))
        self.assertEqual(w, _WIDTH)

    def test_prime_divisor_totals(self):
        """Totals chosen so individual rounded segments never add to exactly 40."""
        w = self._bar_width(_rows(("A", 7.0), ("B", 11.0), ("C", 13.0)))
        self.assertEqual(w, _WIDTH)

    def test_very_skewed_distribution(self):
        """One tiny and one huge category — rounding of the tiny one must not lose characters."""
        w = self._bar_width(_rows(("Tiny", 1.0), ("Big", 99.0)))
        self.assertEqual(w, _WIDTH)

    def test_many_small_equal_categories(self):
        """11 categories of equal size (not a divisor of 40) must still fill bar exactly."""
        rows = _rows(*[(f"Cat{i}", 1.0) for i in range(11)])
        w = self._bar_width(rows)
        self.assertEqual(w, _WIDTH)

    def test_last_segment_can_be_zero_width(self):
        """If rounding uses exactly _WIDTH for earlier segments the last one gets 0 chars."""
        # Two equal halves: 20 + (40 - 20) = 40 exactly.
        w = self._bar_width(_rows(("A", 50.0), ("B", 50.0)))
        self.assertEqual(w, _WIDTH)


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

class TestOutputStructure(unittest.TestCase):
    """Verify the overall shape of the printed output."""

    def test_bar_line_contains_brackets(self):
        out = _render(_rows(("Food", 10.0)))
        bar_lines = [l for l in out.splitlines() if "[" in l and "]" in l]
        self.assertEqual(len(bar_lines), 1, "Expected exactly one bar line")

    def test_blank_line_after_bar(self):
        """There should be a blank line between the bar and the legend."""
        out = _render(_rows(("Food", 10.0), ("Other", 90.0)))
        lines = out.splitlines()
        bar_idx = next(i for i, l in enumerate(lines) if "[" in l and "]" in l)
        self.assertEqual(lines[bar_idx + 1], "", "Expected blank line immediately after bar")

    def test_trailing_blank_line_after_legend(self):
        """Output must end with a trailing newline (blank line after legend)."""
        out = _render(_rows(("Food", 10.0)))
        self.assertTrue(out.endswith("\n"), "Output must end with a newline")

    def test_print_called_correct_number_of_times(self):
        """For n categories: 1 (bar) + 1 (blank) + n (legend) + 1 (trailing blank) = n+3 calls."""
        n = 3
        rows = _rows(("Food", 10.0), ("Transport", 20.0), ("Other", 70.0))
        with patch("builtins.print") as mock_print:
            chart.pie_chart(rows)
        self.assertEqual(mock_print.call_count, n + 3)

    def test_bar_line_format_with_leading_spaces(self):
        """Bar line must be '  [<bar>]' — two leading spaces, then brackets."""
        out = _render(_rows(("Food", 100.0)))
        bar_line = next(l for l in out.splitlines() if "[" in l)
        self.assertTrue(bar_line.startswith("  ["), f"Expected '  [' prefix, got: {bar_line!r}")
        self.assertTrue(bar_line.endswith("]"), f"Expected ']' suffix, got: {bar_line!r}")

    def test_legend_lines_have_leading_spaces(self):
        """Each legend line must start with two spaces (matching the bar line indent)."""
        out = _render(_rows(("Food", 50.0), ("Other", 50.0)))
        legend = _extract_legend_lines(out)
        for line in legend:
            self.assertTrue(
                line.startswith("  "),
                f"Legend line must start with two spaces: {line!r}",
            )


# ---------------------------------------------------------------------------
# Dollar amount formatting edge cases
# ---------------------------------------------------------------------------

class TestDollarFormatting(unittest.TestCase):

    def test_large_dollar_amount(self):
        out = _render(_rows(("Salary", 123456.78)))
        self.assertIn("123456.78", out)

    def test_very_small_dollar_amount(self):
        out = _render(_rows(("Tip", 0.01), ("Other", 9.99)))
        self.assertIn("0.01", out)

    def test_whole_dollar_amount_has_two_decimal_places(self):
        out = _render(_rows(("Rent", 1000.0)))
        self.assertIn("1000.00", out)

    def test_multiple_amounts_all_present(self):
        out = _render(_rows(("Food", 12.34), ("Transport", 56.78)))
        self.assertIn("12.34", out)
        self.assertIn("56.78", out)


if __name__ == "__main__":
    unittest.main()
