
# Imports
import argparse
import os
import re

from bonelab.util.echo_arguments import echo_arguments

def scrub_vms_extension(input_files, verbose):
    # Python 2/3 compatible input
    from six.moves import input

    n_files = len(input_files)
    if n_files == 0:
        print('No files supplied. Exiting...')
        return

    processed = 0
    skipped = 0
    pattern = r'(;[0-9]+)$'
    for filename in input_files:
        m = re.search(pattern, filename)

        # Match found?
        if not m:
            skipped+=1
            if verbose:
                print('Skipping ' + filename)
            continue

        # Format filename
        extension = m.group(0)
        new_filename = filename.replace(extension, '')

        # Rename
        if verbose:
            print('Renaming ' + filename + ' to ' + new_filename)
        os.rename(filename, new_filename)
        processed+=1

    print('Total files:     {}'.format(n_files))
    print('Processed files: {}'.format(processed))
    print('Skipped files:   {}'.format(skipped))

def main():
    # Setup description
    description='''Remove the version extension from VMS files

Example usage:
    scrub_vms_extension D0001274_OBLIQUE.TIF;1
    scrub_vms_extension data/*.AIM*

If one file with multiple versions are found, they will be overwritten. The
final result will be the last file supplied to this script
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="scrub_vms_extension",
        description=description
    )
    parser.add_argument('input_files', nargs='+', help='Input image')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('scrub_vms_extension', vars(args)))

    # Run program
    scrub_vms_extension(**vars(args))

if __name__ == '__main__':
    main()
