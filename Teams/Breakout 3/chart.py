_FILLS = ["#", "=", "+", "~", "*", "-", "@"]
_WIDTH = 40


def pie_chart(totals):
    """Print an ASCII segmented bar chart for a list of (category, total) rows."""
    grand = sum(row["total"] for row in totals)
    if not grand:
        return

    # Allocate bar segments, giving the last category any rounding remainder.
    segments = []
    used = 0
    for i, row in enumerate(totals[:-1]):
        count = round(row["total"] / grand * _WIDTH)
        segments.append((_FILLS[i % len(_FILLS)], count))
        used += count
    segments.append((_FILLS[(len(totals) - 1) % len(_FILLS)], _WIDTH - used))

    bar = "".join(ch * n for ch, n in segments)
    print(f"  [{bar}]")
    print()
    for i, row in enumerate(totals):
        fill = _FILLS[i % len(_FILLS)]
        pct = row["total"] / grand * 100
        print(f"  {fill * 2} {row['category']:<15}  ${row['total']:>8.2f}  {pct:>5.1f}%")
    print()
