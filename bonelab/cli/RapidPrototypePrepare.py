"""Prepare segmented AIMs: plan primitives, fill interiors, cut, and add material.

Geometry and morphology use voxel coordinates (XYZ), including for anisotropic
images. Transforms map a physical, locally centered primitive into AIM space.
"""
import argparse
from datetime import datetime
from pathlib import Path
import shlex
import warnings

import numpy as np
from scipy import ndimage as ndi

from bonelab.util.image_info import print_image_info


def validate_segmentation(data):
    """Validate native values before casting; return a compact input summary."""
    if data.ndim != 3 or not data.size:
        raise ValueError('Input must be a nonempty three-dimensional image.')
    if not np.isfinite(data).all() or data.min() < 0 or data.max() > 127:
        raise ValueError('Expected segmentation values: background 0, foreground 1–127.')
    if not np.issubdtype(data.dtype, np.integer) and np.any(data != np.floor(data)):
        raise ValueError('Segmentation values must be integers.')
    counts = np.zeros(128, dtype=np.int64)
    for plane in data:
        counts += np.bincount(plane.ravel().astype(np.uint8), minlength=128)
    foreground = int(counts[1:].sum())
    if not foreground:
        raise ValueError('Input contains no foreground voxels.')
    if not counts[0]:
        warnings.warn('Input is entirely foreground; background analysis may be uninformative.')
    return (f'{data.dtype}, range {data.min()}–{data.max()}, '
            f'{np.count_nonzero(counts[1:])} positive values, '
            f'{100 * foreground / data.size:.2f}% foreground')


def morphology(mask, radius, erosion=False):
    """Exact Euclidean ball morphology using slabs with a radius-sized halo."""
    if radius == 0:
        return mask.copy()
    output = np.empty_like(mask)
    # Keep distance-transform temporaries bounded for large AIMs.
    for start in range(0, mask.shape[0], 16):
        end = min(start + 16, mask.shape[0])
        lo, hi = max(0, start - radius - 1), min(mask.shape[0], end + radius + 1)
        slab = mask[lo:hi]
        if erosion:
            padded = np.pad(slab, 1, constant_values=False)
            transformed = (ndi.distance_transform_edt(padded) > radius)[1:-1, 1:-1, 1:-1]
        elif slab.any():
            transformed = ndi.distance_transform_edt(~slab) <= radius
        else:
            transformed = np.zeros_like(slab)
        output[start:end] = transformed[start-lo:end-lo]
    return output


def dilate(mask, radius):
    return morphology(mask, radius)


def erode(mask, radius):
    return morphology(mask, radius, erosion=True)


def solid_body(data, close=10, erosion=6):
    """Fill all but the largest background component, erode, restore input."""
    foreground = data > 0
    if close:
        print(f'Closing foreground (radius {close} voxels)...', flush=True)
        padding = close + 1
        expanded = np.pad(foreground, padding)
        expanded = erode(dilate(expanded, close), close)
        foreground = expanded[padding:-padding, padding:-padding, padding:-padding]
    # Six-connected background: zero-valued image regions are labelled directly.
    print('Labelling background components...', flush=True)
    labels, count = ndi.label(~foreground)
    sizes = np.zeros(count + 1, dtype=np.int64)
    for plane in labels:
        sizes += np.bincount(plane.ravel(), minlength=count + 1)
    sizes[0] = 0
    ordered = np.sort(sizes[1:])[::-1]
    largest = int(ordered[0]) if count else 0
    second = int(ordered[1]) if count > 1 else 0
    total = int(sizes.sum())
    exterior = int(sizes.argmax()) if count else 0
    boundary = np.unique(np.concatenate([
        labels[0].ravel(), labels[-1].ravel(), labels[:, 0].ravel(),
        labels[:, -1].ravel(), labels[:, :, 0].ravel(), labels[:, :, -1].ravel()]))
    touches = bool(exterior and exterior in boundary)
    stats = dict(components=count, largest=largest, second_largest=second,
                 largest_fraction=largest / total if total else 0,
                 remaining=total - largest, largest_touches_boundary=touches)
    # A 2:1 ratio is a diagnostic heuristic, not proof of pore separation.
    if count <= 1 or largest < 2 * second or not touches:
        warnings.warn('Background connectivity suggests trabecular spaces may remain '
                      'connected to the exterior, or the exterior is ambiguous. '
                      'Consider increasing --close and inspecting the result.')
    filled = labels != exterior if count else foreground
    del labels, foreground
    print(f'Eroding filled body (radius {erosion} voxels)...', flush=True)
    core = erode(filled, erosion)
    del filled
    result = data.astype(np.int8, copy=True)
    result[core & (data == 0)] = 127
    return result, stats


def read_transform(filename):
    matrix = np.loadtxt(filename, skiprows=2)
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
        raise ValueError('Transform must contain a finite 4x4 matrix.')
    if (not np.allclose(matrix[3], [0, 0, 0, 1])
            or np.linalg.matrix_rank(matrix[:3, :3]) != 3):
        raise ValueError('Transform must be an invertible affine mapping.')
    return matrix


