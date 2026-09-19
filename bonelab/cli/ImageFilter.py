"""Filter and examine AIM and NIfTI images without changing scalar encoding."""
import argparse
from datetime import datetime
from pathlib import Path

import numpy as np

from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.image_info import print_image_info


def image_format(filename):
    name = str(filename).lower()
    if name.endswith('.aim'):
        return 'aim'
    if name.endswith(('.nii', '.nii.gz')):
        return 'nifti'
    raise ValueError('Supported image formats are .aim, .nii, and .nii.gz.')


def update_checked(algorithm):
    errors = []
    observer = algorithm.AddObserver('ErrorEvent', lambda obj, event: errors.append(event))
    try:
        algorithm.Update()
    finally:
        algorithm.RemoveObserver(observer)
    if errors or (hasattr(algorithm, 'GetErrorCode') and algorithm.GetErrorCode()):
        raise RuntimeError(f'{algorithm.GetClassName()} failed; see VTK error output.')


def read_image(filename, label="Input"):
    kind = image_format(filename)
    if not Path(filename).is_file():
        raise ValueError(f'Cannot find input image: {filename}')
    if kind == 'aim':
        from vtkbone import vtkboneAIMReader
        reader = vtkboneAIMReader()
        reader.DataOnCellsOff()
    else:
        from vtkmodules.vtkIOImage import vtkNIFTIImageReader
        reader = vtkNIFTIImageReader()
    reader.SetFileName(str(filename))
    update_checked(reader)
    image = reader.GetOutput()
    scalars = image.GetPointData().GetScalars()
    if scalars is None or not scalars.GetNumberOfTuples():
        raise ValueError('Input image has no scalar data.')
    if scalars.GetNumberOfComponents() != 1 or (kind == 'nifti' and reader.GetTimeDimension() > 1):
        raise ValueError('ImageFilter requires a three-dimensional scalar image.')
    print(f'\n{label} image:')
    print_image_info(filename, image)
    return reader, image


def image_array(image):
    from vtkmodules.util.numpy_support import vtk_to_numpy
    return vtk_to_numpy(image.GetPointData().GetScalars()).reshape(image.GetDimensions(), order='F')


def first_voxel_origin(image):
    spacing = np.asarray(image.GetSpacing())
    direction = np.array([[image.GetDirectionMatrix().GetElement(i, j) for j in range(3)] for i in range(3)])
    return np.asarray(image.GetOrigin()) + direction @ (np.asarray(image.GetExtent()[::2]) * spacing)


def array_image(data, template, offset=(0, 0, 0), factor=1):
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.util.numpy_support import numpy_to_vtk
    image = vtkImageData()
    image.SetDimensions(*data.shape)
    spacing = np.asarray(template.GetSpacing())
    direction = np.array([[template.GetDirectionMatrix().GetElement(i, j) for j in range(3)] for i in range(3)])
    image.SetOrigin(*(first_voxel_origin(template) + direction @ (np.asarray(offset) * spacing)))
    image.SetSpacing(*(spacing * factor))
    image.SetDirectionMatrix(template.GetDirectionMatrix())
    image.GetPointData().SetScalars(numpy_to_vtk(data.ravel(order='F'), deep=True,
                                               array_type=template.GetScalarType()))
    return image


def output_allowed(input_filename, output_filename, overwrite):
    image_format(output_filename)
    if Path(input_filename).resolve() == Path(output_filename).resolve():
        raise ValueError('Output must differ from the input image.')
    if Path(output_filename).exists() and not overwrite:
        answer = input(f'File "{output_filename}" already exists. Overwrite? [y/n]: ')
        if answer.lower() not in ('y', 'yes'):
            print('Not overwriting. Exiting...')
            return False
    return True


def shifted_matrix(matrix, offset):
    from vtkmodules.vtkCommonMath import vtkMatrix4x4
    result = vtkMatrix4x4()
    if matrix is not None:
        result.DeepCopy(matrix)
    for i in range(3):
        result.SetElement(i, 3, result.GetElement(i, 3)
                          + sum(result.GetElement(i, j) * offset[j] for j in range(3)))
    return result


