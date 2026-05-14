
def print_brief_help():
    print('tt - command-line time tracker')
    print()
    print('Commands:')
    commands = [
        ('start',   'Open a new work package'),
        ('stop',    'Close the current work package'),
        ('status',  'Show the current open work package'),
        ('note',    'Add a note to the current work package'),
        ('tag',     'Add tags to the current work package'),
        ('off',     'Record a day off or holiday'),
        ('day',     'Per-day overview: clock-in, clock-out, break, worked'),
        ('log',     'Total time per activity, optionally filtered by date range'),
        ('report',  'Aggregated daily report per work package'),
        ('calview', 'Monthly calendar view with daily durations'),
        ('summary', 'Monthly utilization summary with 12-month ASCII chart'),
        ('balance', 'Weekly hours saldo since a start date'),
        ('csv',     'Export all entries as pipe-separated CSV'),
        ('edit',    'Open the time entry database in $EDITOR'),
        ('ect',     'Edit current timebox notes in $EDITOR'),
        ('push',    'Write times to an xlsx timesheet file'),
    ]
    width = max(len(cmd) for cmd, _ in commands)
    for cmd, desc in commands:
        print('  %-*s  %s' % (width, cmd, desc))
    print()
    print("Run 'tt help' for full documentation.")


def print_help():
    print('tt is a simple command-line time tracking tool.')
    print()
    print('It stores all the information you add in a JSON-formatted time entry database, located  \n'
          'either at the location you specify in the environment variable SHEET_FILE, or by default \n'
          'in ${HOME}/.tt-sheet.json, in case you don\'t set your SHEET_FILE.')
    print()
    print('Usage:')
    print('tt COMMAND [PARAM_0] .. [PARAM_n]')
    print()
    print('Commands: ')
    print('  start [WORK_PACKAGE] [STARTING_TIME] \n'
          '    Description:\n'
          '      Opens a new work package with the supplied name, starting at the supplied time\n'
          '    Examples:\n'
          '      tt start cleaning 10:30\n'
          '      tt start cleaning 1030\n'
          '      tt start cleaning now')
    print()
    print('  stop [END_TIME]\n'
          '    Description:\n'
          '      Closes an open work package at the supplied time\n'
          '    Examples:\n'
          '      tt stop 10:30\n'
          '      tt stop 1030\n'
          '      tt stop now')
    print()
    print('  note [TEXT]\n'
          '    Description:\n'
          '      Adds a note to an open work package\n'
          '    Examples:\n'
          '      tt note x\n'
          '      tt note \'The quick brown fox humps the lazy bear\'')

    print()
    print('  ect | edit-current-timebox\n'
          '    Description:\n'
          '      Edits the notes of the current timebox in an editor of your choosing, yaml formatted. \n'
          '      For information on how to set the editor, please refer to the help entry of the <<edit>> command\n'
          '    Examples:\n'
          '      tt ect\n'
          '      tt edit-current-timebox')

    print()
    print('  tag [TAG0] [TAG1] [TAG2]\n'
          '    Description:\n'
          '      Adds a list of tags to an open work package\n'
          '    Examples:\n'
          '      tt tag TAGNAME\n'
          '      tt tag \'housework\' \'#makeherproud\'')

    print()
    print('  edit \n'
          '    Description:\n'
          '      Opens your time entry database located at ${SHEET_FILE} on an editor of your choosing. The editor\n'
          '      needs to be specified by setting another environment variable: export EDITOR=\'vim\'\n'
          '      Saving and exiting the editor, updates the time entry db with the new info.\n'
          '      Graphical text editors, such as kate, gedit or sublime ar supported just as well.\n'
          '    Examples:\n'
          '      tt edit')

    print()
    print('  csv \n'
          '    Description:\n'
          '      Lists all your individual entries in a comma-separated format, for ease of import into spreadsheet\n'
          '      editors such as LibreOffice Sheets. The separator is the pipe symbol.\n'
          '    Examples:\n'
          '      tt csv\n'
          '      tt csv --no-color > /tmp/allentries.csv ; libreoffice /tmp/allentries.csv')

    print()
    print('  status \n'
          '    Description:\n'
          '      Shows all information pertaining to an open work package or an appropriate message, if one cannot\n'
          '      be found. \n'
          '    Examples:\n'
          '      tt status\n'
          '      tt status --no-color')
    print()
    print('  report [WORK_PACKAGE] \n'
          '    Description:\n'
          '      Creates an aggregated daily report for the work package you specify as parameter. It creates one\n'
          '      aggregated entry per day, based on the entire database content. If you need to restrict the report\n'
          '      to certain periods, such as a specific month, feel free to pipe the output through grep or other\n'
          '      cli tools. If no work package is specified, all activities will be reported.\n'
          '      By default, the report assumes you work 8 hours per day. You can change this by setting the\n'
          '      environment variable TT_HOURS_PER_DAY to the number of hours you work per day.\n'
          '    Examples:\n'
          '      tt report\n'
          '      tt report cleaning\n'
          '      tt report cleaning --no-color\n'
          '      tt report cleaning --no-color | grep 2019-03 ')
    print()
    print('  log [START_DATETIME] [END_DATETIME] \n'
          '    Description:\n'
          '      Prints a log of the total time spent on each activity, optionally filtered by activities started\n'
          '      within a given time period\n'
          '    Examples:\n'
          '      tt log\n'
          '      tt log 2023-11-13\n'
          '      tt log 2023-11-13 2023-11-15T13:00:00')
    print()
    print('  calview [MONTH] [YEAR] \n'
          '    Description:\n'
          '      Renders a monthly workday calendar (Monday-Friday) with daily aggregated package durations.\n'
          '      The [YEAR] parameter is optional; if omitted, it defaults to the current year. \n'
          '    Examples:\n'
          '      tt calview 12\n'
          '      tt calview 11 --no-color\n'
          '      tt calview 10 2030')
    print()
    print('  off [NAME] [DATE | START_DATE END_DATE]\n'
          '    Description:\n'
          '      Records a day off (holiday, sick day, etc.) into the database. Accepts a single date\n'
          '      or a range of dates. Days off are excluded from target working time in summary and balance.\n'
          '    Examples:\n'
          '      tt off vacation 2026-12-24\n'
          '      tt off vacation 2026-12-24 2026-12-31')
    print()
    print('  day \n'
          '    Description:\n'
          '      Prints a per-day overview of first clock-in, last clock-out, break time, and total worked time.\n'
          '    Examples:\n'
          '      tt day\n'
          '      tt day --no-color')
    print()
    print('  balance \n'
          '    Description:\n'
          '      Shows a weekly hours saldo table since a start date, accumulating over- and under-time.\n'
          '      Requires the environment variable TT_SALDO_START_DATE (YYYY-MM-DD).\n'
          '      Optionally set TT_SALDO_START_HOURS to a decimal initial saldo (e.g. 12.5 or -3).\n'
          '      Respects TT_HOURS_PER_DAY and days recorded with tt off.\n'
          '    Examples:\n'
          '      TT_SALDO_START_DATE=2026-01-01 tt balance\n'
          '      TT_SALDO_START_DATE=2026-01-01 TT_SALDO_START_HOURS=-5 tt balance')
    print()
    print('  push [XLSX_PATH]\n'
          '    Description:\n'
          '      Writes daily start, end, and break times into an xlsx timesheet file (column F/G/H).\n'
          '      Days off are written to column L and set the Soll column (E) to 0.\n'
          '      Requires openpyxl: pip install openpyxl --break-system-packages\n'
          '      The xlsx path can also be set via TT_XLSX_FILE.\n'
          '    Examples:\n'
          '      tt push ~/timesheet.xlsx\n'
          '      TT_XLSX_FILE=~/timesheet.xlsx tt push')
    print()
    print('  summary [MONTH] [YEAR] [--with-categories] \n'
          '    Description:\n'
          '      Prints a monthly activity share summary and an ASCII utilization chart for the last 12 months.\n'
          '      Use --with-categories (or --categories) to include stacked category lines in the chart.\n'
          '      If [MONTH] is omitted, it defaults to the current local month. [YEAR] is optional.\n'
          '    Examples:\n'
          '      tt summary\n'
          '      tt summary 03\n'
          '      tt summary 03 2026\n'
          '      tt summary --with-categories\n'
          '      tt summary 03 2026 --categories')
    print()
    print('For the full documentation, check out http://github.com/dribnif/tt')
