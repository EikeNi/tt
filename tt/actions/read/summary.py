from __future__ import print_function

from tt.dataaccess.utils import get_data_store
from tt.dateutils.dateutils import *
from tt.actions.utils import reportingutils

import calendar

TT_HOURS_PER_DAY = float(os.getenv("TT_HOURS_PER_DAY", 8))
hours_per_day = timedelta(
    hours=int(TT_HOURS_PER_DAY),
    minutes=int(round(TT_HOURS_PER_DAY % 1, 2) * 60),
    seconds=int(round((round(TT_HOURS_PER_DAY % 1, 2) * 60) % 1, 2) * 60),
)


def action_summary(month, year):
    data = get_data_store().load()
    work = data["work"]
    days_off = generate_days_off()

    year = get_current_year_local_tz() if year is None else year
    month_cal = calendar.monthcalendar(int(year), int(month))

    target_working_time = timedelta()
    days_off_time = timedelta()
    month_days = []
    for week in month_cal:
        for i, day in enumerate(week):
            report_key = str(year) + "-" + month.zfill(2) + "-" + str(day).zfill(2)
            month_days.append(report_key)
            if day > 0 and i < 5:
                if report_key not in days_off.keys():
                    target_working_time += hours_per_day
    report = dict()
    for item in work:
        if "end" in item:
            day = reportingutils.extract_day(item["start"])
            if day not in month_days:
                continue
            name = item["name"]
            duration = parse_isotime(item["end"]) - parse_isotime(item["start"])
            try:
                report[name]
            except KeyError:
                report[name] = dict()
                report[name]["work_duration"] = timedelta()
                report[name]["tags"] = []
            report[name]["work_duration"] += duration
            if "tags" in item.keys():
                report[name]["tags"] += item["tags"]

    fill = max([len(k) for k in report.keys()]) if report else 8 + 1
    for name in sorted(report.keys()):
        report[name]["rate"] = round(
            100 * report[name]["work_duration"] / target_working_time, 1
        )
    total_rate = sum([entry["rate"] for entry in report.values()])
    for name in sorted(report.keys()):
        # adjust the rate to cover days off
        report[name]["adjusted_rate"] = round(
            100 * (report[name]["work_duration"]) / target_working_time,
            2,
        )
    for name in sorted(report.keys()):
        print(
            name.ljust(fill),
            ": ",
            "%5.2f" % report[name]["adjusted_rate"],
            " - TAGS:",
            sorted(list(set(report[name]["tags"]))),
        )
    print("-" * fill)
    print(
        "Total".ljust(fill),
        ": ",
        "%5.2f" % sum([entry["adjusted_rate"] for entry in report.values()]),
    )


def generate_days_off():
    data = get_data_store().load()
    holiday = data["holiday"]
    days_off = dict()
    for item in holiday:
        day = reportingutils.extract_day(item["date"] + "00:00:00.0Z")
        days_off[day] = item["name"]
    return days_off