def write_transform(filename, matrix, overwrite=False):
    with open(filename, 'w' if overwrite else 'x') as stream:
        np.savetxt(stream, matrix, fmt='%.17e', comments='',
                   header='SCANCO TRANSFORMATION DATA VERSION:   10\nR4_MAT:')


def principal_axes(data, center):
    """Return foreground PCA directions as columns in voxel coordinates.

    Accumulate centered second moments one plane at a time. Values are treated
    as segmentation labels, so every positive voxel has equal weight.
    """
    covariance = np.zeros((3, 3), dtype=float)
    total = 0
    for x, plane in enumerate(data):
        y, z = np.nonzero(plane > 0)
        points = np.empty((len(y), 3), dtype=float)
        points[:, 0] = x - center[0]
        points[:, 1] = y - center[1]
        points[:, 2] = z - center[2]
        covariance += points.T @ points
        total += len(y)
    if not total:
        raise ValueError('Cannot compute principal axes without foreground voxels.')
    values, axes = np.linalg.eigh(covariance / total)
    values, axes = values[::-1], axes[:, ::-1].copy()
    # Fix sign ambiguity using the largest image-axis component of each vector.
    for axis in range(3):
        if axes[np.argmax(np.abs(axes[:, axis])), axis] < 0:
            axes[:, axis] *= -1
    if np.linalg.det(axes) < 0:
        axes[:, 2] *= -1
    if values[0] <= 0 or np.any(np.abs(np.diff(values)) <= 1e-3 * values[0]):
        warnings.warn('Nearly equal principal variances make the principal-axis '
                      'orientation ambiguous; inspect the placement.')
    print('Principal variances (first, second, third):', values)
    return axes


def placement(data, spacing, origin, transform_file=None, position=None):
    if transform_file:
        if position is not None:
            raise ValueError('--position cannot be combined with --transform_file.')
        return read_transform(transform_file)
    mode, *offset = position or ('origin', 0., 0., 0.)
    center = np.zeros(3)
    axes = np.eye(3)
    if mode != 'origin':
        counts = np.array([np.count_nonzero(plane) for plane in data])
        total = counts.sum()
        if not total:
            raise ValueError('Cannot position a primitive without foreground voxels.')
        center[0] = np.dot(np.arange(data.shape[0]), counts)
        for plane in data:
            foreground = plane > 0
            center[1] += np.dot(np.arange(data.shape[1]), foreground.sum(axis=1))
            center[2] += np.dot(np.arange(data.shape[2]), foreground.sum(axis=0))
        center /= total
        if mode == 'principal_axes':
            axes = principal_axes(data, center)
    center += axes @ np.asarray(offset)
    matrix = np.eye(4)
    spacing = np.asarray(spacing)
    matrix[:3, :3] = spacing[:, None] * axes / spacing[None, :]
    matrix[:3, 3] = np.asarray(origin) + center * spacing
    return matrix


def primitive_bounds(spacing, origin, primitive, dimensions, matrix):
    """Compare exact primitive support bounds to the image's voxel edges."""
    spacing = np.asarray(spacing)
    linear = matrix[:3, :3] * spacing[None, :] / spacing[:, None]
    center = (matrix[:3, 3] - origin) / spacing
    if primitive in ('cube', 'box'):
        half = np.abs(linear) @ np.broadcast_to(np.asarray(dimensions) / 2, (3,))
    elif primitive == 'sphere':
        half = np.linalg.norm(linear, axis=1) * dimensions[0] / 2
    else:
        half = (np.linalg.norm(linear[:, :2], axis=1) * dimensions[0] / 2
                + np.abs(linear[:, 2]) * dimensions[1] / 2)
    return center - half, center + half


def primitive_is_clipped(shape, spacing, origin, primitive, dimensions, matrix):
    lower, upper = primitive_bounds(spacing, origin, primitive, dimensions, matrix)
    return bool(np.any(lower < -0.5 - 1e-9)
                or np.any(upper > np.asarray(shape) - 0.5 + 1e-9))


def box_mask(local, dimensions):
    half = np.broadcast_to(np.asarray(dimensions) / 2, (3,))
    return np.logical_and.reduce([(v >= -h - 1e-9) & (v < h - 1e-9)
                                  for v, h in zip(local, half)])


def sphere_mask(local, dimensions):
    return sum(v * v for v in local) <= (dimensions[0] / 2) ** 2 + 1e-9


def cylinder_mask(local, dimensions):
    radius, half_length = np.asarray(dimensions) / 2
    return ((local[0] ** 2 + local[1] ** 2 <= radius ** 2 + 1e-9)
            & (local[2] >= -half_length - 1e-9) & (local[2] < half_length - 1e-9))


def box_source(dimensions):
    from vtkmodules.vtkFiltersSources import vtkCubeSource
    source = vtkCubeSource()
    x, y, z = np.broadcast_to(dimensions, (3,))
    source.SetXLength(x)
    source.SetYLength(y)
    source.SetZLength(z)
    return source


def sphere_source(dimensions):
    from vtkmodules.vtkFiltersSources import vtkSphereSource
    source = vtkSphereSource()
    source.SetRadius(dimensions[0] / 2)
    source.SetThetaResolution(64)
    source.SetPhiResolution(64)
    return source


