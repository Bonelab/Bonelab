
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

# Specify type parameters
EXTRACT_FIELDS_SUPPORTED_TYPES = {
    'float':    vtk.VTK_FLOAT,
    'char':     vtk.VTK_CHAR,
    'short':    vtk.VTK_SHORT
}

def ExtractFields(
    input_model,
    output_image,
    field_name,
    outside_value=0.0,
    lower_threshold=0.0,
    upper_threshold=0.0,
    output_type='float'):

    # Python 2/3 compatible input
    from six.moves import input

    # Check requested output type
    output_type = output_type.lower()
    if output_type not in EXTRACT_FIELDS_SUPPORTED_TYPES.keys():
        print('Valid output types: {}'.format(', '.join(EXTRACT_FIELDS_SUPPORTED_TYPES.keys())))
        os.sys.exit('[ERROR] Requested type {} not supported'.format(output_type))

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
    print('')

    if output_type == 'float':
        print('Not rescaling data')
    else:
        print('Rescaling data into {} dynamic range'.format(output_type))
        # Hack to get data type range
        source = vtk.vtkImageEllipsoidSource()
        source.SetWholeExtent(0, 1, 0, 1, 0, 0)
        source.SetCenter(0, 0, 0)
        source.SetRadius(0, 0, 0)
        source.SetOutputScalarType(EXTRACT_FIELDS_SUPPORTED_TYPES[output_type])
        source.Update()

        # Compute min/max
        if lower_threshold == upper_threshold:
            scalar_range = vtkImage.GetScalarRange()
        else:
            scalar_range = [lower_threshold, upper_threshold]
        dtype_range = [
            0,
            source.GetOutput().GetScalarTypeMax()
        ]
        print(' Image range:  {}'.format(vtkImage.GetScalarRange()))
        print(' Input range:  {}'.format(scalar_range))
        print(' Output range: {}'.format(dtype_range))

        # Note the equation for shift/scale:
        #   u = (v + ScalarShift)*ScalarScale
        m = float(dtype_range[1] - dtype_range[0]) / float(scalar_range[1] - scalar_range[0])
        b = float(dtype_range[1] - m*scalar_range[1])
        b = b/m

        print(' Shift: {}'.format(b))
        print(' Scale: {}'.format(m))

        scaler = vtk.vtkImageShiftScale()
        scaler.SetInputData(vtkImage)
        scaler.SetShift(b)
        scaler.SetScale(m)
        scaler.ClampOverflowOn()
        scaler.SetOutputScalarType(EXTRACT_FIELDS_SUPPORTED_TYPES[output_type])
        scaler.Update()
        vtkImage = scaler.GetOutput()

        print(' Output image range:  {}'.format(vtkImage.GetScalarRange()))
    print('')

    # Write image
    print('Saving image ' + output_image)
    writer = get_vtk_writer(output_image)
    if writer is None:
        os.sys.exit('[ERROR] Cannot find writer for file \"{}\"'.format(output_image))
    writer.SetInputData(vtkImage)
    writer.SetFileName(output_image)
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

If you are using this script to visualize a field with uct_3d, the
output_type must be either char or short. If lower_threshold and
upper_threshold are specified and not equal, the field will be
truncated between these two values and rescaled to the min/max of
the datatype range. If lower_threshold equals upper_threshold,
the dynamic range of the image will be mapped to the range of the
output type.

Valid output types include: {convert_types}
'''.format(
        valid_fields=', '.join(valid_fields()),
        convert_types=', '.join(EXTRACT_FIELDS_SUPPORTED_TYPES.keys())
    )

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blExtractFields",
        description=description
    )
    parser.add_argument('input_model', help='Input N88 model')
    parser.add_argument('output_image', help='Output image filename')
    parser.add_argument('-f', '--field_name', default='StrainEnergyDensity', type=str,
                        help='Field name to extract (default: %(default)s)')
    parser.add_argument('-o', '--outside_value', default=0.0, type=float,
                        help='Value to assign voxels where there is no field (default: %(default)s)')
    parser.add_argument('-l', '--lower_threshold', default=0.0, type=float,
                        help='If output type is not float, what is the lower threshold for rescaling? (default: %(default)s)')
    parser.add_argument('-u', '--upper_threshold', default=0.0, type=float,
                        help='If output type is not float, what is the upper threshold for rescaling? (default: %(default)s)')
    parser.add_argument('-t', '--output_type', default='float', type=str,
                        help='Specify the output type (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ExtractFields', vars(args)))

    # Run program
    ExtractFields(**vars(args))

if __name__ == '__main__':
    main()
