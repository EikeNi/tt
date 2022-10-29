from tt.exceptz.exceptz import AlreadyOn
from tt.dataaccess.utils import get_data_store
from tt.dateutils.dateutils import formatted_str_for_isodate_str

def action_free(colorizer, name, time):
    data = get_data_store().load()
    holiday = data['holiday']

    # if work and 'end' not in work[-1] and 'free' not in work[-1]:
    #     raise AlreadyOn("You are already working on %s. Stop it or use a "
    #                     "different sheet." % (colorizer.yellow(work[-1]['name']),))

    entry = {
        'name': name,
        'date': time,
    }

    holiday.append(entry)
    get_data_store().dump(data)

    print('You are off work on ' + colorizer.yellow(formatted_str_for_isodate_str(time, '%d.%m.%y'))
          + ' due to ' + colorizer.green(name) + '.')