def write_image(filename, image, reader, operation):
    """Preserve AIM logs and NIfTI qform/sform, including grid shifts."""
    from vtkmodules.vtkCommonDataModel import vtkImageData
    output = vtkImageData()
    output.DeepCopy(image)
    origin = first_voxel_origin(image)
    source_nifti = reader.IsA('vtkNIFTIImageReader')
    kind = image_format(filename)
    if kind == 'nifti':
        from vtkmodules.vtkIOImage import vtkNIFTIImageWriter
        writer = vtkNIFTIImageWriter()
        # Store spatial shifts in the forms, not a VTK origin the format might ignore.
        output.SetOrigin(0, 0, 0)
        if source_nifti:
            writer.SetNIFTIHeader(reader.GetNIFTIHeader())
            writer.SetTimeDimension(reader.GetTimeDimension())
            writer.SetTimeSpacing(reader.GetTimeSpacing())
            writer.SetRescaleSlope(reader.GetRescaleSlope())
            writer.SetRescaleIntercept(reader.GetRescaleIntercept())
            writer.SetQFac(reader.GetQFac())
            qform, sform = reader.GetQFormMatrix(), reader.GetSFormMatrix()
            if qform is not None:
                writer.SetQFormMatrix(shifted_matrix(qform, origin))
            if sform is not None:
                writer.SetSFormMatrix(shifted_matrix(sform, origin))
            if qform is None and sform is None:
                writer.SetQFormMatrix(shifted_matrix(None, origin))
        else:
            writer.SetQFormMatrix(shifted_matrix(None, origin))
    else:
        from vtkbone import vtkboneAIMWriter
        writer = vtkboneAIMWriter()
        if source_nifti:
            form = reader.GetSFormMatrix() or reader.GetQFormMatrix()
            if form is not None:
                linear = np.array([[form.GetElement(i, j) for j in range(3)] for i in range(3)])
                if not np.allclose(linear, np.eye(3), atol=1e-6):
                    raise ValueError('AIM cannot represent this NIfTI orientation; write NIfTI to preserve it.')
                origin = np.asarray(form.MultiplyPoint((*origin, 1)))[:3]
                output.SetOrigin(*origin)
            if reader.GetRescaleSlope() not in (0, 1) or reader.GetRescaleIntercept() != 0:
                raise ValueError('AIM cannot preserve NIfTI intensity scaling; write NIfTI instead.')
        scalar_name = output.GetScalarTypeAsString()
        if scalar_name not in ('char', 'signed char', 'short', 'float'):
            raise ValueError(f'AIM cannot preserve scalar type {scalar_name}; use NIfTI output.')
        processing_log = reader.GetProcessingLog() if reader.IsA('vtkboneAIMReader') else ''
        writer.SetProcessingLog((processing_log or '') + f'\n{datetime.now().isoformat()} blImageFilter {operation}\n'
                                + f'Requested output origin (mm): {tuple(origin)}\n')
        # AIM uses integer voxel positions, so block-center shifts may be inexact.
        position = origin / np.asarray(output.GetSpacing())
        if not np.allclose(position, np.rint(position), rtol=0, atol=1e-5):
            print('WARNING: AIM stores its position in whole output voxels. The requested '
                  'block-center origin may be rounded by the AIM writer; use NIfTI for exact alignment.')
    writer.SetFileName(str(filename))
    writer.SetInputData(output)
    update_checked(writer)
    if not Path(filename).is_file():
        raise RuntimeError(f'Output was not written: {filename}')
    print('Saved:', filename)
    # Report actual stored geometry (especially AIM integer-position rounding).
    _, stored = read_image(filename, label="Output")
    return stored


def histogram(image):
    values = image_array(image)
    counts, edges = np.histogram(values, bins=128)
    print('!> Value range                Count')
    for i in np.flatnonzero(counts):
        print(f'!> {edges[i]:10.3f}–{edges[i+1]:10.3f} {counts[i]:12d}')


def thres(input_filename, output_filename, range, overwrite=False, func=None):
    if range[0] > range[1]:
        raise ValueError('Threshold minimum must not exceed maximum.')
    if not output_allowed(input_filename, output_filename, overwrite):
        return
    reader, image = read_image(input_filename)
    data = image_array(image)
    result = np.where((data >= range[0]) & (data <= range[1]), data, 0).astype(data.dtype)
    write_image(output_filename, array_image(result, image), reader, f'thres range={range}')


def subvol(input_filename, output_filename, voi, overwrite=False, func=None):
    if not output_allowed(input_filename, output_filename, overwrite):
        return
    reader, image = read_image(input_filename)
    extent = image.GetExtent()
    if any(voi[i] > voi[i+1] or voi[i] < extent[i] or voi[i+1] > extent[i+1]
           for i in (0, 2, 4)):
        raise ValueError('VOI must be ordered, inclusive bounds inside the input extent.')
    start = np.array(voi[::2]) - np.array(extent[::2])
    stop = np.array(voi[1::2]) - np.array(extent[::2]) + 1
    data = image_array(image)[tuple(slice(a, b) for a, b in zip(start, stop))]
    write_image(output_filename, array_image(data, image, offset=start), reader, f'subvol voi={voi}')


def exam(input_filename, func=None):
    _, image = read_image(input_filename)
    histogram(image)


def reduction_factor(value):
    try:
        factor = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('Reduction factor must be an integer >= 2.')
    if factor < 2:
        raise argparse.ArgumentTypeError('Reduction factor must be >= 2.')
    return factor