def cylinder_source(dimensions):
    from vtkmodules.vtkFiltersSources import vtkCylinderSource
    from vtkmodules.vtkCommonTransforms import vtkTransform
    from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
    source = vtkCylinderSource()
    source.SetRadius(dimensions[0] / 2)
    source.SetHeight(dimensions[1])
    source.SetResolution(64)
    source.CappingOn()
    # VTK cylinders start along Y; our primitive's length follows local Z.
    rotation = vtkTransform()
    rotation.RotateX(90)
    oriented = vtkTransformPolyDataFilter()
    oriented.SetInputConnection(source.GetOutputPort())
    oriented.SetTransform(rotation)
    return oriented


PRIMITIVES = {
    'sphere': dict(parameters=('DIAMETER',), mask=sphere_mask, source=sphere_source),
    'cube': dict(parameters=('EDGE',), mask=box_mask, source=box_source),
    'box': dict(parameters=('X_LENGTH', 'Y_LENGTH', 'Z_LENGTH'), mask=box_mask, source=box_source),
    'cylinder': dict(parameters=('DIAMETER', 'LENGTH'), mask=cylinder_mask, source=cylinder_source),
}


def normalize_primitive(args, parser):
    """Validate the shape and its dimensions before either command runs."""
    if not args.primitive:
        return
    name, *values = args.primitive
    if name not in PRIMITIVES:
        parser.error('Unknown primitive; choose ' + ', '.join(PRIMITIVES) + '.')
    parameters = PRIMITIVES[name]['parameters']
    if len(values) != len(parameters):
        parser.error(f'--primitive {name} requires {len(parameters)} dimension(s): ' + ' '.join(parameters))
    try:
        dimensions = tuple(positive(value) for value in values)
    except (ValueError, argparse.ArgumentTypeError):
        parser.error('Primitive dimensions must be positive integer voxel counts.')
    args.primitive = name
    args.dimensions = dimensions


def primitive_mask(shape, spacing, origin, primitive, dimensions, matrix):
    """Sample voxel centers in inverse-transformed primitive coordinates.

    Work one X plane at a time to avoid allocating full-volume coordinate grids.
    """
    inverse = np.linalg.inv(matrix)
    spacing, origin = np.asarray(spacing), np.asarray(origin)
    y, z = np.meshgrid(origin[1] + np.arange(shape[1]) * spacing[1],
                       origin[2] + np.arange(shape[2]) * spacing[2], indexing='ij')
    mask = np.empty(shape, dtype=bool)
    definition = PRIMITIVES[primitive]
    for x in range(shape[0]):
        world_x = origin[0] + x * spacing[0]
        local = [(inverse[i, 0] * world_x + inverse[i, 1] * y +
                  inverse[i, 2] * z + inverse[i, 3]) / spacing[i] for i in range(3)]
        mask[x] = definition['mask'](local, dimensions)
    return mask


def cut_volume(data, primitive, reference=None, buffer=None):
    """Erase the primitive, optionally restoring original detail in its buffer."""
    if primitive.shape != data.shape or not primitive.any():
        raise ValueError('Primitive must overlap the input image grid.')
    result = data.copy()
    if reference is not None:
        if reference.shape != data.shape or buffer is None or buffer < 1:
            raise ValueError('Detail requires a matching reference and buffer >= 1.')
        bounds = []
        for axis in range(3):
            occupied = np.flatnonzero(np.any(primitive, axis=tuple(i for i in range(3) if i != axis)))
            bounds.append(slice(max(0, occupied[0] - buffer), min(data.shape[axis], occupied[-1] + buffer + 1)))
        crop = tuple(bounds)
        buffered = dilate(primitive[crop], buffer)
        result[crop][buffered] = reference[crop][buffered]
    result[primitive] = 0
    return result


def cutout_volume(data, primitive, reference=None, buffer=None):
    """Keep the primitive interior, with reference detail just inside its edge."""
    result = np.zeros_like(data)
    result[primitive] = data[primitive]
    if reference is not None:
        if reference.shape != data.shape or buffer is None or buffer < 1:
            raise ValueError('Detail requires a matching reference and buffer >= 1.')
        core = erode(primitive, buffer)
        if not core.any():
            print('Cutout has no interior beyond the detail buffer; all retained voxels use reference detail.')
        inner_buffer = primitive & ~core
        result[inner_buffer] = reference[inner_buffer]
    return result


def remove_fragments(data, label='Model'):
    """Keep the largest 26-connected foreground component and its labels."""
    print(f'[{label}] Removing disconnected foreground fragments (keeping the largest component)...', flush=True)
    labels, count = ndi.label(data > 0, structure=ndi.generate_binary_structure(3, 3))
    if count <= 1:
        print(f'[{label}] Found {count} components; removed 0 fragments (0 voxels); '
              f'kept {np.count_nonzero(data):,} foreground voxels.', flush=True)
        return data.copy()
    sizes = np.zeros(count + 1, dtype=np.int64)
    for plane in labels:
        sizes += np.bincount(plane.ravel(), minlength=count + 1)
    sizes[0] = 0
    largest = int(sizes.argmax())
    removed = int(sizes.sum() - sizes[largest])
    result = data.copy()
    for x, plane in enumerate(labels):
        result[x][plane != largest] = 0
    print(f'[{label}] Found {count:,} components; removed {count - 1:,} fragments ({removed:,} voxels); '
          f'kept {sizes[largest]:,} foreground voxels.', flush=True)
    return result


