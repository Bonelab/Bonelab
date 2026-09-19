"""Prepare segmented AIMs with a solid body and a buffered primitive cutout.

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


def solid_body(data, close=0, erosion=5):
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
        np.savetxt(stream, matrix, fmt='%.10e', comments='',
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


def placement(data, spacing, origin, transform_file=None, relative=None, use_principal_axes=False):
    if transform_file:
        if use_principal_axes:
            raise ValueError('Principal-axis placement cannot be combined with a transform file.')
        return read_transform(transform_file)
    counts = np.array([np.count_nonzero(plane) for plane in data])
    total = counts.sum()
    center = np.array([np.dot(np.arange(data.shape[0]), counts), 0., 0.])
    for plane in data:
        foreground = plane > 0
        center[1] += np.dot(np.arange(data.shape[1]), foreground.sum(axis=1))
        center[2] += np.dot(np.arange(data.shape[2]), foreground.sum(axis=0))
    if not total:
        raise ValueError('Cannot position a primitive without foreground voxels.')
    center /= total
    axes = principal_axes(data, center) if use_principal_axes else np.eye(3)
    if relative is not None:
        center += axes @ np.asarray(relative)
    matrix = np.eye(4)
    # Geometry is already scaled by spacing: S R S^-1 maps it to S R voxels.
    spacing = np.asarray(spacing)
    matrix[:3, :3] = spacing[:, None] * axes / spacing[None, :]
    matrix[:3, 3] = np.asarray(origin) + center * spacing
    return matrix


def primitive_mask(shape, spacing, origin, primitive, dimension, matrix):
    """Sample voxel centers in inverse-transformed primitive coordinates.

    Work one X plane at a time to avoid allocating full-volume coordinate grids.
    """
    inverse = np.linalg.inv(matrix)
    spacing, origin = np.asarray(spacing), np.asarray(origin)
    y, z = np.meshgrid(origin[1] + np.arange(shape[1]) * spacing[1],
                       origin[2] + np.arange(shape[2]) * spacing[2], indexing='ij')
    mask = np.empty(shape, dtype=bool)
    half = dimension / 2
    for x in range(shape[0]):
        world_x = origin[0] + x * spacing[0]
        local = [(inverse[i, 0] * world_x + inverse[i, 1] * y +
                  inverse[i, 2] * z + inverse[i, 3]) / spacing[i] for i in range(3)]
        if primitive == 'cube':
            # Half-open bounds give exactly D voxels for aligned integer cubes.
            mask[x] = np.logical_and.reduce([(v >= -half - 1e-9) & (v < half - 1e-9) for v in local])
        else:
            mask[x] = sum(v * v for v in local) <= half * half + 1e-9
    return mask


def generate(data, primitive, buffer=8, close=0, erosion=5):
    validate_segmentation(data)
    if buffer < 1 or close < 0 or erosion < 0:
        raise ValueError('Buffer must be >= 1; close and erosion must be >= 0.')
    if primitive.shape != data.shape or not primitive.any():
        raise ValueError('Primitive must overlap the input image grid.')
    # Dilation is clipped to the original grid, as is the final output.
    bounds = []
    for axis in range(3):
        occupied = np.flatnonzero(np.any(primitive, axis=tuple(i for i in range(3) if i != axis)))
        bounds.append(slice(max(0, occupied[0] - buffer), min(data.shape[axis], occupied[-1] + buffer + 1)))
    crop = tuple(bounds)
    buffered = dilate(primitive[crop], buffer)
    result, stats = solid_body(data, close, erosion)
    region = result[crop]
    region[buffered] = data[crop][buffered]
    region[primitive[crop]] = 0
    return result, stats


def remove_fragments(data):
    """Keep the largest 26-connected foreground component and its labels."""
    print('Removing disconnected foreground fragments...', flush=True)
    labels, count = ndi.label(data > 0, structure=ndi.generate_binary_structure(3, 3))
    if count <= 1:
        print('Removed 0 fragments (0 voxels).')
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
    print(f'Removed {count - 1:,} fragments ({removed:,} voxels); '
          f'kept {sizes[largest]:,} foreground voxels.')
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


def apply(args):
    import vtkbone
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.util.numpy_support import numpy_to_vtk
    output = Path(args.output_file)
    if output.suffix.lower() != '.aim':
        raise ValueError('Output must have an .aim extension.')
    if output.resolve() == Path(args.input_file).resolve():
        raise ValueError('Output must differ from the input AIM.')
    if output.exists() and not args.overwrite:
        raise ValueError(f'Output exists: {output}; use --overwrite to replace it.')
    reader, image, data = read_aim(args.input_file)
    spacing, origin = image_geometry(image)
    matrix = placement(data, spacing, origin, args.transform_file, args.relative_to_centroid, args.principal_axes)
    primitive = primitive_mask(data.shape, spacing, origin, args.primitive, args.dimension, matrix)
    result, stats = generate(data, primitive, args.buffer, args.close, args.erode)
    print('Background components:', stats)
    if args.remove_fragments:
        result = remove_fragments(result)
    output_image = vtkImageData()
    output_image.DeepCopy(image)
    output_image.GetPointData().SetScalars(numpy_to_vtk(result.ravel(order='F'), deep=True))
    if args.visualize:
        print('Previewing output AIM: q/close to write; x to cancel without writing.', flush=True)
        preview_options = {}
        if args.principal_axes:
            preview_options['principal_frame'] = principal_axes_frame(matrix, spacing, args.relative_to_centroid)
            preview_options['principal_lengths'] = principal_axis_lengths(
                data, spacing, origin, preview_options['principal_frame'])
        if not render_image(output_image, result, allow_cancel=True, **preview_options):
            print('Cancelled; output AIM was not written.')
            return
    writer = vtkbone.vtkboneAIMWriter()
    writer.SetFileName(str(output))
    writer.SetInputData(output_image)
    log = (reader.GetProcessingLog() or '') + '\n' + str(datetime.now())
    log += '\nblRapidPrototypeModelGenerator ' + str({k: v for k, v in vars(args).items() if k != 'func'})
    log += '\nPrimitive transform:\n' + np.array2string(matrix, precision=12)
    writer.SetProcessingLog(log)
    writer.Update()
    if writer.GetErrorCode() or not output.is_file():
        raise RuntimeError(f'Failed to write {output}')
    print('Written:', output)


def visualize(args):
    reader, image, data = read_aim(args.input_file)
    render_image(image, data, args)


def suggest_apply_command(args, transform_saved):
    """Print a reusable command for the primitive's last saved placement."""
    if not args.primitive:
        return
    source = Path(args.input_file)
    output = source.with_name(source.stem + '_crop' + source.suffix)
    command = [
        ['blRapidPrototypeModelGenerator', 'apply', str(source), str(output)],
        ['--primitive', args.primitive, '--dimension', str(args.dimension)],
        ['--transform_file', args.transform_output],
        ['--visualize'],
    ]
    if args.overwrite:
        command[-1].append('--overwrite')
    if not transform_saved:
        print("No transform was saved in this session. Save the desired placement with 'u' "
              'in visualize mode before using this command.')
    print('\nSuggested apply command (uses the last saved transform):')
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


