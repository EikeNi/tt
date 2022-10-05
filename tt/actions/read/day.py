from __future__ import print_function

from tt.dataaccess.utils import get_data_store
from tt.dateutils.dateutils import *
from tt.actions.utils import reportingutils


def action_day():
    sep = '|'
    data = get_data_store().load()
    work = data['work']

    report=dict()
    for item in work:
        if 'end' in item:
            day = reportingutils.extract_day(item['start'])
            start = isotime_utc_to_local(item['start'])
            end = isotime_utc_to_local(item['end'])
            duration = parse_isotime(item['end']) - parse_isotime(item['start'])
            # duration = duration - timedelta(seconds=duration.seconds)
            try:
                report[day]
            except KeyError:
                report[day] = dict()
                report[day]['work_duration'] = timedelta()
                report[day]['start'] = start
                report[day]['end'] = end
            if report[day]['start'] > start:
                report[day]['start'] = start
            if report[day]['end'] < end:
                report[day]['end'] = end
            report[day]['work_duration'] += duration
    sep = '|'
    for day in sorted(report.keys()):
        print(day, ': ', reportingutils.remove_seconds(report[day]['start'].time()), sep, reportingutils.remove_seconds(report[day]['end'].time()), sep, reportingutils.remove_seconds((report[day]['end'] - report[day]['start']) - report[day]['work_duration']))
    