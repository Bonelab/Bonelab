"""Numerical tests run without VTK; AIM integration runs when vtkbone exists."""
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
from bonelab.cli import RapidPrototypePrepare as generator


class TestModelGenerator(unittest.TestCase):
    def shell(self):
        data = np.zeros((25, 25, 25), dtype=np.int8)
        data[3:22, 3:22, 3:22] = 42
        data[5:20, 5:20, 5:20] = 0
        return data

    def test_validation(self):
        for value in [-1, 128, 0.5, np.nan, np.inf, 0]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                generator.validate_segmentation(np.full((3, 3, 3), value))
        data = self.shell()
        data[3, 3, 3] = 1
        self.assertIn('2 positive values', generator.validate_segmentation(data))

    def test_filling_and_erosion_restore_original_values(self):
        data = self.shell()
        result, stats = generator.solid_body(data, close=0, erosion=0)
        self.assertEqual(result[12, 12, 12], 127)
        np.testing.assert_array_equal(result[data > 0], data[data > 0])
        self.assertEqual(stats['components'], 2)
        self.assertTrue(stats['largest_touches_boundary'])
        eroded, _ = generator.solid_body(data, close=0, erosion=20)
        np.testing.assert_array_equal(eroded, data)

    def test_open_pore_warns_and_closing_seals_it(self):
        data = self.shell()
        data[3:22, 3:22, 3:22] = 42
        data[8:17, 8:17, 8:17] = 0
        data[3:9, 12, 12] = 0
        with self.assertWarnsRegex(UserWarning, 'increasing --close'):
            opened, stats = generator.solid_body(data, close=0, erosion=0)
        self.assertEqual(stats['components'], 1)
        self.assertEqual(opened[12, 12, 12], 0)
        closed, stats = generator.solid_body(data, close=1, erosion=0)
        self.assertGreater(stats['components'], 1)
        self.assertEqual(closed[12, 12, 12], 127)

    def test_buffer_overwrites_zeros_and_foreground(self):
        data = self.shell()
        data[12, 12, 16] = 73
        primitive = np.zeros_like(data, dtype=bool)
        primitive[10:15, 10:15, 10:15] = True
        filled, _ = generator.solid_body(data, close=0, erosion=0)
        output = generator.cut_volume(filled, primitive, data, 3)
        buffered = generator.dilate(primitive, 3)
        np.testing.assert_array_equal(output[buffered & ~primitive], data[buffered & ~primitive])
        self.assertTrue(np.all(output[primitive] == 0))
        self.assertEqual(output[12, 12, 18], 127)
        self.assertEqual(output[12, 12, 16], 73)
        self.assertEqual(output.shape, data.shape)

    def test_anisotropic_voxel_primitives_and_offset(self):
        data = np.zeros((15, 15, 15), dtype=np.int8)
        data[7, 7, 7] = 127
        spacing = np.array([0.1, 0.2, 0.3])
        origin = np.array([10., 20., 30.])
        transform = generator.placement(data, spacing, origin, position=('centroid', 1, -2, 3))
        np.testing.assert_allclose(transform[:3, 3], origin + spacing * [8, 5, 10])
        for name in ['cube', 'sphere']:
            mask = generator.primitive_mask(data.shape, spacing, origin, name, (4,), transform)
            self.assertTrue(mask[8, 5, 10])
            self.assertFalse(mask[8, 5, 13])

    def test_transform_roundtrip_rotation(self):
        matrix = np.eye(4)
        matrix[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
        matrix[:3, 3] = [10, 20, 30]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'transform.txt'
            generator.write_transform(path, matrix)
            np.testing.assert_allclose(generator.read_transform(path), matrix)
            with self.assertRaises(FileExistsError):
                generator.write_transform(path, matrix)
            matrix[0, 1] = 0
            generator.write_transform(path, matrix, overwrite=True)
            with self.assertRaises(ValueError):
                generator.read_transform(path)
        rotated = generator.primitive_mask((20, 30, 40), [1, 1, 1], [0, 0, 0], 'cube', (4,),
                                          np.array([[0, -1, 0, 10], [1, 0, 0, 20], [0, 0, 1, 30], [0, 0, 0, 1]]))
        self.assertEqual(np.count_nonzero(rotated), 64)

    def test_boundary_clipping(self):
        data = self.shell()
        matrix = np.eye(4)
        primitive = generator.primitive_mask(data.shape, [1]*3, [0]*3, 'cube', (8,), matrix)
        output = generator.cut_volume(data, primitive)
        self.assertEqual(output.shape, data.shape)
        self.assertTrue(np.all(output[primitive] == 0))
        with self.assertRaises(ValueError):
            generator.cut_volume(data, np.zeros_like(primitive))

    def test_slab_morphology_matches_full_volume(self):
        from scipy import ndimage as ndi
        rng = np.random.default_rng(12)
        mask = rng.random((47, 19, 21)) > 0.5
        for radius in (1, 3):
            expected = ndi.distance_transform_edt(~mask) <= radius
            np.testing.assert_array_equal(generator.dilate(mask, radius), expected)
            padded = np.pad(mask, 1)
            expected = (ndi.distance_transform_edt(padded) > radius)[1:-1, 1:-1, 1:-1]
            np.testing.assert_array_equal(generator.erode(mask, radius), expected)

    def test_principal_axes_anisotropic_placement_and_roundtrip(self):
        coords = np.indices((51, 51, 51)).reshape(3, -1).T - 25
        angle = np.deg2rad(30)
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                             [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
        local = coords @ rotation
        data = (np.sum((local / [18, 10, 5]) ** 2, axis=1) <= 1).reshape((51,) * 3).astype(np.int8)
        spacing = np.array([0.1, 0.3, 0.7])
        origin = np.array([2., 3., 4.])
        offset = np.array([3., -2., 1.])
        matrix = generator.placement(data, spacing, origin, position=('principal_axes', *offset))
        axes = matrix[:3, :3] / spacing[:, None] * spacing[None, :]
        np.testing.assert_allclose(axes, rotation, atol=0.015)
        np.testing.assert_allclose(axes.T @ axes, np.eye(3), atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(axes), 1.)
        np.testing.assert_allclose(matrix[:3, 3], origin + spacing * (25 + axes @ offset))
        # Equivalent voxel-space and physical-space masks, despite anisotropy.
        voxel_matrix = np.eye(4)
        voxel_matrix[:3, :3] = axes
        voxel_matrix[:3, 3] = 25 + axes @ offset
        for primitive in ['cube', 'sphere']:
            actual = generator.primitive_mask(data.shape, spacing, origin, primitive, (8,), matrix)
            expected = generator.primitive_mask(data.shape, np.ones(3), np.zeros(3), primitive, (8,), voxel_matrix)
            np.testing.assert_array_equal(actual, expected)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'pca.txt'
                generator.write_transform(path, matrix)
                restored = generator.placement(data, spacing, origin, transform_file=path)
                mask = generator.primitive_mask(data.shape, spacing, origin, primitive, (8,), restored)
                np.testing.assert_array_equal(mask, actual)

    def test_principal_axis_arrows_at_centroid(self):
        try:
            from vtkmodules.vtkRenderingCore import vtkRenderer
        except ImportError:
            self.skipTest('VTK is required for axis actors')
        angle = np.deg2rad(30)
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                             [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
        spacing = np.array([0.1, 0.3, 0.7])
        centroid = np.array([12., 15., 9.])
        offset = np.array([4., -3., 2.])
        matrix = np.eye(4)
        matrix[:3, :3] = spacing[:, None] * rotation / spacing[None, :]
        matrix[:3, 3] = centroid + spacing * (rotation @ offset)
        frame = generator.principal_axes_frame(matrix, spacing, offset)
        np.testing.assert_allclose(frame[:3, 3], centroid)
        voxel_axes = frame[:3, :3] / spacing[:, None]
        np.testing.assert_allclose(voxel_axes.T @ voxel_axes, np.eye(3), atol=1e-12)
        renderer = vtkRenderer()
        actor = generator.add_principal_axes(renderer, frame, (10., 7., 3.))
        self.assertFalse(actor.GetPickable())
        self.assertFalse(actor.GetAxisLabels())
        np.testing.assert_allclose(actor.GetTotalLength(), [10., 7., 3.])
        actual = np.array([[actor.GetMatrix().GetElement(i, j) for j in range(4)] for i in range(4)])
        np.testing.assert_allclose(actual, frame)

    def test_axis_lengths_match_magnitudes_and_model_bounds(self):
        data = np.zeros((30, 30, 30), dtype=np.int8)
        data[5:25, 10:20, 13:17] = 127
        spacing = np.array([0.1, 0.3, 0.7])
        frame = generator.placement(data, spacing, np.zeros(3), position=('principal_axes', 0, 0, 0))
        frame = generator.principal_axes_frame(frame, spacing)
        lengths = generator.principal_axis_lengths(data, spacing, np.zeros(3), frame)
        physical = lengths * np.linalg.norm(frame[:3, :3], axis=0)
        expected_magnitudes = np.sqrt((np.array([20., 10., 4.]) ** 2 - 1) / 12)
        np.testing.assert_allclose(physical / physical[0], expected_magnitudes / expected_magnitudes[0])
        self.assertAlmostEqual(physical.max(), 0.5 * np.linalg.norm(spacing * [20, 10, 4]))

    def test_principal_axes_ambiguity_and_cli_conflicts(self):
        with self.assertWarnsRegex(UserWarning, 'ambiguous'):
            generator.placement(np.ones((5, 5, 5)), [1, 1, 1], [0, 0, 0], position=('principal_axes', 0, 0, 0))
        for command in [
            ['view', 'input.aim', '--position', 'principal_axes', '0', '0', '0'],
            ['view', 'input.aim', '--primitive', 'cube', '8',
             '--position', 'centroid', '0', '0', '0', '--transform_file', 'placement.txt'],
            ['cut', 'input.aim', 'output.aim', '--primitive', 'cube', '8',
             '--position', 'principal_axes', '0', '0', '0', '--transform_file', 'placement.txt'],
        ]:
            with self.assertRaises(SystemExit):
                generator.main(command)
        args = generator.create_parser().parse_args([
            'view', 'input.aim', '--primitive', 'cube', '8',
            '--position', 'principal_axes', '1', '2', '3'])
        self.assertEqual(args.position, ['principal_axes', '1', '2', '3'])

    def test_remove_fragments_preserves_connected_labels(self):
        data = np.zeros((12, 12, 12), dtype=np.int8)
        data[2:6, 2:6, 2:6] = 42
        data[6, 6, 6] = 73  # Corner contact is connected.
        data[10, 10, 10] = 127
        cleaned = generator.remove_fragments(data)
        self.assertEqual(cleaned[10, 10, 10], 0)
        self.assertEqual(cleaned[6, 6, 6], 73)
        np.testing.assert_array_equal(cleaned[2:6, 2:6, 2:6], data[2:6, 2:6, 2:6])
        self.assertEqual(data[10, 10, 10], 127)
        np.testing.assert_array_equal(generator.remove_fragments(np.zeros_like(data)), np.zeros_like(data))
        np.testing.assert_array_equal(generator.remove_fragments(cleaned), cleaned)
        parser = generator.create_parser()
        command = ['cut', 'a.aim', 'b.aim', '--primitive', 'cube', '4']
        self.assertFalse(parser.parse_args(command).remove_fragments)
        self.assertTrue(parser.parse_args(command + ['--remove_fragments']).remove_fragments)

    def test_combined_primitive_cli(self):
        for name, sizes in [('sphere', ['8']), ('cube', ['8']),
                            ('box', ['4', '6', '8']), ('cylinder', ['4', '8'])]:
            for mode in ['cut', 'add', 'view']:
                command = [mode, 'input.aim'] + (['output.aim'] if mode != 'view' else [])
                with patch.object(generator, mode) as handler:
                    generator.main(command + ['--primitive', name] + sizes)
                    args = handler.call_args.args[0]
                    self.assertEqual(args.primitive, name)
                    np.testing.assert_array_equal(args.dimensions, list(map(int, sizes)))
        for tokens in [['box', '4', '6'], ['cylinder', '4', '8', '9'],
                       ['sphere', '1.5'], ['cube', '0'], ['cone', '4'],
                       ['cube', '4', '4'], ['box', '4']]:
            with self.assertRaises(SystemExit):
                generator.main(['view', 'input.aim', '--primitive'] + tokens)

    def test_new_primitive_masks_and_sources(self):
        transform = np.eye(4)
        transform[:3, 3] = 14
        for name, dimensions, volume in [('box', (4, 6, 8), 192), ('cylinder', (4, 8), 104)]:
            mask = generator.primitive_mask((29, 29, 29), [1, 1, 1], [0, 0, 0], name, dimensions, transform)
            self.assertEqual(mask.sum(), volume)
            self.assertTrue(mask[14, 14, 17])
            self.assertFalse(mask[14, 14, 18])
            self.assertFalse(mask[17, 14, 14])
            # Verify rendering uses matching local dimensions and a Z-axis cylinder.
            try:
                source = generator.PRIMITIVES[name]['source'](dimensions)
            except ImportError:
                continue
            source.Update()
            bounds = np.array(source.GetOutput().GetBounds()).reshape(3, 2)
            expected = [4, 6, 8] if name == 'box' else [4, 4, 8]
            np.testing.assert_allclose(bounds[:, 1] - bounds[:, 0], expected, atol=1e-5)
            np.testing.assert_allclose(bounds.mean(axis=1), 0, atol=1e-5)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'placement.txt'
                generator.write_transform(path, transform)
                restored = generator.read_transform(path)
                np.testing.assert_array_equal(mask, generator.primitive_mask(
                    mask.shape, [1, 1, 1], [0, 0, 0], name, dimensions, restored))

    def test_origin_position_and_clipping(self):
        data = np.zeros((20, 20, 20), dtype=np.int8)
        data[10, 10, 10] = 127
        spacing = np.array([0.1, 0.2, 0.3])
        origin = np.array([7., 8., 9.])
        matrix = generator.placement(data, spacing, origin)
        np.testing.assert_allclose(matrix[:3, 3], origin)
        for kind, sizes in [('cube', (4,)), ('box', (4, 6, 8)),
                            ('sphere', (4,)), ('cylinder', (4, 8))]:
            self.assertTrue(generator.primitive_is_clipped(data.shape, spacing, origin, kind, sizes, matrix))
            centered = generator.placement(data, spacing, origin, position=('centroid', 0, 0, 0))
            self.assertFalse(generator.primitive_is_clipped(data.shape, spacing, origin, kind, sizes, centered))
        shifted = generator.placement(data, spacing, origin, position=('origin', 1.5, -2, 3))
        np.testing.assert_allclose(shifted[:3, 3], origin + spacing * [1.5, -2, 3])
        for values in [('unknown', '0', '0', '0'), ('origin', 'nan', '0', '0')]:
            with self.assertRaises(SystemExit):
                generator.main(['view', 'a.aim', '--primitive', 'cube', '4', '--position', *values])

    def test_viewer_refinement_exports_complete_transform(self):
        """Exercise real viewer save callbacks without opening an OpenGL window."""
        try:
            import vtkmodules.vtkRenderingCore as rendering
            from vtkmodules.vtkCommonDataModel import vtkImageData
            from vtkmodules.vtkCommonTransforms import vtkTransform
            from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
            from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
        except ImportError:
            self.skipTest('VTK is required for actor round trips')
        test = self
        coordinates = np.indices((25, 25, 25)).reshape(3, -1).T - 12
        angle = np.deg2rad(30)
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                             [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
        local = coordinates @ rotation
        data = (np.sum((local / [9, 6, 4]) ** 2, axis=1) <= 1).reshape((25,) * 3).astype(np.int8) * 127
        origin = np.array([10., 20., 30.])

        class Window(rendering.vtkRenderWindow):
            def Render(self):
                pass

        class Interactor(rendering.vtkRenderWindowInteractor):
            def Initialize(self):
                pass

            def TerminateApp(self):
                self.terminated = True

            def Start(self):
                renderer = self.GetRenderWindow().GetRenderers().GetFirstRenderer()
                actors = renderer.GetActors()
                primitive = next(actors.GetItemAsObject(i) for i in range(actors.GetNumberOfItems())
                                 if actors.GetItemAsObject(i).GetPickable())
                initial = np.array([[primitive.GetMatrix().GetElement(i, j) for j in range(4)] for i in range(4)])
                # Trackball actor interaction can modify the user matrix. Apply
                # a world rotation about the actor center plus translation.
                move = vtkTransform()
                move.PostMultiply()
                move.SetMatrix(primitive.GetUserMatrix())
                center = primitive.GetCenter()
                move.Translate(*(-np.array(center)))
                move.RotateWXYZ(23, 1, 2, 3)
                move.Translate(*center)
                move.Translate(0.13, -0.21, 0.17)
                primitive.SetUserMatrix(move.GetMatrix())
                # Also verify actor-local adjustments are included in export.
                primitive.RotateY(11)
                primitive.AddPosition(0.04, -0.03, 0.02)
                saved_matrices = []
                for key in ['u', 'q']:
                    if key == 'q':
                        primitive.AddPosition(0.05, 0.02, -0.01)
                    final = primitive.GetMatrix()
                    expected = np.array([[final.GetElement(i, j) for j in range(4)] for i in range(4)])
                    test.assertFalse(np.allclose(expected, initial))
                    self.SetKeyEventInformation(0, 0, key, 0, key)
                    self.InvokeEvent('KeyPressEvent')
                    loaded = generator.placement(data, spacing, origin, transform_file=output)
                    np.testing.assert_array_equal(loaded, expected)
                    saved_matrices.append(loaded)
                    # Independent VTK geometry transform versus the reloaded map.
                    primitive.GetMapper().Update()
                    geometry = primitive.GetMapper().GetInput()
                    transform = vtkTransform()
                    transform.SetMatrix(final)
                    world = vtkTransformPolyDataFilter()
                    world.SetInputData(geometry)
                    world.SetTransform(transform)
                    world.Update()
                    local_points = vtk_to_numpy(geometry.GetPoints().GetData())
                    reloaded_points = local_points @ loaded[:3, :3].T + loaded[:3, 3]
                    np.testing.assert_allclose(reloaded_points,
                        vtk_to_numpy(world.GetOutput().GetPoints().GetData()), atol=5e-6, rtol=1e-6)
                    expected_mask = generator.primitive_mask(data.shape, spacing, origin, name, sizes, expected)
                    actual_mask = generator.primitive_mask(data.shape, spacing, origin, name, sizes, loaded)
                    test.assertTrue(expected_mask.any())
                    np.testing.assert_array_equal(actual_mask, expected_mask)
                test.assertFalse(np.array_equal(*saved_matrices))
                test.assertTrue(self.terminated)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'final.txt'
            seed = Path(directory) / 'initial.txt'
            for spacing in [np.ones(3), np.array([0.1, 0.2, 0.3])]:
                image = vtkImageData()
                image.SetDimensions(*data.shape)
                image.SetSpacing(*spacing)
                image.SetOrigin(*origin)
                image.GetPointData().SetScalars(numpy_to_vtk(data.ravel(order='F'), deep=True))
                generator.write_transform(seed, generator.placement(
                    data, spacing, origin, position=('principal_axes', 1, -1, 2)), overwrite=True)
                modes = [
                    ['--position', 'origin', '12', '12', '12'],
                    ['--position', 'centroid', '1', '-1', '2'],
                    ['--position', 'principal_axes', '1', '-1', '2'],
                    ['--transform_file', str(seed)],
                ]
                for name, sizes in [('cube', (6,)), ('sphere', (6,)),
                                    ('box', (4, 6, 8)), ('cylinder', (6, 8))]:
                    for mode in modes:
                        with self.subTest(spacing=spacing, primitive=name, placement=mode):
                            with patch.object(rendering, 'vtkRenderWindow', Window), \
                                 patch.object(rendering, 'vtkRenderWindowInteractor', Interactor), \
                                 patch.object(generator, 'read_aim', return_value=(None, image, data)):
                                generator.main(['view', 'input.aim', '--primitive', name,
                                                *map(str, sizes), '--transform_output', str(output),
                                                '--overwrite', *mode])

    def test_cutout_complement_and_inner_detail(self):
        data = np.full((19, 19, 19), 127, dtype=np.int8)
        primitive = np.zeros_like(data, dtype=bool)
        primitive[4:15, 4:15, 4:15] = True
        remainder = generator.cut_volume(data, primitive)
        piece = generator.cutout_volume(data, primitive)
        np.testing.assert_array_equal(remainder.astype(int) + piece, data)
        reference = np.zeros_like(data)
        reference[4, 8, 8] = 42
        detailed = generator.cutout_volume(data, primitive, reference, 2)
        self.assertEqual(detailed[4, 8, 8], 42)
        self.assertEqual(detailed[4, 9, 9], 0)
        self.assertEqual(detailed[9, 9, 9], 127)
        self.assertTrue(np.all(detailed[~primitive] == 0))
        with patch('builtins.print') as message:
            thin = generator.cutout_volume(data, primitive, reference, 20)
        np.testing.assert_array_equal(thin, np.where(primitive, reference, 0))
        self.assertTrue(any('no interior' in str(call) for call in message.call_args_list))

    def test_cutout_paths_validated_before_processing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output, piece = root/'input.aim', root/'out.aim', root/'piece.aim'
            for path in [source, output]:
                path.write_bytes(b'original')
            commands = [
                ['--cutout_output', str(output)],
                ['--cutout_output', str(source)],
                ['--cutout_output', str(piece), '--detail', str(piece), '2'],
            ]
            for extra in commands:
                with patch.object(generator, 'read_aim') as read, self.assertRaises(SystemExit):
                    generator.main(['cut', str(source), str(output), '--primitive', 'cube', '4',
                                    '--overwrite', *extra])
                read.assert_not_called()
            piece.write_bytes(b'existing piece')
            with patch.object(generator, 'read_aim') as read, self.assertRaises(SystemExit):
                generator.main(['cut', str(source), str(root/'new.aim'), '--primitive', 'cube', '4',
                                '--cutout_output', str(piece)])
            read.assert_not_called()
            self.assertEqual(piece.read_bytes(), b'existing piece')

    def test_paired_preview_shared_camera_and_cancel(self):
        try:
            import vtkmodules.vtkRenderingCore as rendering
            from vtkmodules.vtkCommonDataModel import vtkImageData
        except ImportError:
            self.skipTest('VTK required')
        test = self
        image = vtkImageData()
        image.SetDimensions(15, 15, 15)
        image.SetSpacing(0.1, 0.2, 0.3)
        image.SetOrigin(1, 2, 3)
        remaining = np.zeros((15, 15, 15), dtype=np.int8)
        remaining[2:6, 2:12, 2:12] = 127
        piece = np.zeros_like(remaining)
        piece[6:12, 2:12, 2:12] = 127
        class Window(rendering.vtkRenderWindow):
            def Render(self):
                pass
        class Interactor(rendering.vtkRenderWindowInteractor):
            def Initialize(self):
                pass
            def TerminateApp(self):
                self.terminated = True
            def Start(self):
                panels = self.GetRenderWindow().GetRenderers()
                test.assertEqual(panels.GetNumberOfItems(), 2)
                left, right = panels.GetItemAsObject(0), panels.GetItemAsObject(1)
                test.assertEqual(left.GetActiveCamera(), right.GetActiveCamera())
                test.assertEqual(left.GetViewport(), (0., 0., .5, 1.))
                test.assertEqual(right.GetViewport(), (.5, 0., 1., 1.))
                left.GetActiveCamera().Azimuth(20)
                test.assertEqual(left.GetActiveCamera().GetPosition(), right.GetActiveCamera().GetPosition())
                self.SetKeyEventInformation(0, 0, key, 0, key)
                self.InvokeEvent('KeyPressEvent')
                test.assertTrue(self.terminated)
        for key in ['q', 'x']:
            with patch.object(rendering, 'vtkRenderWindow', Window), patch.object(rendering, 'vtkRenderWindowInteractor', Interactor):
                accepted = generator.render_image(image, remaining, allow_cancel=True, cutout_data=piece)
                self.assertEqual(accepted, key == 'q')

    def test_view_x_exits_without_saving(self):
        try:
            import vtkmodules.vtkRenderingCore as rendering
            from vtkmodules.vtkCommonDataModel import vtkImageData
        except ImportError:
            self.skipTest('VTK required')
        test = self
        data = self.shell()
        image = vtkImageData()
        image.SetDimensions(*data.shape)
        class Window(rendering.vtkRenderWindow):
            def Render(self):
                pass
        class Interactor(rendering.vtkRenderWindowInteractor):
            def Initialize(self):
                pass
            def TerminateApp(self):
                self.terminated = True
            def Start(self):
                self.SetKeyEventInformation(0, 0, 'x', 0, 'x')
                self.InvokeEvent('KeyPressEvent')
                test.assertTrue(self.terminated)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'transform.txt'
            for existing in [False, True]:
                if existing:
                    target.write_text('previously saved transform')
                for primitive in [[], ['--primitive', 'cube', '8']]:
                    with patch.object(rendering, 'vtkRenderWindow', Window), \
                         patch.object(rendering, 'vtkRenderWindowInteractor', Interactor), \
                         patch.object(generator, 'read_aim', return_value=(None, image, data)), \
                         patch.object(generator, 'write_transform') as write, \
                         patch.object(generator, 'suggest_cut_command') as suggest:
                        generator.main(['view', 'input.aim', '--transform_output', str(target),
                                        '--overwrite', *primitive])
                        write.assert_not_called()
                        suggest.assert_not_called()
                    if existing:
                        self.assertEqual(target.read_text(), 'previously saved transform')
                    else:
                        self.assertFalse(target.exists())

    def test_parser(self):
        args = generator.create_parser().parse_args(['cut', 'a.aim', 'b.aim', '--primitive', 'sphere', '10'])
        self.assertFalse(args.remove_fragments)
        filled = generator.create_parser().parse_args(['fill', 'a.aim', 'b.aim'])
        self.assertEqual((filled.close, filled.erode, filled.remove_fragments), (10, 6, False))
        with self.assertRaises(SystemExit):
            generator.main(['cut', 'a.aim', 'b.aim', '--primitive', 'cube'])

    def test_generated_aim_workflow(self):
        try:
            import vtkbone
            from vtkmodules.vtkCommonDataModel import vtkImageData
            from vtkmodules.util.numpy_support import numpy_to_vtk
        except ImportError:
            self.skipTest('vtkbone is required for AIM integration')
        data = self.shell()
        data[1, 1, 1] = 42
        image = vtkImageData()
        image.SetDimensions(*data.shape)
        image.SetSpacing(0.1, 0.2, 0.3)
        image.SetOrigin(1.0, 2.0, 3.0)
        image.GetPointData().SetScalars(numpy_to_vtk(data.ravel(order='F'), deep=True))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.aim'
            writer = vtkbone.vtkboneAIMWriter()
            writer.SetInputData(image)
            writer.SetFileName(str(source))
            writer.SetProcessingLog('Synthetic test segmentation')
            writer.Update()
            _, source_image, native = generator.read_aim(source)
            spacing, origin = generator.image_geometry(source_image)
            filled_path = Path(directory) / 'filled.aim'
            generator.main(['fill', str(source), str(filled_path), '--close', '0', '--erode', '0'])
            fill_reader, fill_image, filled = generator.read_aim(filled_path)
            expected_fill, _ = generator.solid_body(native, close=0, erosion=0)
            np.testing.assert_array_equal(filled, expected_fill)
            self.assertEqual(filled[1, 1, 1], 42)  # Fragment retained by default.
            self.assertIn('Synthetic test segmentation', fill_reader.GetProcessingLog())
            matrix = generator.placement(native, spacing, origin, position=('centroid', 0, 0, 0))
            transform = Path(directory) / 'placement.txt'
            generator.write_transform(transform, matrix)
            mask = generator.primitive_mask(native.shape, spacing, origin, 'sphere', (6,), matrix)
            for detail in [False, True]:
                target = Path(directory) / f'cut_{detail}.aim'
                piece_path = Path(directory) / f'piece_{detail}.aim'
                command = ['cut', str(filled_path), str(target), '--primitive', 'sphere', '6',
                           '--transform_file', str(transform), '--cutout_output', str(piece_path)]
                if detail:
                    command += ['--detail', str(source), '2']
                expected = generator.cut_volume(filled, mask, native if detail else None, 2 if detail else None)
                def check_preview(preview_image, preview_data, **kwargs):
                    self.assertFalse(target.exists())
                    self.assertFalse(piece_path.exists())
                    np.testing.assert_array_equal(kwargs['cutout_data'], generator.cutout_volume(
                        filled, mask, native if detail else None, 2 if detail else None))
                    np.testing.assert_array_equal(preview_data, expected)
                    return True
                with patch.object(generator, 'render_image', side_effect=check_preview):
                    generator.main(command + ['--visualize'])
                reader, out_image, result = generator.read_aim(target)
                np.testing.assert_array_equal(result, expected)
                np.testing.assert_allclose(out_image.GetOrigin(), source_image.GetOrigin())
                np.testing.assert_allclose(out_image.GetSpacing(), source_image.GetSpacing())
                self.assertEqual(out_image.GetExtent(), source_image.GetExtent())
                self.assertIn('Primitive transform', reader.GetProcessingLog())
                piece_reader, piece_image, piece = generator.read_aim(piece_path)
                np.testing.assert_array_equal(piece, generator.cutout_volume(
                    filled, mask, native if detail else None, 2 if detail else None))
                self.assertEqual(piece_image.GetExtent(), out_image.GetExtent())
                np.testing.assert_allclose(piece_image.GetOrigin(), out_image.GetOrigin())
                np.testing.assert_allclose(piece_image.GetSpacing(), out_image.GetSpacing())
                self.assertIn('Output role: cutout', piece_reader.GetProcessingLog())
            cleaned_path = Path(directory) / 'cleaned.aim'
            generator.main(['cut', str(filled_path), str(cleaned_path), '--primitive', 'sphere', '6',
                            '--transform_file', str(transform), '--remove_fragments'])
            _, _, cleaned = generator.read_aim(cleaned_path)
            self.assertEqual(cleaned[1, 1, 1], 0)

            # Expand on both lower and upper sides with nonzero physical origin.
            for x in [-7, 30]:
                target = Path(directory) / f'add_{x}.aim'
                matrix = generator.placement(native, spacing, origin, position=('origin', x, 12, 12))
                expected, expanded_origin = generator.expand_for_primitive(native, spacing, origin, 'box', (6, 8, 10), matrix)
                added_mask = generator.primitive_mask(expected.shape, spacing, expanded_origin, 'box', (6, 8, 10), matrix)
                expected[added_mask] = 127
                generator.main(['add', str(source), str(target), '--primitive', 'box', '6', '8', '10',
                                '--position', 'origin', str(x), '12', '12'])
                _, out_image, result = generator.read_aim(target)
                np.testing.assert_array_equal(result, expected)
                np.testing.assert_allclose(out_image.GetOrigin(), expanded_origin, atol=1e-6)
                np.testing.assert_allclose(out_image.GetSpacing(), spacing)
                self.assertGreater(result.shape[0], native.shape[0])
                # A detached added body and the original foreground both survive.
                self.assertGreater(np.count_nonzero(result), np.count_nonzero(native))

            for mode, extra in [('fill', []), ('cut', ['--primitive', 'cube', '4']),
                                ('add', ['--primitive', 'cube', '4'])]:
                target = Path(directory) / f'cancel_{mode}.aim'
                command = [mode, str(source), str(target), *extra, '--visualize']
                cancelled_piece = Path(directory) / 'cancelled_piece.aim'
                if mode == 'cut':
                    command += ['--cutout_output', str(cancelled_piece)]
                with patch.object(generator, 'render_image', return_value=False):
                    generator.main(command)
                    self.assertFalse(target.exists())
                    if mode == 'cut':
                        self.assertFalse(cancelled_piece.exists())
                        cancelled_piece.write_bytes(b'existing piece')
                    target.write_bytes(b'existing output')
                    generator.main(command + ['--overwrite'])
                    self.assertEqual(target.read_bytes(), b'existing output')
                    if mode == 'cut':
                        self.assertEqual(cancelled_piece.read_bytes(), b'existing piece')

    def test_expansion_preserves_world_coordinates_for_all_shapes(self):
        data = np.full((5, 6, 7), 42, dtype=np.int8)
        spacing = np.array([0.1, 0.2, 0.3])
        origin = np.array([3., 4., 5.])
        angle = np.deg2rad(35)
        rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                             [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
        matrix = np.eye(4)
        matrix[:3, :3] = spacing[:, None] * rotation / spacing[None, :]
        matrix[:3, 3] = origin + spacing * [-8, 12, 3]
        for name, sizes in [('cube', (8,)), ('sphere', (8,)),
                            ('box', (8, 10, 12)), ('cylinder', (8, 12))]:
            expanded, new_origin = generator.expand_for_primitive(data, spacing, origin, name, sizes, matrix)
            self.assertFalse(generator.primitive_is_clipped(expanded.shape, spacing, new_origin, name, sizes, matrix))
            shift = np.rint((origin - new_origin) / spacing).astype(int)
            original_region = tuple(slice(a, a+n) for a, n in zip(shift, data.shape))
            np.testing.assert_array_equal(expanded[original_region], data)
            np.testing.assert_allclose(new_origin + shift * spacing, origin)
            self.assertEqual(np.count_nonzero(expanded), data.size)
            self.assertGreater(generator.primitive_mask(expanded.shape, spacing, new_origin, name, sizes, matrix).sum(), 0)

    def test_detail_geometry_rejects_mismatch(self):
        try:
            from vtkmodules.vtkCommonDataModel import vtkImageData
        except ImportError:
            self.skipTest('VTK required')
        image = vtkImageData()
        image.SetDimensions(10, 12, 14)
        image.SetSpacing(0.1, 0.2, 0.3)
        reference = vtkImageData()
        reference.DeepCopy(image)
        generator.check_detail_geometry(image, reference)
        for change in [lambda: reference.SetDimensions(11, 12, 14),
                       lambda: reference.SetOrigin(0.1, 0, 0),
                       lambda: reference.SetSpacing(0.2, 0.2, 0.3)]:
            reference.DeepCopy(image)
            change()
            with self.assertRaises(ValueError):
                generator.check_detail_geometry(image, reference)


if __name__ == '__main__':
    unittest.main()