def read_aim(filename):
    import vtkbone
    from vtkmodules.util.numpy_support import vtk_to_numpy
    if Path(filename).suffix.lower() != '.aim' or not Path(filename).is_file():
        raise ValueError(f'Input AIM does not exist: {filename}')
    reader = vtkbone.vtkboneAIMReader()
    reader.DataOnCellsOff()
    reader.SetFileName(str(filename))
    reader.Update()
    image = reader.GetOutput()
    scalars = image.GetPointData().GetScalars()
    if scalars is None or scalars.GetNumberOfComponents() != 1:
        raise ValueError('Could not read a scalar AIM image.')
    print_image_info(filename, image)
    data = vtk_to_numpy(scalars).reshape(image.GetDimensions(), order='F').copy()
    print('Input:', validate_segmentation(data))
    return reader, image, data


def image_geometry(image):
    spacing = np.asarray(image.GetSpacing())
    if not np.isfinite(spacing).all() or np.any(spacing <= 0):
        raise ValueError('Image spacing must be finite and positive.')
    start = np.asarray(image.GetExtent()[::2])
    return spacing, np.asarray(image.GetOrigin()) + start * spacing


def check_detail_geometry(image, reference):
    spacing, origin = image_geometry(image)
    ref_spacing, ref_origin = image_geometry(reference)
    if (image.GetDimensions() != reference.GetDimensions()
            or not np.allclose(spacing, ref_spacing, rtol=1e-6, atol=1e-8)
            or not np.allclose(origin, ref_origin, rtol=0, atol=1e-6)):
        raise ValueError('Detail reference must match input dimensions, spacing, and physical placement.')


def expand_for_primitive(data, spacing, origin, primitive, dimensions, matrix):
    lower, upper = primitive_bounds(spacing, origin, primitive, dimensions, matrix)
    low = np.minimum(0, np.floor(lower + 0.5)).astype(int)
    high = np.maximum(np.asarray(data.shape) - 1, np.ceil(upper - 0.5)).astype(int)
    shape = tuple(high - low + 1)
    expanded = np.zeros(shape, dtype=np.int8)
    destination = tuple(slice(-a, -a + n) for a, n in zip(low, data.shape))
    expanded[destination] = data
    new_origin = np.asarray(origin) + low * spacing
    print(f'Add image bounds: {data.shape} -> {shape}; origin {new_origin}.')
    return expanded, new_origin


def fill(args):
    process_image(args)


def cut(args):
    process_image(args)


def add(args):
    process_image(args)