def render_image(image, data, args=None, allow_cancel=False, principal_frame=None, principal_lengths=None):
    """Render a loaded AIM; return False when an output preview is cancelled."""
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.vtkCommonMath import vtkMatrix4x4
    from vtkmodules.vtkCommonTransforms import vtkTransform
    from vtkmodules.vtkFiltersCore import vtkMarchingCubes
    from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
    from vtkmodules.vtkFiltersSources import vtkCubeSource, vtkSphereSource
    from vtkmodules.vtkImagingCore import vtkImageConstantPad
    from vtkmodules.vtkInteractionStyle import (vtkInteractorStyleTrackballActor,
                                               vtkInteractorStyleTrackballCamera)
    from vtkmodules.vtkRenderingCore import (vtkPolyDataMapper, vtkActor, vtkRenderer,
                                            vtkRenderWindow, vtkRenderWindowInteractor)
    import vtkmodules.vtkRenderingOpenGL2  # Register the rendering backend.
    import vtkmodules.vtkRenderingUI  # Register the native window interactor.
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
    renderer = vtkRenderer()
    renderer.AddActor(anatomy)
    actor = None
    if args is not None and args.primitive:
        spacing, origin = image_geometry(image)
        matrix = placement(data, spacing, origin, args.transform_file, args.relative_to_centroid, args.principal_axes)
        if args.principal_axes:
            principal_frame = principal_axes_frame(matrix, spacing, args.relative_to_centroid)
        if args.primitive == 'cube':
            source = vtkCubeSource()
            source.SetXLength(args.dimension)
            source.SetYLength(args.dimension)
            source.SetZLength(args.dimension)
        else:
            source = vtkSphereSource()
            source.SetRadius(args.dimension / 2)
            source.SetThetaResolution(64)
            source.SetPhiResolution(64)
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
            matrix = np.array([[actor.GetMatrix().GetElement(i, j) for j in range(4)] for i in range(4)])
            try:
                write_transform(args.transform_output, matrix, args.overwrite)
                transform_saved = True
                print('Transform written:', args.transform_output)
            except FileExistsError:
                print('Transform exists; use --overwrite or a different --transform_output.')
            if key == 'q':
                obj.TerminateApp()
        elif key == 'x' and allow_cancel:
            cancelled = True
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
    if allow_cancel:
        print('Output preview: q or close window to write; x to cancel without writing.')
    interactor.Initialize()
    # Frame the model rather than the combined bounds of arrows and primitive.
    # Initialize first so the camera uses the window's actual viewport size.
    renderer.ResetCamera(anatomy.GetBounds())
    renderer.ResetCameraClippingRange()
    window.Render()
    interactor.Start()
    if args is not None:
        suggest_apply_command(args, transform_saved)
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
    epilog = '''Example workflow:
  1. Position the primitive and press 'u' to save its transform:
     blRapidPrototypeModelGenerator visualize vertebra.aim \\
       --primitive cube --dimension 500 \\
       --transform_output vertebra_xform.txt \\
       --principal_axes --relative_to_centroid 250 -250 250 \\
       --overwrite

  2. Apply the saved transform and preview the resulting AIM:
     blRapidPrototypeModelGenerator apply vertebra.aim vertebra_crop.aim \\
       --primitive cube --dimension 500 \\
       --buffer 20 --close 10 --erode 10 \\
       --transform_file vertebra_xform.txt \\
       --visualize --overwrite

     The saved transform includes principal-axis alignment; apply does not need
     --principal_axes when using --transform_file.

     In the output preview, press 'q' or close the window to write; press 'x' to cancel.
'''
    parser = argparse.ArgumentParser(
        description=__doc__, prog='blRapidPrototypeModelGenerator',
        epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest='command', required=True)
    command_epilogs = {
        'visualize': '''Examples:
  Position a primitive and press 'u' to save its transform:
    blRapidPrototypeModelGenerator visualize vertebra.aim \\
      --primitive cube --dimension 500 \\
      --transform_output vertebra_xform.txt \\
      --principal_axes --relative_to_centroid 250 -250 250 \\
      --overwrite

  View an AIM without a primitive:
    blRapidPrototypeModelGenerator visualize vertebra_crop.aim
''',
        'apply': '''Examples:
  Apply the saved transform and preview the resulting AIM:
    blRapidPrototypeModelGenerator apply vertebra.aim vertebra_crop.aim \\
      --primitive cube --dimension 500 \\
      --buffer 20 --close 10 --erode 10 \\
      --transform_file vertebra_xform.txt \\
      --visualize --overwrite

  Alternatively, apply principal-axis placement directly without a transform:
    blRapidPrototypeModelGenerator apply vertebra.aim vertebra_crop.aim \\
      --primitive cube --dimension 500 \\
      --principal_axes --relative_to_centroid 250 -250 250 \\
      --buffer 20 --close 10 --erode 10 \\
      --visualize --overwrite

  Saved transforms already include principal-axis alignment; do not combine
  --transform_file with --principal_axes.

  In the output preview, press 'q' or close the window to write; press 'x' to cancel.
''',
    }
    for name, function in [('apply', apply), ('visualize', visualize)]:
        sub = commands.add_parser(
            name, epilog=command_epilogs[name],
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        sub.add_argument('input_file')
        if name == 'apply':
            sub.add_argument('output_file')
            fragments = sub.add_mutually_exclusive_group()
            fragments.add_argument('--remove_fragments', dest='remove_fragments',
                                   action='store_true', default=True,
                                   help='Keep only the largest foreground component before preview/writing (default: on; face, edge, or corner connectivity).')
            fragments.add_argument('--no-remove_fragments', dest='remove_fragments',
                                   action='store_false', help='Retain disconnected foreground fragments.')
            sub.add_argument('--visualize', action='store_true',
                             help='Preview the resulting AIM; q or close window to write, x to cancel without writing.')
            sub.add_argument('--buffer', type=positive, default=8, help='Buffer radius in voxels (default: 8).')
            sub.add_argument('--close', type=nonnegative, default=0, help='Closing radius in voxels (default: 0, disabled).')
            sub.add_argument('--erode', type=nonnegative, default=5, help='Body erosion radius in voxels (default: 5).')
        else:
            sub.add_argument('--transform_output', default='transform.txt',
                             help="Save the primitive transform on 'u' or on 'q' before quitting (default: transform.txt).")
        sub.add_argument('--primitive', choices=['cube', 'sphere'], required=name == 'apply')
        sub.add_argument('--dimension', type=positive, help='Cube edge or sphere diameter in voxels.')
        sub.add_argument('--principal_axes', action='store_true',
                         help='Align with foreground principal axes in voxel coordinates; XYZ offsets follow those axes.')
        position = sub.add_mutually_exclusive_group()
        position.add_argument('--position_at_centroid', action='store_true', help='Default placement.')
        position.add_argument('--relative_to_centroid', nargs=3, type=float, metavar=('X', 'Y', 'Z'),
                              help='Voxel offsets along image axes, or principal axes with --principal_axes.')
        position.add_argument('--transform_file',
                              help='Load saved placement, including alignment; cannot combine with --principal_axes.')
        sub.add_argument('--overwrite', action='store_true')
        sub.set_defaults(func=function)
    return parser


def main(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)
    if bool(args.primitive) != (args.dimension is not None):
        parser.error('--primitive and --dimension must be supplied together.')
    if not args.primitive and (args.transform_file or args.relative_to_centroid or args.position_at_centroid or args.principal_axes):
        parser.error('Primitive placement options require --primitive.')
    if args.principal_axes and args.transform_file:
        parser.error('--principal_axes cannot be combined with --transform_file.')
    if args.relative_to_centroid and not np.isfinite(args.relative_to_centroid).all():
        parser.error('Centroid offsets must be finite.')
    try:
        args.func(args)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
