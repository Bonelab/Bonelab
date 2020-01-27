
# Imports
import argparse
import os
import SimpleITK as sitk
import glob

from bonelab.util.echo_arguments import echo_arguments

def PseudoCT(input_directory, output_filename, expression, overwrite=False, verbose=False):
    # Python 2/3 compatible input
    from six.moves import input

    # Check if output exists and should overwrite
    if os.path.isfile(output_filename) and not overwrite:
        result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_filename))
        if result.lower() not in ['y', 'yes']:
            print('Not overwriting. Exiting...')
            os.sys.exit()

    if output_filename.lower().endswith('aim'):
        os.sys.exit('[ERROR] Cannot write to AIM. Please write to an intermediate type (say, .nii) and then use blImageConvert to convert to AIM.')

    # First, we assume it is a DICOM series. If GDCM finds no DICOM files
    # we assume it is otherwise
    is_dicom = True
    sitk.ProcessObject.GlobalWarningDisplayOff()
    filenames = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(input_directory)
    sitk.ProcessObject.GlobalWarningDisplayOn()
    filenames = [x for x in filenames]

    if len(filenames)==0:
        is_dicom = False
        filenames = glob.glob(os.path.join(input_directory, expression))
        filenames.sort()
    print('Found {} files'.format(len(filenames)))
    if len(filenames) < 0:
        os.sys.exit('Found no files')
    if verbose:
        print('Filenames: {}'.format(filenames))

    print('Reading in {} files'.format(len(filenames)))
    image = sitk.ReadImage(filenames)

    print('Writing to ' + output_filename)
    sitk.WriteImage(image, output_filename)

def main():
    # Setup description
    description='''Convert a series of 2D images to one 3D image

Example usage:
    blPseudoCT ~/.bldata/dicom dicom.nii

There are a great deal of details in the DICOM standard of which not
all are handled by this function. If you experience nuanced outputs,
please consult a commercial DICOM importer.

Stacking of slices will be determined by GDCM if the input is a DICOM
series, otherwise an alpha-numeric sort.

If you are not reading in a DICOM, it is highly recommended to set a
matching expression with `-e` to avoid extra files - like .DS_store,
text files, other images - from being input into the stack. If the
script fails, this is almost always the problem. `expression` is
ignored for DICOM data.

The output cannot be an AIM type. If you require an AIM, please write
to an intermediate type (say, .nii) and then convert to AIM using
`blImageConvert`.
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blPseudoCT",
        description=description
    )
    parser.add_argument('input_directory', help='Input image')
    parser.add_argument('output_filename', help='Output converted image')
    parser.add_argument( '-e', '--expression', default='*', type=str,
                        help='An expression for matching files (default: %(default)s)')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('PseudoCT', vars(args)))

    # Run program
    PseudoCT(**vars(args))

if __name__ == '__main__':
    main()