def process_image(args):
    """Read, process, optionally preview, and write a prepared AIM."""
    import vtkbone
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.util.numpy_support import numpy_to_vtk
    output = Path(args.output_file)
    cutout_path = Path(args.cutout_output) if args.command == 'cut' and args.cutout_output else None
    outputs = [output] + ([cutout_path] if cutout_path is not None else [])
    protected = [Path(args.input_file)]
    if args.command == 'cut' and args.detail:
        protected.append(Path(args.detail[0]))
    if len({path.resolve() for path in outputs}) != len(outputs):
        raise ValueError('Remaining-model and cutout output paths must differ.')
    for path in outputs:
        if path.suffix.lower() != '.aim':
            raise ValueError('Each output must have an .aim extension.')
        if any(path.resolve() == source.resolve() for source in protected):
            raise ValueError('Outputs must differ from input and detail reference AIMs.')
        if path.exists() and not args.overwrite:
            raise ValueError(f'Output exists: {path}; use --overwrite to replace it.')
        if not path.parent.is_dir():
            raise ValueError(f'Output directory does not exist: {path.parent}')
    cutout = None
    reader, image, data = read_aim(args.input_file)
    spacing, origin = image_geometry(image)
    result_origin = origin
    matrix = None
    preview_options = {}
    if args.command == 'fill':
        result, stats = solid_body(data, args.close, args.erode)
        print('Background components:', stats)
    else:
        matrix = placement(data, spacing, origin, args.transform_file, args.position)
        if args.position and args.position[0] == 'principal_axes':
            frame = principal_axes_frame(matrix, spacing, args.position[1:])
            preview_options = dict(principal_frame=frame,
                                   principal_lengths=principal_axis_lengths(data, spacing, origin, frame))
        if args.command == 'add':
            result, result_origin = expand_for_primitive(
                data, spacing, origin, args.primitive, args.dimensions, matrix)
            primitive = primitive_mask(result.shape, spacing, result_origin, args.primitive, args.dimensions, matrix)
            result[primitive] = 127
        else:
            if primitive_is_clipped(data.shape, spacing, origin, args.primitive, args.dimensions, matrix):
                print('WARNING: PRIMITIVE CLIPPED AT IMAGE BOUNDS. Part of the requested primitive '
                      'lies outside the input image. Only the part inside the image is cut, '
                      'so the cutout may be smaller than requested.', flush=True)
            primitive = primitive_mask(data.shape, spacing, origin, args.primitive, args.dimensions, matrix)
            reference = None
            buffer = None
            if args.detail:
                _, ref_image, reference = read_aim(args.detail[0])
                check_detail_geometry(image, ref_image)
                buffer = args.detail[1]
            result = cut_volume(data, primitive, reference, buffer)
            if cutout_path is not None:
                cutout = cutout_volume(data, primitive, reference, buffer)
    if args.remove_fragments:
        if cutout is not None:
            print('Fragment removal will run independently on BOTH the remaining model and the cutout.', flush=True)
        result = remove_fragments(result, label='Remaining model' if args.command == 'cut' else 'Model')
        if cutout is not None:
            cutout = remove_fragments(cutout, label='Cutout')
    if cutout is not None and not np.any(cutout):
        print('WARNING: The cutout contains no foreground voxels; an empty AIM will be saved.')
    output_image = vtkImageData()
    if args.command == 'add':
        output_image.SetDimensions(*result.shape)
        output_image.SetSpacing(*spacing)
        output_image.SetOrigin(*result_origin)
    else:
        output_image.DeepCopy(image)
    output_image.GetPointData().SetScalars(numpy_to_vtk(result.ravel(order='F'), deep=True))
    if cutout is not None:
        preview_options['cutout_data'] = cutout
    if args.visualize:
        print('Previewing output AIM: q/close to write; x to cancel without writing.', flush=True)
        if not render_image(output_image, result, allow_cancel=True, **preview_options):
            print('Cancelled; output AIM was not written.')
            return
    log = (reader.GetProcessingLog() or '') + '\n' + str(datetime.now())
    log += '\nblRapidPrototypePrepare ' + str({k: v for k, v in vars(args).items() if k != 'func'})
    if matrix is not None:
        log += '\nPrimitive transform:\n' + np.array2string(matrix, precision=17)
    images = [(output, output_image, 'remaining model' if cutout is not None else args.command)]
    if cutout is not None:
        cutout_image = vtkImageData()
        cutout_image.DeepCopy(image)
        cutout_image.GetPointData().SetScalars(numpy_to_vtk(cutout.ravel(order='F'), deep=True))
        images.append((cutout_path, cutout_image, 'cutout'))
    # Complete both AIM writes before replacing any existing output file.
    import tempfile
    from contextlib import ExitStack
    with ExitStack() as stack:
        staged = []
        for path, image_to_write, role in images:
            directory = stack.enter_context(tempfile.TemporaryDirectory(dir=path.parent))
            temporary = Path(directory) / path.name
            writer = vtkbone.vtkboneAIMWriter()
            writer.SetFileName(str(temporary))
            writer.SetInputData(image_to_write)
            writer.SetProcessingLog(log + '\nOutput role: ' + role)
            errors = []
            writer.AddObserver('ErrorEvent', lambda obj, event: errors.append(event))
            writer.Update()
            if errors or writer.GetErrorCode() or not temporary.is_file():
                raise RuntimeError(f'Failed to write {path}')
            staged.append((temporary, path))
        for temporary, path in staged:
            temporary.replace(path)
            print('Written:', path)


def view(args):
    reader, image, data = read_aim(args.input_file)
    render_image(image, data, args)


def suggest_cut_command(args, transform_saved):
    """Print a reusable command for the primitive's last saved placement."""
    if not args.primitive:
        return
    source = Path(args.input_file)
    output = source.with_name(source.stem + '_crop' + source.suffix)
    command = [
        ['blRapidPrototypePrepare', 'cut', str(source), str(output)],
        ['--primitive', args.primitive, *map(str, args.dimensions)],
        ['--transform_file', args.transform_output],
        ['--visualize'],
    ]
    if args.overwrite:
        command[-1].append('--overwrite')
    if not transform_saved:
        print("No transform was saved in this session. Save the desired placement with 'u' "
              'in view mode before using this command.')
    print('\nSuggested cut command (uses the last saved transform):')
    print(' \\\n    '.join(shlex.join(line) for line in command))


def principal_axes_frame(matrix, spacing, relative=None):
    """Map voxel PCA axes to physical space, anchored at the model centroid."""
    frame = matrix.copy()
    frame[:3, :3] = matrix[:3, :3] * np.asarray(spacing)[None, :]
    if relative is not None:
        frame[:3, 3] -= frame[:3, :3] @ np.asarray(relative)
    return frame


