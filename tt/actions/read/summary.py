from __future__ import print_function

from tt.dataaccess.utils import get_data_store
from tt.dateutils.dateutils import *
from tt.actions.utils import reportingutils

import calendar
import shutil

try:
    import asciichartpy as asciichart

    HAS_ASCIICHART = True
except Exception:
    asciichart = None
    HAS_ASCIICHART = False

TT_HOURS_PER_DAY = float(os.getenv("TT_HOURS_PER_DAY", 8))
MINI_PLOT_HEIGHT = 6
CATEGORY_CHOICES = ["Dissertation", "Projekt", "Lehre", "Institut"]
hours_per_day = timedelta(
    hours=int(TT_HOURS_PER_DAY),
    minutes=int(round(TT_HOURS_PER_DAY % 1, 2) * 60),
    seconds=int(round((round(TT_HOURS_PER_DAY % 1, 2) * 60) % 1, 2) * 60),
)


def action_summary(month, year, colorizer=None, include_categories=False):
    month = get_current_month_local_tz() if month is None else str(month).zfill(2)
    year = get_current_year_local_tz() if year is None else str(year)

    store = get_data_store()
    data = store.load()
    work = data["work"]
    category_by_task = ensure_task_categories(data, work)
    assign_missing_categories_interactive(category_by_task, work)
    store.dump(data)

    days_off = generate_days_off()
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
    category_report = dict((category_name, timedelta()) for category_name in CATEGORY_CHOICES)
    for item in work:
        if "end" in item:
            day = reportingutils.extract_day(item["start"])
            if day not in month_days:
                continue
            name = item["name"]
            category = category_by_task.get(name)
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
            if category in CATEGORY_CHOICES:
                category_report[category] += duration

    fill = max([len(k) for k in report.keys()]) if report else 8 + 1
    fill = max(fill, max([len(category_name) for category_name in CATEGORY_CHOICES]))
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
            "%-*s : %6.2f - TAGS: %s"
            % (
                fill,
                name,
                report[name]["adjusted_rate"],
                sorted(list(set(report[name]["tags"]))),
            )
        )
    print("-" * fill)
    print(
        "%-*s : %6.2f"
        % (fill, "Total", sum([entry["adjusted_rate"] for entry in report.values()]))
    )
    print()
    print("Category distribution:")
    for category_name in CATEGORY_CHOICES:
        category_rate = 0.0
        if target_working_time.total_seconds() > 0:
            category_rate = round(
                100 * category_report[category_name].total_seconds() / target_working_time.total_seconds(),
                2,
            )
        print(
            "%-*s : %6.2f - HOURS: %s"
            % (
                fill,
                category_name,
                category_rate,
                format_hours(category_report[category_name]),
            )
        )
    print()
    print_last_12_month_summary_plot(
        work,
        days_off,
        int(year),
        int(month),
        category_by_task,
        colorizer,
        include_categories,
    )


def print_last_12_month_summary_plot(
    work,
    days_off,
    anchor_year,
    anchor_month,
    category_by_task,
    colorizer,
    include_categories,
):
    months = get_last_n_months(anchor_year, anchor_month, 12)
    rows = []
    for month_year in months:
        month_target = get_month_target_working_time(
            month_year["year"], month_year["month"], days_off
        )
        month_worked = get_month_worked_time(work, month_year["year"], month_year["month"])
        worked_per_category = get_month_worked_time_per_category(
            work,
            month_year["year"],
            month_year["month"],
            category_by_task,
        )
        month_rate = 0.0
        if month_target.total_seconds() > 0:
            month_rate = (100.0 * month_worked.total_seconds()) / month_target.total_seconds()
        category_rates = dict((name, 0.0) for name in CATEGORY_CHOICES)
        if month_target.total_seconds() > 0:
            for category_name in CATEGORY_CHOICES:
                category_rates[category_name] = (
                    100.0 * worked_per_category[category_name].total_seconds()
                ) / month_target.total_seconds()
        rows.append(
            {
                "label": "%04d-%02d" % (month_year["year"], month_year["month"]),
                "rate": round(month_rate, 1),
                "worked": month_worked,
                "target": month_target,
                "category_rates": category_rates,
            }
        )

    if include_categories:
        print("Last 12 months utilization trend (stacked categories + total):")
    else:
        print("Last 12 months total utilization trend:")
    for line in render_last_12_month_total_plot(rows, colorizer, include_categories):
        print(line)


