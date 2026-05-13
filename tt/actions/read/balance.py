from __future__ import print_function

import os
from datetime import datetime, date, timedelta

from tt.dataaccess.utils import get_data_store
from tt.dateutils.dateutils import parse_isotime
from tt.actions.utils import reportingutils
from tt.exceptz.exceptz import TIError
from tt.colors.colors import ljust_with_color

SALDO_START_DATE_ENV = "TT_SALDO_START_DATE"
SALDO_START_HOURS_ENV = "TT_SALDO_START_HOURS"
HOURS_PER_DAY_ENV = "TT_HOURS_PER_DAY"

_DAY_COL = 6
_DIFF_COL = 9


def _build_day_worked(work):
    result = {}
    for item in work:
        if "end" not in item:
            continue
        day = reportingutils.extract_day(item["start"])
        duration = parse_isotime(item["end"]) - parse_isotime(item["start"])
        result[day] = result.get(day, timedelta()) + duration
    return result


def _build_days_off(holiday):
    result = {}
    for item in holiday:
        day_key = item["date"].rstrip("T")
        result[day_key] = item["name"]
    return result


def _fmt_hm(td):
    total_minutes = int(abs(td.total_seconds())) // 60
    return "%d:%02d" % (total_minutes // 60, total_minutes % 60)


def _fmt_signed(td):
    total_seconds = int(td.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_minutes = abs(total_seconds) // 60
    return "%s%d:%02d" % (sign, total_minutes // 60, total_minutes % 60)


def _color_by_sign(colorizer, td, text):
    return colorizer.green(text) if td.total_seconds() >= 0 else colorizer.red(text)


def action_balance(colorizer):
    start_date_str = os.getenv(SALDO_START_DATE_ENV)
    start_hours_str = os.getenv(SALDO_START_HOURS_ENV, "0")
    hours_per_day = float(os.getenv(HOURS_PER_DAY_ENV, "8"))

    if not start_date_str:
        raise TIError(
            "Please set %s (YYYY-MM-DD).\n"
            "Optionally set %s to the starting saldo in decimal hours (e.g. 12.5 or -3)."
            % (SALDO_START_DATE_ENV, SALDO_START_HOURS_ENV)
        )

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    start_td = timedelta(hours=float(start_hours_str))
    saldo = timedelta(hours=float(start_hours_str))
    soll_per_day = timedelta(hours=hours_per_day)

    data = get_data_store().load()
    day_worked = _build_day_worked(data["work"])
    days_off = _build_days_off(data.get("holiday", []))

    today = date.today()

    print(
        "Balance since %s  start: %s  soll: %gh/day"
        % (start_date_str, _fmt_signed(start_td), hours_per_day)
    )
    print()
    day_headers = "".join("%-*s" % (_DAY_COL, d) for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Wknd"])
    print(
        "  %-9s  %s  %-*s %s"
        % ("", day_headers, _DIFF_COL, "Diff", "Saldo")
    )
    print("  " + "-" * 72)

    current_monday = start_date - timedelta(days=start_date.weekday())

    while current_monday <= today:
        iso = current_monday.isocalendar()
        week_label = "%d-W%02d" % (iso[0], iso[1])
        week_diff = timedelta()
        day_cells = []

        for i in range(5):
            d = current_monday + timedelta(days=i)
            day_key = d.strftime("%Y-%m-%d")

            if d < start_date or d > today:
                day_cells.append(" " * _DAY_COL)
                continue

            is_off = day_key in days_off
            worked = day_worked.get(day_key, timedelta())
            soll = timedelta() if is_off else soll_per_day
            week_diff += worked - soll

            if is_off and worked == timedelta():
                raw = colorizer.yellow("off")
            elif worked > timedelta():
                raw = _fmt_hm(worked)
            else:
                raw = colorizer.red("--")

            day_cells.append(ljust_with_color(raw, _DAY_COL))

        # Saturday + Sunday: soll is always 0
        wknd_worked = timedelta()
        for i in range(5, 7):
            d = current_monday + timedelta(days=i)
            if d < start_date or d > today:
                continue
            worked = day_worked.get(d.strftime("%Y-%m-%d"), timedelta())
            wknd_worked += worked
        week_diff += wknd_worked

        if wknd_worked > timedelta():
            wknd_cell = ljust_with_color(colorizer.cyan(_fmt_hm(wknd_worked)), _DAY_COL)
        else:
            wknd_cell = " " * _DAY_COL

        saldo += week_diff

        diff_str = _fmt_signed(week_diff)
        diff_colored = ljust_with_color(_color_by_sign(colorizer, week_diff, diff_str), _DIFF_COL)
        saldo_colored = _color_by_sign(colorizer, saldo, _fmt_signed(saldo))

        print("  %-9s  %s%s  %s %s" % (
            week_label, "".join(day_cells), wknd_cell, diff_colored, saldo_colored
        ))

        current_monday += timedelta(weeks=1)

    print()
    print("Current saldo: " + _color_by_sign(colorizer, saldo, _fmt_signed(saldo)))