def reduced_filename(filename, factor):
    path = Path(filename)
    extension = path.name[-7:] if path.name.lower().endswith('.nii.gz') else path.suffix
    return str(path.with_name(path.name[:-len(extension)] + f'_R{factor:02d}' + extension))


def reduce_array(data, factor):
    """Block majority for char segmentation; rounded mean for signed short."""
    if not isinstance(factor, (int, np.integer)) or factor < 2:
        raise ValueError('Reduction factor must be an integer >= 2.')
    shape = np.asarray(data.shape) // factor
    if data.ndim != 3 or np.any(shape < 1):
        raise ValueError('Factor must not exceed any input image dimension.')
    if data.dtype.kind in 'iu' and data.dtype.itemsize == 1:
        counts = np.zeros(128, dtype=np.int64)
        for plane in data:
            if plane.min() < 0 or plane.max() > 127:
                raise ValueError('Binary char input must use background 0 and one foreground value in 1–127.')
            counts += np.bincount(plane.ravel(), minlength=128)
        positive = np.flatnonzero(counts[1:]) + 1
        if len(positive) > 1:
            raise ValueError('Binary reduction requires one foreground value; multiple positive labels found.')
        label = int(positive[0]) if len(positive) else 0
        mode = 'binary majority (ties become background)'
    elif data.dtype == np.dtype('int16'):
        label = None
        mode = 'raw mean (nearest integer; half-way ties to even)'
    else:
        raise ValueError('Reduce supports char binary data or signed short raw data.')
    result = np.empty(tuple(shape), dtype=data.dtype)
    for x in range(shape[0]):
        block = data[x*factor:(x+1)*factor, :shape[1]*factor, :shape[2]*factor]
        blocks = block.reshape(factor, shape[1], factor, shape[2], factor)
        if label is not None:
            votes = np.count_nonzero(blocks, axis=(0, 2, 4))
            result[x] = (votes > factor**3 / 2) * label
        else:
            means = blocks.sum(axis=(0, 2, 4), dtype=np.int64) / factor**3
            result[x] = np.rint(means).astype(data.dtype)
    return result, mode


def reduce(input_filename, factor, overwrite=False, func=None):
    output_filename = reduced_filename(input_filename, factor)
    if not output_allowed(input_filename, output_filename, overwrite):
        return
    reader, image = read_image(input_filename)
    result, mode = reduce_array(image_array(image), factor)
    trimmed = np.array(image.GetDimensions()) % factor
    print('Reduction mode:', mode)
    print(f'Reduction factor: {factor}; output: {output_filename}')
    if trimmed.any():
        print(f'WARNING: Trimming incomplete blocks at upper X/Y/Z boundaries: {tuple(trimmed)} voxels.')
    output = array_image(result, image, offset=np.full(3, (factor - 1) / 2), factor=factor)
    write_image(output_filename, output, reader, f'reduce factor={factor}; {mode}; trimmed={tuple(trimmed)}')


def create_parser():
    parser = argparse.ArgumentParser(prog='blImageFilter', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='All commands accept .aim, .nii, and .nii.gz.\n\n'
               'Examples:\n  blImageFilter reduce vertebra.aim --factor 2\n'
               '  blImageFilter thres vertebra.aim threshold.aim --range 100 127\n'
               '  blImageFilter subvol vertebra.aim crop.aim --voi 0 49 0 49 0 49\n'
               '  blImageFilter exam vertebra.aim')
    commands = parser.add_subparsers(dest='command', required=True)
    for name, function in [('thres', thres), ('subvol', subvol), ('exam', exam), ('reduce', reduce)]:
        sub = commands.add_parser(name)
        sub.add_argument('input_filename', help='Input .aim, .nii, or .nii.gz image.')
        if name in ('thres', 'subvol'):
            sub.add_argument('output_filename', help='Output .aim, .nii, or .nii.gz image.')
        if name == 'thres':
            sub.add_argument('--range', type=int, nargs=2, default=[0, 10], metavar=('MIN', 'MAX'), help='Inclusive values to keep (default: 0 10).')
        if name == 'subvol':
            sub.add_argument('--voi', type=int, nargs=6, default=[0, 1, 0, 1, 0, 1], help='Inclusive XMIN XMAX YMIN YMAX ZMIN ZMAX voxel indices.')
        if name == 'reduce':
            sub.add_argument('--factor', type=reduction_factor, required=True,
                             help='Integer >= 2. Majority for char, mean for short; output suffix _R02, _R03, etc. Incomplete blocks are trimmed.')
        if name != 'exam':
            sub.add_argument('--overwrite', action='store_true', help='Overwrite existing output without asking.')
        sub.set_defaults(func=function)
    return parser


def main(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)
    print(echo_arguments('ImageFilter', vars(args)))
    kwargs = vars(args).copy()
    del kwargs['command']
    try:
        args.func(**kwargs)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
