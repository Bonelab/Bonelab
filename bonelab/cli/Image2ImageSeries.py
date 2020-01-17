
# Imports
import argparse
import os
import SimpleITK as sitk
import numpy as np

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.sitk_helpers import sitk_supported_file_types


def Image2ImageSeries(input_filename, output_filename, extension, number_of_digits=-1, verbose=False, no_rescale=False):
    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    if extension.lower().endswith('aim'):
        os.sys.exit('[ERROR] Aim files are not supported. Please run blImageConvert first.')

    print('Reading input image ' + input_filename)
    image = sitk.ReadImage(input_filename)

    if image.GetNumberOfComponentsPerPixel() != 1:
        os.sys.exit('[ERROR] Currently, only single component images are supported.')

    # Determine number of slices, number of digits for formatting
    z_slices = image.GetSize()[-1]
    n_required_digits= 0
    while z_slices//(10**n_required_digits) > 0:
        n_required_digits+=1
    if n_required_digits > number_of_digits:
        print('  With {} slices, {} digits are required.'.format(z_slices, n_required_digits))
        print('  Rounding number_of_digits to {}'.format(n_required_digits))
        number_of_digits=n_required_digits

    print('Writing to {} with extension {} and {} digits'.format(output_filename, extension, number_of_digits))
    formatter = '{o}_{{:0{n}d}}.{s}'.format(o=output_filename,n=number_of_digits,s=extension)
    filenames = (formatter.format(n) for n in range(z_slices))
    if verbose:
        print('Formatter: {}'.format(formatter))
        print('Filenames: {}'.format(filenames))

    output = image
    if extension not in sitk_supported_file_types:
        print('Could not check supported image types for extension {}'.format(extension))
        print('Trying to write image series without type checking')
    else:
        if image.GetPixelID() in sitk_supported_file_types[extension]['supported_types']:
            print('Found supported pixel type {}. No conversion performed.'.format(image.GetPixelIDTypeAsString()))
        else:
            print('Current pixel type not supported for this writer. Casting pixel value appropriately.')
            print('  Input type: ' + image.GetPixelIDTypeAsString())
            output_type = sitk_supported_file_types[extension]['sitk_cast_type']
            if no_rescale:
                output = sitk.Cast(image, output_type)
            else:
                # Get image min/max
                minmax_filter = sitk.MinimumMaximumImageFilter()
                minmax_filter.Execute(image)
                image_min = minmax_filter.GetMinimum()
                image_max = minmax_filter.GetMaximum()

                # Get output type min/max
                dtype_min = np.iinfo(sitk_supported_file_types[extension]['np_cast_type']).min
                dtype_max = np.iinfo(sitk_supported_file_types[extension]['np_cast_type']).max

                m = float(dtype_max - dtype_min) / float(image_max - image_min)
                b = float(image_max - m*dtype_max)

                if verbose:
                    print('  Image range:  {}'.format([image_min, image_max]))
                    print('  Output range: {}'.format([dtype_min, dtype_max]))
                    print('  Rescale:      {}'.format([m, b]))

                output = sitk.Cast(m*sitk.Cast(image, sitk.sitkFloat32)+b, output_type)
            print('  Output type: ' + output.GetPixelIDTypeAsString())

    print('Writing {} files'.format(z_slices))
    sitk.WriteImage(output, list(filenames))

def main():
    # Setup description
    description='''Convert a 3D image to a series of 2D Images

Example usage:
    blImage2ImageSeries ~/.bldata/test25a.nii temp/test25a

Output files will be numbered according to last dimension slice number
and formatted as follows:
    '{output_filename}_{number}.{extension}'
Output files will be overwritten if they exist. The method will
automatically figure out the number of digits required. However, if you
want your filenames to have a specific number of zeros greater than that
required, please set `number_of_digits`.

AIM files are not supported. It is recommended to use blImageConvert
if you would like to serialize an AIM.
    blImageConvert filename.aim filename.nii
    blImage2ImageSeries filename.nii filename

Currently, only single component images are supported. Please submit
an issue if support for Vector images is required.

Writing of DICOM series is not supported because it requires delicate
handling of the DICOM tags. Please see the SimpleITK DICOM documentation
to write your own DICOM series writer.

Writing is performed using the SimpleITK ImageSeriesWriter. Supported
extension include:
    bmp
    tif tiff
    png
    jpeg jpg

Many filetypes used for 2D images (png, bmp, jpg) only support a limited
number of data types. For this reason, the image may need to be cast to a
supporting type. By default, the algorithm will stretch the dynamic range
of the image to fit optimally inside the new type. However, if you do not
want the datatype to be stretch, set the flag `--no_rescale` to cause
direct conversion. This may cause loss of data, for example when going
from a signed to unsigned type.
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImage2ImageSeries",
        description=description
    )
    parser.add_argument('input_filename', help='Input image')
    parser.add_argument('output_filename', help='Output converted image prefix')
    parser.add_argument('-e', '--extension', default='bmp', type=str,
                        help='Filename extension without a period (default: %(default)s)')
    parser.add_argument('-n', '--number_of_digits', default=-1, type=int,
                        help='Number of digits to format with (default: %(default)d)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--no_rescale', action='store_true', help='Rescale pixel types on casting')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('Image2ImageSeries', vars(args)))

    # Run program
    Image2ImageSeries(**vars(args))

if __name__ == '__main__':
    main()
