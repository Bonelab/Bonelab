
# Imports
import argparse
import os
from netCDF4 import Dataset
import numpy as np
import vtk

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_writer, handle_filetype_writing_special_cases
from bonelab.util.vtk_util import numpy_to_vtkImageData
from bonelab.util.n88_util import valid_fields, field_to_image


def ExtractFields(input_model, output_image, field_name, outside_value=0.0):
    # Python 2/3 compatible input
    from six.moves import input

    # Read input
    if not os.path.isfile(input_model):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_model))

    # Test field name
    if field_name not in valid_fields():
        print('Valid field names: {}'.format(valid_fields()))
        os.sys.exit('[ERROR] Please provide a valid field name')

    print('Reading elements into image array')
    image, spacing, origin, n_elements = field_to_image(input_model, field_name, outside_value)
    print('  Spacing:            {}'.format(spacing))
    print('  Origin:             {}'.format(origin))
    print('  Dimensions:         {}'.format(image.shape))
    print('  Number of elements: {}'.format(n_elements))
    print('')

    # Convert to VTK
    print('Converting to vtkImageData')
    vtkImage = numpy_to_vtkImageData(image, spacing, origin)

    # Write image
    print('Saving image ' + output_image)
    writer = get_vtk_writer(output_image)
    if writer is None:
        os.sys.exit('[ERROR] Cannot find writer for file \"{}\"'.format(output_image))
    writer.SetInputData(vtkImage)
    writer.SetFileName(output_image)

    # Handle edge cases for each output file type
    handle_filetype_writing_special_cases(
        writer
    )
    writer.Update()

def main():
    # Setup description
    description='''Extract field on elements from N88 model

Take values stored in the elements of a N88 model and extract them
into an image. This can be used for visualization with uct_3d or
for other processing requirements. Possible choices of field names
include: {valid_fields}

Example usage:
    blExtractFields test25a_uniaxial.n88model test25a_sed.aim

Note that the domain of the finite element model does not match
the domain of the image. For voxels that do not have a corresponding
element, a value must still be placed there.

This solution manually indexes the hexahedron elements and may be
slow for very large models.
'''.format(valid_fields=', '.join(valid_fields()))

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blExtractFields",
        description=description
    )
    parser.add_argument('input_model', help='Input N88 model')
    parser.add_argument('output_image', help='Output field')
    parser.add_argument('-f', '--field_name', default='StrainEnergyDensity', type=str,
                        help='Field name to extract (default: %(default)s)')
    parser.add_argument('-o', '--outside_value', default=0.0, type=float,
                        help='Value to assign voxels where there is no field (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ExtractFields', vars(args)))

    # Run program
    ExtractFields(**vars(args))

if __name__ == '__main__':
    main()
