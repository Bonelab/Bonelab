
# Imports
import argparse
import os
import subprocess

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.download_data import \
    BL_DATA_DEFAULT_URL, BL_DATA_DIRECTORY_ENVIRONMENT_VARIABLE, BL_DATA_DIRECTORY_DEFAULT

def DownloadData(url, output_directory, no_verify):
    # Python 2/3 compatible input
    from six.moves import input
    
    if not no_verify:
        print('Locations:')
        print('  url:              {}'.format(url))
        print('  output_directory: {}'.format(output_directory))
        result = input('Are these location OK? [y/n]: ')
        if result.lower() not in ['y', 'yes']:
            print('Exiting...')
            os.sys.exit()

    # Create directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Run commands
    command = ['svn', 'export', '--force', url, output_directory]
    failed = False
    try:
        output = subprocess.check_output(command)
    except subprocess.CalledProcessError as e:
        failed = True
    except OSError as e:
        failed = True

    if failed:
        os.sys.exit('[ERROR] Could not execute download. Do you have SVN installed?')
    
    if not os.path.isdir(output_directory):
        os.sys.exit('[ERROR] An unkown error occured where the output directory was not created')

    print('Successfully downloaded')

def main():
    # Set constant variables
    environment_location = os.environ.get(BL_DATA_DIRECTORY_ENVIRONMENT_VARIABLE)
    output_directory = os.getenv(BL_DATA_DIRECTORY_ENVIRONMENT_VARIABLE, BL_DATA_DIRECTORY_DEFAULT)

    description='''Download the bonelab dataset.

This function fetches the bonelab dataset and stores it locally on your achine.
This repository is good for testing scripts and creating simple programs.

The default URL is \"{BL_DATA_DEFAULT_URL}\". This can be changed with the `--url` flag.

The output directory is resolved in the following order:
    - First, it is assigned to ~/.bldata (Currently \"{BL_DATA_DIRECTORY_DEFAULT}\")
    - Next, if the environment variable {ENV_VAR} is set, it defaults there (Current \"{environment_location}\")
    - Finally, it can be specified at the command line with the flag `--output_directory``
Note that the order of precedence is `--output_directory` > {ENV_VAR} > ~/.bldata

`svn export` is used for downloading the data. This required you to have svn installed on your system.
'''.format(
        BL_DATA_DEFAULT_URL=BL_DATA_DEFAULT_URL,
        BL_DATA_DIRECTORY_DEFAULT=BL_DATA_DIRECTORY_DEFAULT,
        ENV_VAR=BL_DATA_DIRECTORY_ENVIRONMENT_VARIABLE,
        environment_location=environment_location
    )

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blDownloadData",
        description=description
    )
    parser.add_argument('--url', default=BL_DATA_DEFAULT_URL, help='URL for downloading data')
    parser.add_argument('--output_directory', default=output_directory, help='Local directory to store data in')
    parser.add_argument('--no_verify', '-n', action='store_true', help='Prompt user to verify url and output_directory')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('DownloadData', vars(args)))

    # Run program
    DownloadData(**vars(args))

if __name__ == '__main__':
    main()
