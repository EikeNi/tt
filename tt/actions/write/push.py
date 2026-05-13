from __future__ import print_function

import os
from datetime import datetime, time, timedelta

from tt.dataaccess.utils import get_data_store
from tt.dateutils.dateutils import isotime_utc_to_local, parse_isotime
from tt.actions.utils import reportingutils
from tt.exceptz.exceptz import TIError


def _build_day_report(work):
    report = {}
    for item in work:
        if "end" not in item:
            continue
        day = reportingutils.extract_day(item["start"])
        start = isotime_utc_to_local(item["start"])
        end = isotime_utc_to_local(item["end"])
        duration = parse_isotime(item["end"]) - parse_isotime(item["start"])
        if day not in report:
            report[day] = {"work_duration": timedelta(), "start": start, "end": end}
        if report[day]["start"] > start:
            report[day]["start"] = start
        if report[day]["end"] < end:
            report[day]["end"] = end
        report[day]["work_duration"] += duration
    return report


def _timedelta_to_time(td):
    total_minutes = int(td.total_seconds()) // 60
    return time(total_minutes // 60, total_minutes % 60)


XLSX_FILE_ENV_VAR = "TT_XLSX_FILE"


def _build_days_off(holiday):
    days_off = {}
    for item in holiday:
        day_key = item["date"].rstrip("T")  # "2026-05-06T" -> "2026-05-06"
        days_off[day_key] = item["name"]
    return days_off


def action_push(colorizer, xlsx_path):
    try:
        import openpyxl
    except ImportError:
        raise TIError(
            "openpyxl is required for 'tt push'. Install with:\n"
            "  pip install openpyxl --break-system-packages"
        )

    if xlsx_path is None:
        xlsx_path = os.getenv(XLSX_FILE_ENV_VAR)
    if not xlsx_path:
        raise TIError(
            "Please provide the path to the xlsx file, or set %s in your environment." % XLSX_FILE_ENV_VAR
        )

    xlsx_path = os.path.expanduser(xlsx_path)
    if not os.path.exists(xlsx_path):
        raise TIError("File not found: %s" % xlsx_path)

    data = get_data_store().load()
    day_report = _build_day_report(data["work"])
    days_off = _build_days_off(data.get("holiday", []))

    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active

    work_filled = 0
    work_skipped = 0
    off_filled = 0
    off_skipped = 0

    for row in ws.iter_rows(min_row=2):
        cell_date = row[0].value
        if not isinstance(cell_date, datetime):
            continue
        day_key = cell_date.strftime("%Y-%m-%d")

        if day_key in day_report:
            cell_start = row[5]   # column F
            cell_end = row[6]     # column G
            cell_break = row[7]   # column H
            if cell_start.value is not None:
                work_skipped += 1
            else:
                entry = day_report[day_key]
                break_duration = (entry["end"] - entry["start"]) - entry["work_duration"]
                start_t = entry["start"].time().replace(second=0, microsecond=0)
                end_t = entry["end"].time().replace(second=0, microsecond=0)
                break_t = _timedelta_to_time(break_duration)
                cell_start.value = start_t
                cell_end.value = end_t
                cell_break.value = break_t
                work_filled += 1
                print(
                    colorizer.green(day_key) + "  work  "
                    + start_t.strftime("%H:%M") + " - " + end_t.strftime("%H:%M")
                    + "  break " + break_t.strftime("%H:%M")
                )

        if day_key in days_off:
            cell_comment = row[11]  # column L
            if cell_comment.value is not None:
                off_skipped += 1
            else:
                cell_comment.value = days_off[day_key]
                row[4].value = 0  # column E: Soll = 0 for days off
                off_filled += 1
                print(colorizer.yellow(day_key) + "  off   " + days_off[day_key])

    wb.save(xlsx_path)

    if work_filled == 0 and work_skipped == 0 and off_filled == 0 and off_skipped == 0:
        print("No matching days found in %s." % xlsx_path)
        return

    print("")
    parts = []
    parts.append("Pushed " + colorizer.green(str(work_filled)) + " work day(s) and "
                 + colorizer.green(str(off_filled)) + " day(s) off to " + xlsx_path + ".")
    skipped_parts = []
    if work_skipped:
        skipped_parts.append(colorizer.yellow(str(work_skipped)) + " work day(s)")
    if off_skipped:
        skipped_parts.append(colorizer.yellow(str(off_skipped)) + " day(s) off")
    if skipped_parts:
        parts.append("Skipped " + " and ".join(skipped_parts) + " already filled.")
    print(" ".join(parts))
