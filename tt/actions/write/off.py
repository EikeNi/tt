from tt.exceptz.exceptz import AlreadyOn
from tt.dataaccess.utils import get_data_store
from tt.dateutils.dateutils import formatted_str_for_isodate_str

def action_off(colorizer, name, time):
    data = get_data_store().load()
    holiday = data['holiday']

    entry = {
        'name': name,
        'date': time,
    }

    holiday.append(entry)
    get_data_store().dump(data)

    print('You are off work on ' + colorizer.yellow(formatted_str_for_isodate_str(time, '%d.%m.%y'))
          + ' due to ' + colorizer.green(name) + '.')