def render_last_12_month_total_plot(rows, colorizer=None, include_categories=False):
    if not rows:
        return ["(no data)"]

    if include_categories:
        return render_last_12_month_stacked_area_plot(rows, colorizer)

    if not HAS_ASCIICHART:
        return [
            "asciichartpy is not installed for this interpreter.",
            "Install with: python -m pip install --user asciichartpy",
        ]

    total_series = [max(0.0, row["rate"]) for row in rows]

    terminal_cols, terminal_rows = get_terminal_size()
    chart_height = max(MINI_PLOT_HEIGHT, min(18, terminal_rows - 8))
    repeat_per_month = max(1, int((terminal_cols - 12) / max(1, len(total_series))))
    repeat_per_month = min(repeat_per_month, 8)

    expanded_total_series = []
    for value in total_series:
        expanded_total_series.extend([value] * repeat_per_month)

    scale_max = max([100.0] + total_series)

    config = {
        "height": chart_height,
        "min": 0,
        "max": scale_max,
        "format": "{:6.1f}",
    }

    series = [expanded_total_series]
    lines = ["  Total"]
    if should_use_chart_colors(colorizer):
        config["colors"] = [asciichart.red]

    plot_lines = asciichart.plot(series, config).splitlines()
    lines.extend(plot_lines)
    lines.append("")

    axis_column = get_chart_axis_column(plot_lines)
    plot_width = get_chart_plot_width(plot_lines, axis_column)
    lines.append(build_month_axis_line(rows, repeat_per_month, axis_column, plot_width))
    return lines


def render_last_12_month_stacked_area_plot(rows, colorizer=None):
    total_series = [max(0.0, row["rate"]) for row in rows]
    category_series = {
        category_name: [max(0.0, row["category_rates"][category_name]) for row in rows]
        for category_name in CATEGORY_CHOICES
    }

    terminal_cols, terminal_rows = get_terminal_size()
    chart_height = max(MINI_PLOT_HEIGHT, min(18, terminal_rows - 8))
    repeat_per_month = max(1, int((terminal_cols - 12) / max(1, len(total_series))))
    repeat_per_month = min(repeat_per_month, 8)

    expanded_category_series = {}
    for category_name in CATEGORY_CHOICES:
        expanded_category_series[category_name] = []
        for value in category_series[category_name]:
            expanded_category_series[category_name].extend([value] * repeat_per_month)

    plot_width = len(expanded_category_series[CATEGORY_CHOICES[0]])
    cumulative_totals = [
        sum(expanded_category_series[category_name][idx] for category_name in CATEGORY_CHOICES)
        for idx in range(plot_width)
    ]
    scale_max = max([100.0] + cumulative_totals)

    # Bottom-up canvas; each column is filled by stacked categories.
    canvas = [[" " for _ in range(plot_width)] for _ in range(chart_height + 1)]
    category_symbols = {
        "Dissertation": "D",
        "Projekt": "P",
        "Lehre": "L",
        "Institut": "I",
    }

    for x in range(plot_width):
        bottom = 0
        cumulative = 0.0
        for category_name in CATEGORY_CHOICES:
            cumulative += expanded_category_series[category_name][x]
            top = int(round((cumulative / scale_max) * chart_height))
            for y in range(bottom, min(top, chart_height + 1)):
                canvas[y][x] = category_symbols[category_name]
            bottom = top

    lines = ["  Stacked categories (total is top edge)"]
    lines.append(get_stacked_plot_legend_line(colorizer))

    axis_column = 8
    for level in range(chart_height, -1, -1):
        y_value = (scale_max * float(level)) / float(max(1, chart_height))
        y_label = "%6.1f |" % y_value
        row_chars = [
            colorize_area_symbol(colorizer, ch) if ch != " " else " "
            for ch in canvas[level]
        ]
        lines.append(y_label + "".join(row_chars))

    lines.append(build_month_axis_line(rows, repeat_per_month, axis_column, plot_width))
    return lines


def get_terminal_size():
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def get_chart_axis_column(plot_lines):
    for line in plot_lines:
        for axis_char in ["┤", "┼", "┐", "┘", "┬", "┴", "│"]:
            idx = line.find(axis_char)
            if idx >= 0:
                return idx + 1
    return 8


def get_chart_plot_width(plot_lines, axis_column):
    widths = [max(0, len(line) - axis_column) for line in plot_lines]
    return max(widths) if widths else 0


def build_month_axis_line(rows, repeat_per_month, axis_column, plot_width):
    if plot_width <= 0:
        return ""

    track = [" " for _ in range(plot_width)]
    for index, row in enumerate(rows):
        label = row["label"][5:]
        segment_start = index * repeat_per_month
        segment_center = segment_start + int(repeat_per_month / 2)
        label_start = max(0, segment_center - int(len(label) / 2))

        for offset, char in enumerate(label):
            pos = label_start + offset
            if pos < plot_width:
                track[pos] = char

    return " " * axis_column + "".join(track)


