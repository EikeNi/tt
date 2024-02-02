from tt.dataaccess.utils import get_data_store
from tt.dateutils.dateutils import formatted_str_for_isodate_str, parse_isodate

from datetime import timedelta


def action_off(colorizer, name, time):
    data = get_data_store().load()
    holiday = data["holiday"]

    if isinstance(time, list):
        start_date = parse_isodate(time[0])
        end_date = parse_isodate(time[-1])
    else:
        start_date = parse_isodate(time)
        end_date = start_date

    delta = timedelta(days=1)

    current_date = start_date
    while current_date <= end_date:
        entry = {
            "name": name,
            "date": current_date.strftime("%Y-%m-%dT"),
        }
        holiday.append(entry)
        get_data_store().dump(data)

        print(
            "You are off work on "
            + colorizer.yellow(
                formatted_str_for_isodate_str(
                    current_date.strftime("%Y-%m-%dT"), "%d.%m.%y"
                )
            )
            + " due to "
            + colorizer.green(name)
            + "."
        )
        current_date += delta