def principal_axis_lengths(data, spacing, origin, frame):
    """Scale PCA standard deviations to half the foreground bounds diagonal.

    Return local arrow lengths, compensating for the frame's physical scaling.
    Foreground bounds include the half-voxel extent at each end.
    """
    spacing = np.asarray(spacing)
    center = (frame[:3, 3] - origin) / spacing
    directions = frame[:3, :3] / spacing[:, None]
    sums = np.zeros(3)
    lower = np.full(3, np.inf)
    upper = np.full(3, -np.inf)
    total = 0
    for x, plane in enumerate(data):
        y, z = np.nonzero(plane > 0)
        if not len(y):
            continue
        points = np.column_stack((np.full(len(y), x), y, z))
        lower = np.minimum(lower, points.min(axis=0))
        upper = np.maximum(upper, points.max(axis=0))
        projected = (points - center) @ directions
        sums += np.sum(projected ** 2, axis=0)
        total += len(y)
    if not total:
        return np.zeros(3)
    magnitudes = np.sqrt(sums / total)
    if not magnitudes.max():
        return np.zeros(3)
    maximum_length = 0.5 * np.linalg.norm((upper - lower + 1) * spacing)
    physical_lengths = maximum_length * magnitudes / magnitudes.max()
    return physical_lengths / np.linalg.norm(frame[:3, :3], axis=0)


def add_principal_axes(renderer, frame, lengths):
    """Add unlabeled, non-pickable arrows in the model's voxel PCA frame."""
    from vtkmodules.vtkCommonMath import vtkMatrix4x4
    from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
    axes = vtkAxesActor()
    axes.AxisLabelsOff()
    axes.SetTotalLength(*lengths)
    axes.SetShaftTypeToCylinder()
    axes.SetCylinderRadius(0.015)
    axes.SetConeRadius(0.06)
    transform = vtkMatrix4x4()
    transform.DeepCopy(frame.ravel())
    axes.SetUserMatrix(transform)
    axes.PickableOff()
    renderer.AddActor(axes)
    print('Principal-axis arrows at model centroid: PC1 red, PC2 green, PC3 blue.')
    return axes


def surface_actor(image, data):
    """Create an AIM surface actor for a single or paired preview."""
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.vtkFiltersCore import vtkMarchingCubes
    from vtkmodules.vtkImagingCore import vtkImageConstantPad
    from vtkmodules.vtkRenderingCore import vtkPolyDataMapper, vtkActor
    from vtkmodules.util.numpy_support import numpy_to_vtk
    binary = vtkImageData()
    binary.DeepCopy(image)
    binary.GetPointData().SetScalars(numpy_to_vtk((data > 0).astype(np.uint8).ravel(order='F'), deep=True))
    pad = vtkImageConstantPad()
    pad.SetInputData(binary)
    extent = image.GetExtent()
    pad.SetOutputWholeExtent(*[v + (-1 if i % 2 == 0 else 1) for i, v in enumerate(extent)])
    pad.SetConstant(0)
    surface = vtkMarchingCubes()
    surface.SetInputConnection(pad.GetOutputPort())
    surface.SetValue(0, 0.5)
    surface.Update()
    print(f'Rendering AIM surface: {surface.GetOutput().GetNumberOfPolys():,} triangles.', flush=True)
    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(surface.GetOutputPort())
    mapper.ScalarVisibilityOff()
    anatomy = vtkActor()
    anatomy.SetMapper(mapper)
    anatomy.PickableOff()
    anatomy.GetProperty().SetColor(0.9, 0.85, 0.7)
    return anatomy


