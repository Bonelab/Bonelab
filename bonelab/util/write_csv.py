'''Utility function for writing to a csv file'''

import os


def write_csv(entry, csv_file, delimiter=','):
    '''Write data to a CSV file.

    This function handles creating the CSV file if it doesn't exist,
    appending to said file, and managing header formatting.

    Note that if you want specific formatting on numerics - i.e. precision
    - the numerical value should be passed as a string and precision set
    before calling this function.

    Note that the input `entry` should be a collections.OrderedDict object
    to preserve the ordering of the keys between printing.

    Args:
        entry (OrderedDict):    Input dictionary of entry to write
        csv_file (string):      Filename to write to
        delimiter (string):     Delimiter to be used for writing

    Returns:
        None
    '''
    # Create formating strings
    format_header = ['{{{}}}'.format(x) for x in entry.keys()]
    format_string = delimiter.join(format_header)

    # If we doesn't exist, need to write header
    if not os.path.exists(csv_file):
        with open(csv_file, 'w') as f:
            f.write(delimiter.join(entry.keys()) + os.linesep)

    # Write entry
    with open(csv_file, 'a') as f:
        f.write(format_string.format(**entry) + os.linesep)
