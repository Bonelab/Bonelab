# See https://github.com/Numerics88/n88tools/blob/master/tests/regression/config_regression.py for how this file was defined

import os
import subprocess

'''
A set of helper variables and functions for running tests.

Importantly, `cfg['DOWNLOAD_TESTING_DATA']` defines a function
that can be called to download data from `cfg['REGRESSION_DATA_URL']`
for testing. This data is stored in a local directory define by
`cfg['REGRESSION_DATA_DIRECTORY']`. If the data has already been
downloaded, the download process does not start again. Every
test that requires data should:
    1) Upload the data to `cfg['REGRESSION_DATA_URL']`
    2) Call `cfg['DOWNLOAD_TESTING_DATA']` in the test
See running tests for more examples.
'''

# Setup the configuration file
cfg = {}

cfg['REGRESSION_FILES'] = [
     'test25a.aim'
]

cfg['REGRESSION_DATA_URL'] = "https://github.com/Bonelab/BonelabData/trunk/data/"

cfg['REGRESSION_DATA_DIRECTORY'] = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data'
)

# Define an error observer class
class ErrorObserver:

    def __init__(self):
        self.__ErrorOccurred = False
        self.__ErrorMessage = None
        self.CallDataType = 'string'

    def __call__(self, obj, event, message):
        self.__ErrorOccurred = True
        self.__ErrorMessage = message

    def ErrorOccurred(self):
        occ = self.__ErrorOccurred
        self.__ErrorOccurred = False
        return occ

    def ErrorMessage(self):
        return self.__ErrorMessage
cfg['ERROR_OBSERVER'] = ErrorObserver

# Define a call run mechanic
def run_call(command, stdin=None):
    '''Returns true if call succeeds, false otherwise'''
    try:
        subprocess.check_output(command, stdin=stdin)
    except subprocess.CalledProcessError as e:
        return False
    except OSError as e:
        return False
    return True
cfg['RUN_CALL'] = run_call

# Create download script
def download_testing_data(filename):
    '''Download data used in testing
    
    Typically, this is done for regression testing.
    
    On success, this function returns the full file path. On failure,
    an empty string is returned.
    '''
    input_uri = cfg['REGRESSION_DATA_URL'] + filename
    output_uri = os.path.join(cfg['REGRESSION_DATA_DIRECTORY'], filename)

    # Create output directory if it doesn't exist
    if not os.path.exists(cfg['REGRESSION_DATA_DIRECTORY']):
        os.makedirs(cfg['REGRESSION_DATA_DIRECTORY'])
    
    # If we have already downloaded it, skip
    if os.path.exists(output_uri):
        return output_uri

    # Download
    command = ['svn', 'export', input_uri, output_uri]
    if cfg['RUN_CALL'](command):
        return output_uri
    else:
        return ''
cfg['DOWNLOAD_TESTING_DATA'] = download_testing_data