def render_image(image, data, args=None, allow_cancel=False, principal_frame=None, principal_lengths=None, cutout_data=None):
    """Render a loaded AIM; return False when an output preview is cancelled."""
    from vtkmodules.vtkCommonMath import vtkMatrix4x4
    from vtkmodules.vtkCommonTransforms import vtkTransform
    from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
    from vtkmodules.vtkInteractionStyle import (vtkInteractorStyleTrackballActor,
                                               vtkInteractorStyleTrackballCamera)
    from vtkmodules.vtkRenderingCore import (vtkPolyDataMapper, vtkActor, vtkRenderer,
                                            vtkRenderWindow, vtkRenderWindowInteractor)
    import vtkmodules.vtkRenderingOpenGL2  # Register the rendering backend.
    import vtkmodules.vtkRenderingUI  # Register the native window interactor.
    anatomy = surface_actor(image, data)
    renderer = vtkRenderer()
    renderer.AddActor(anatomy)
    actor = None
    if args is not None and args.primitive:
        spacing, origin = image_geometry(image)
        matrix = placement(data, spacing, origin, args.transform_file, args.position)
        if args.position and args.position[0] == 'principal_axes':
            principal_frame = principal_axes_frame(matrix, spacing, args.position[1:])
        source = PRIMITIVES[args.primitive]['source'](args.dimensions)
        scale = vtkTransform()
        scale.Scale(*spacing)
        geometry = vtkTransformPolyDataFilter()
        geometry.SetInputConnection(source.GetOutputPort())
        geometry.SetTransform(scale)
        primitive_mapper = vtkPolyDataMapper()
        primitive_mapper.SetInputConnection(geometry.GetOutputPort())
        actor = vtkActor()
        actor.SetMapper(primitive_mapper)
        vtk_matrix = vtkMatrix4x4()
        vtk_matrix.DeepCopy(matrix.ravel())
        actor.SetUserMatrix(vtk_matrix)
        actor.GetProperty().SetColor(0.2, 0.7, 1)
        actor.GetProperty().SetOpacity(0.55)
        anatomy.GetProperty().SetOpacity(0.45)
        renderer.AddActor(actor)
    if principal_frame is not None:
        if principal_lengths is None:
            spacing, origin = image_geometry(image)
            principal_lengths = principal_axis_lengths(data, spacing, origin, principal_frame)
        add_principal_axes(renderer, principal_frame, principal_lengths)
    window = vtkRenderWindow()
    window.AddRenderer(renderer)
    paired_renderer = None
    model_bounds = np.asarray(anatomy.GetBounds()).reshape(3, 2)
    if cutout_data is not None:
        paired_renderer = vtkRenderer()
        paired_renderer.AddActor(surface_actor(image, cutout_data))
        renderer.SetViewport(0, 0, 0.5, 1)
        paired_renderer.SetViewport(0.5, 0, 1, 1)
        paired_renderer.SetActiveCamera(renderer.GetActiveCamera())
        paired_renderer.SetBackground(0.15, 0.18, 0.22)
        window.AddRenderer(paired_renderer)
        bounds = np.asarray(paired_renderer.GetActors().GetItemAsObject(0).GetBounds()).reshape(3, 2)
        if np.all(bounds[:, 0] <= bounds[:, 1]):
            if np.all(model_bounds[:, 0] <= model_bounds[:, 1]):
                model_bounds = np.column_stack((np.minimum(model_bounds[:, 0], bounds[:, 0]),
                                                np.maximum(model_bounds[:, 1], bounds[:, 1])))
            else:
                model_bounds = bounds
        from vtkmodules.vtkRenderingCore import vtkTextActor
        import vtkmodules.vtkRenderingFreeType
        for panel, title in [(renderer, 'Remaining model'), (paired_renderer, 'Cutout')]:
            label = vtkTextActor()
            label.SetInput(title)
            label.SetPosition(15, 15)
            label.GetTextProperty().SetFontSize(22)
            label.PickableOff()
            panel.AddActor2D(label)
        print('Paired preview: remaining model (left), cutout (right). Cameras are synchronized.')
    window.SetSize(2200, 1700)
    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(window)
    # Custom controls avoid actor scaling: left rotates, middle/shift-left pans.
    class RigidActorStyle(vtkInteractorStyleTrackballActor):
        def __init__(self):
            self.AddObserver('RightButtonPressEvent', lambda obj, event: None)
            self.AddObserver('MouseWheelForwardEvent', lambda obj, event: None)
            self.AddObserver('MouseWheelBackwardEvent', lambda obj, event: None)
            self.AddObserver('LeftButtonPressEvent', self.left)
        def left(self, obj, event):
            if not self.GetInteractor().GetControlKey():
                self.OnLeftButtonDown()
    actor_style = RigidActorStyle()
    camera_style = vtkInteractorStyleTrackballCamera()
    interactor.SetInteractorStyle(camera_style)
    cancelled = False
    transform_saved = False
    def keypress(obj, event):
        nonlocal cancelled, transform_saved
        key = obj.GetKeySym().lower()
        if key == 'a' and actor:
            obj.SetInteractorStyle(actor_style)
        elif key == 'c':
            obj.SetInteractorStyle(camera_style)
        elif key in ('u', 'q') and actor and args.transform_output:
            # Export the full local-to-world mapping, including the initial user
            # matrix and every interactive actor adjustment. Never save only
            # the initial placement or apply it again when reloading.
            final_matrix = actor.GetMatrix()
            matrix = np.array([[final_matrix.GetElement(i, j) for j in range(4)] for i in range(4)])
            try:
                write_transform(args.transform_output, matrix, args.overwrite)
                transform_saved = True
                print('Transform written:', args.transform_output)
            except FileExistsError:
                print('Transform exists; use --overwrite or a different --transform_output.')
            if key == 'q':
                obj.TerminateApp()
        elif key == 'x':
            cancelled = True
            print('Exited without writing files. Previously saved files are unchanged.')
            obj.TerminateApp()
        elif key == 'q':
            obj.TerminateApp()
    interactor.AddObserver('KeyPressEvent', keypress, 1.0)
    renderer.SetBackground(0.15, 0.18, 0.22)
    if actor:
        print('Starting in camera mode. a: move primitive; c: camera; u: save transform; q: save transform and quit. '
              'Primitive: left drag rotates; middle or shift-left drag translates.')
    else:
        print('Camera: left drag rotates; middle drag pans; right drag zooms; q: quit.')
    print('x: exit without writing any files (previous saves are retained).')
    if allow_cancel:
        print('Output preview: q or close window to write; x to cancel without writing.')
    interactor.Initialize()
    # Frame the model rather than the combined bounds of arrows and primitive.
    # Initialize first so the camera uses the window's actual viewport size.
    if np.all(model_bounds[:, 0] <= model_bounds[:, 1]):
        renderer.ResetCamera(model_bounds.ravel())
        renderer.ResetCameraClippingRange(model_bounds.ravel())
        if paired_renderer is not None:
            interactor.AddObserver('EndInteractionEvent',
                lambda obj, event: renderer.ResetCameraClippingRange(model_bounds.ravel()))
    window.Render()
    interactor.Start()
    if args is not None and not cancelled:
        suggest_cut_command(args, transform_saved)
    return not cancelled