def should_use_chart_colors(colorizer):
    if colorizer is None:
        return True
    if hasattr(colorizer, "get_use_color"):
        return colorizer.get_use_color()
    return True


def get_stacked_plot_legend_line(colorizer):
    entries = [
        ("green", "D=Dissertation"),
        ("blue", "P=Projekt"),
        ("yellow", "L=Lehre"),
        ("cyan", "I=Institut"),
    ]

    rendered = []
    for color_name, label in entries:
        text = label
        if colorizer is not None and hasattr(colorizer, color_name):
            text = getattr(colorizer, color_name)(text)
        rendered.append(text)

    return "  Legend: " + ", ".join(rendered)


def colorize_area_symbol(colorizer, symbol):
    if colorizer is None:
        return symbol
    if symbol == "D":
        return colorizer.green(symbol)
    if symbol == "P":
        return colorizer.blue(symbol)
    if symbol == "L":
        return colorizer.yellow(symbol)
    if symbol == "I":
        return colorizer.cyan(symbol)
    return symbol


def get_last_n_months(anchor_year, anchor_month, month_count):
    months = []
    year = anchor_year
    month = anchor_month
    for _ in range(month_count):
        months.append({"year": year, "month": month})
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    return months


def get_month_target_working_time(year, month, days_off):
    target_working_time = timedelta()
    for week in calendar.monthcalendar(year, month):
        for week_day, day in enumerate(week):
            if day <= 0 or week_day >= 5:
                continue
            report_key = "%04d-%02d-%02d" % (year, month, day)
            if report_key not in days_off.keys():
                target_working_time += hours_per_day
    return target_working_time


def get_month_worked_time(work, year, month):
    worked_time = timedelta()
    month_prefix = "%04d-%02d-" % (year, month)
    for item in work:
        if "end" not in item:
            continue
        day = reportingutils.extract_day(item["start"])
        if not day.startswith(month_prefix):
            continue
        worked_time += parse_isotime(item["end"]) - parse_isotime(item["start"])
    return worked_time


def get_month_worked_time_per_category(work, year, month, category_by_task):
    worked_time_per_category = dict((name, timedelta()) for name in CATEGORY_CHOICES)
    month_prefix = "%04d-%02d-" % (year, month)
    for item in work:
        if "end" not in item:
            continue
        day = reportingutils.extract_day(item["start"])
        if not day.startswith(month_prefix):
            continue
        task_name = item["name"]
        task_category = category_by_task.get(task_name)
        if task_category not in CATEGORY_CHOICES:
            continue
        worked_time_per_category[task_category] += parse_isotime(item["end"]) - parse_isotime(item["start"])
    return worked_time_per_category


def format_hours(duration):
    total_minutes = int(duration.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return "%d:%02d" % (hours, minutes)


def generate_days_off():
    data = get_data_store().load()
    holiday = data["holiday"]
    days_off = dict()
    for item in holiday:
        day = reportingutils.extract_day(item["date"] + "00:00:00.0Z")
        days_off[day] = item["name"]
    return days_off


def ensure_task_categories(data, work):
    if "task_categories" not in data or not isinstance(data["task_categories"], dict):
        data["task_categories"] = {}
    category_by_task = data["task_categories"]

    for item in work:
        task_name = item.get("name")
        if task_name and task_name not in category_by_task:
            category_by_task[task_name] = None
    return category_by_task


def assign_missing_categories_interactive(category_by_task, work):
    task_names = []
    seen = set()
    for item in work:
        task_name = item.get("name")
        if task_name and task_name not in seen:
            seen.add(task_name)
            task_names.append(task_name)

    for task_name in sorted(task_names):
        if category_by_task.get(task_name) in CATEGORY_CHOICES:
            continue
        selected_category = prompt_for_category(task_name)
        category_by_task[task_name] = selected_category


def prompt_for_category(task_name):
    print("Task '%s' has no category yet." % task_name)
    while True:
        for idx, category_name in enumerate(CATEGORY_CHOICES, 1):
            print("  %d) %s" % (idx, category_name))
        print("Choose category [1-%d]: " % len(CATEGORY_CHOICES), end="")
        input_fn = globals().get("raw_input", input)
        user_input = input_fn().strip()

        if user_input.isdigit():
            selection = int(user_input)
            if selection >= 1 and selection <= len(CATEGORY_CHOICES):
                return CATEGORY_CHOICES[selection - 1]

        if user_input in CATEGORY_CHOICES:
            return user_input

        print("Invalid selection. Please choose one of the listed categories.")