def nonnegative(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError('Must be >= 0.')
    return number


def positive(value):
    number = nonnegative(value)
    if number < 1:
        raise argparse.ArgumentTypeError('Must be >= 1.')
    return number


def create_parser():
    examples = {
        'view': r'''Plan a placement; 'u' saves, 'q' saves and quits, 'x' exits without saving:
  blRapidPrototypePrepare view vertebra.aim \
    --primitive box 300 400 500 \
    --position principal_axes 250 -250 250 \
    --transform_output vertebra_xform.txt --overwrite

View an AIM without a primitive:
  blRapidPrototypePrepare view vertebra_crop.aim''',
        'fill': r'''Fill the model once before cutting or adding:
  blRapidPrototypePrepare fill vertebra.aim vertebra_filled.aim \
    --close 10 --erode 6 --visualize --overwrite''',
        'cut': r'''Cut a filled model and restore original detail around the cut:
  blRapidPrototypePrepare cut vertebra_filled.aim vertebra_crop.aim \
    --primitive box 300 400 500 \
    --transform_file vertebra_xform.txt \
    --detail vertebra.aim 20 --visualize --overwrite

Add --cutout_output vertebra_piece.aim to save the extracted piece too.
With --visualize, both pieces share a camera; q writes both, x cancels both.
For a plain cut, omit --detail. Direct placement is also available:
  blRapidPrototypePrepare cut vertebra_filled.aim vertebra_crop.aim \
    --primitive cube 500 --position principal_axes 250 -250 250 \
    --visualize --overwrite''',
        'add': r'''Add a cylinder; image bounds expand to contain it:
  blRapidPrototypePrepare add vertebra_crop.aim vertebra_added.aim \
    --primitive cylinder 100 300 --position centroid 0 0 0 \
    --visualize --overwrite''',
    }
    controls = ("Output previews: q or close window to write; x to cancel.\n"
                "Saved transforms replace --position; do not supply both.\n"
                "Fragment removal is off by default; enable with --remove_fragments.")
    parser = argparse.ArgumentParser(
        description=__doc__, prog='blRapidPrototypePrepare',
        epilog='Workflow: view -> fill -> cut/add\n\n' + '\n\n'.join(examples.values()) + '\n\n' + controls,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    for name, function in [('view', view), ('fill', fill), ('cut', cut), ('add', add)]:
        sub = commands.add_parser(name, epilog=examples[name] + '\n\n' + controls,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
        sub.add_argument('input_file')
        if name != 'view':
            sub.add_argument('output_file')
            sub.add_argument('--visualize', action='store_true', help='Preview before writing; x cancels, q/close writes.')
            sub.add_argument('--remove_fragments', action='store_true',
                             help='Keep only the largest 26-connected foreground component (default: off).')
        else:
            sub.add_argument('--transform_output', default='transform.txt',
                             help="Save the final primitive placement with u or q (default: transform.txt).")
        if name == 'fill':
            sub.add_argument('--close', type=nonnegative, default=10, help='Closing radius in voxels (default: 10; 0 disables).')
            sub.add_argument('--erode', type=nonnegative, default=6, help='Erosion radius in voxels (default: 6).')
        if name == 'cut':
            sub.add_argument('--cutout_output', metavar='CUTOUT_AIM',
                             help='Also save the extracted piece on the input grid; --detail restores its inner buffer.')
            sub.add_argument('--detail', nargs=2, metavar=('REFERENCE_AIM', 'BUFFER'),
                             help='Restore reference values around the cut within BUFFER voxels (minimum 1).')
        if name != 'fill':
            sub.add_argument('--primitive', nargs='+', metavar='SHAPE_OR_SIZE', required=name != 'view',
                             help='sphere D; cube E; box X Y Z; cylinder D L (local Z length), in voxels.')
            position = sub.add_mutually_exclusive_group()
            position.add_argument('--position', nargs=4, metavar=('MODE', 'X', 'Y', 'Z'),
                                  help='origin, centroid, or principal_axes plus voxel offsets. Default: origin 0 0 0.')
            position.add_argument('--transform_file', help='Load complete placement instead of --position.')
        sub.add_argument('--overwrite', action='store_true')
        sub.set_defaults(func=function)
    return parser


def main(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)
    if args.command != 'fill':
        normalize_primitive(args, parser)
        if not args.primitive and (args.transform_file or args.position):
            parser.error('Primitive placement options require --primitive.')
        if args.position:
            mode, *offset = args.position
            if mode not in ('origin', 'centroid', 'principal_axes'):
                parser.error('--position mode must be origin, centroid, or principal_axes.')
            try:
                offset = tuple(float(value) for value in offset)
            except ValueError:
                parser.error('--position XYZ offsets must be numbers.')
            if not np.isfinite(offset).all():
                parser.error('--position XYZ offsets must be finite.')
            args.position = (mode, *offset)
    if args.command == 'cut' and args.detail:
        try:
            args.detail = (args.detail[0], positive(args.detail[1]))
        except (ValueError, argparse.ArgumentTypeError):
            parser.error('--detail BUFFER must be a positive integer voxel count.')
    try:
        args.func(args)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
