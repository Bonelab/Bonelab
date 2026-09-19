"""Numerical tests run without VTK; AIM integration runs when vtkbone exists."""
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
from bonelab.cli import RapidPrototypeModelGenerator as generator


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
        result, stats = generator.solid_body(data, erosion=0)
        self.assertEqual(result[12, 12, 12], 127)
        np.testing.assert_array_equal(result[data > 0], data[data > 0])
        self.assertEqual(stats['components'], 2)
        self.assertTrue(stats['largest_touches_boundary'])
        eroded, _ = generator.solid_body(data, erosion=20)
        np.testing.assert_array_equal(eroded, data)

    def test_open_pore_warns_and_closing_seals_it(self):
        data = self.shell()
        data[3:22, 3:22, 3:22] = 42
        data[8:17, 8:17, 8:17] = 0
        data[3:9, 12, 12] = 0
        with self.assertWarnsRegex(UserWarning, 'increasing --close'):
            opened, stats = generator.solid_body(data, erosion=0)
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
        output, _ = generator.generate(data, primitive, buffer=3, erosion=0)
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
        transform = generator.placement(data, spacing, origin, relative=[1, -2, 3])
        np.testing.assert_allclose(transform[:3, 3], origin + spacing * [8, 5, 10])
        for name in ['cube', 'sphere']:
            mask = generator.primitive_mask(data.shape, spacing, origin, name, 4, transform)
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
        rotated = generator.primitive_mask((20, 30, 40), [1, 1, 1], [0, 0, 0], 'cube', 4,
                                          np.array([[0, -1, 0, 10], [1, 0, 0, 20], [0, 0, 1, 30], [0, 0, 0, 1]]))
        self.assertEqual(np.count_nonzero(rotated), 64)

    def test_boundary_clipping(self):
        data = self.shell()
        matrix = np.eye(4)
        primitive = generator.primitive_mask(data.shape, [1]*3, [0]*3, 'cube', 8, matrix)
        output, _ = generator.generate(data, primitive, erosion=0)
        self.assertEqual(output.shape, data.shape)
        self.assertTrue(np.all(output[primitive] == 0))
        with self.assertRaises(ValueError):
            generator.generate(data, np.zeros_like(primitive))

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
        matrix = generator.placement(data, spacing, origin, relative=offset, use_principal_axes=True)
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
            actual = generator.primitive_mask(data.shape, spacing, origin, primitive, 8, matrix)
            expected = generator.primitive_mask(data.shape, np.ones(3), np.zeros(3), primitive, 8, voxel_matrix)
            np.testing.assert_array_equal(actual, expected)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'pca.txt'
                generator.write_transform(path, matrix)
                restored = generator.placement(data, spacing, origin, transform_file=path)
                mask = generator.primitive_mask(data.shape, spacing, origin, primitive, 8, restored)
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
        frame = generator.placement(data, spacing, np.zeros(3), use_principal_axes=True)
        frame = generator.principal_axes_frame(frame, spacing)
        lengths = generator.principal_axis_lengths(data, spacing, np.zeros(3), frame)
        physical = lengths * np.linalg.norm(frame[:3, :3], axis=0)
        expected_magnitudes = np.sqrt((np.array([20., 10., 4.]) ** 2 - 1) / 12)
        np.testing.assert_allclose(physical / physical[0], expected_magnitudes / expected_magnitudes[0])
        self.assertAlmostEqual(physical.max(), 0.5 * np.linalg.norm(spacing * [20, 10, 4]))

    def test_principal_axes_ambiguity_and_cli_conflicts(self):
        with self.assertWarnsRegex(UserWarning, 'ambiguous'):
            generator.placement(np.ones((5, 5, 5)), [1, 1, 1], [0, 0, 0], use_principal_axes=True)
        for command in [
            ['visualize', 'input.aim', '--principal_axes'],
            ['apply', 'input.aim', 'output.aim', '--primitive', 'cube', '--dimension', '8',
             '--principal_axes', '--transform_file', 'placement.txt'],
        ]:
            with self.assertRaises(SystemExit):
                generator.main(command)
        args = generator.create_parser().parse_args([
            'visualize', 'input.aim', '--primitive', 'cube', '--dimension', '8',
            '--principal_axes', '--relative_to_centroid', '1', '2', '3'])
        self.assertTrue(args.principal_axes)

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
        command = ['apply', 'a.aim', 'b.aim', '--primitive', 'cube', '--dimension', '4']
        self.assertTrue(parser.parse_args(command).remove_fragments)
        self.assertFalse(parser.parse_args(command + ['--no-remove_fragments']).remove_fragments)
        self.assertTrue(parser.parse_args(command + ['--remove_fragments']).remove_fragments)

    def test_parser(self):
        args = generator.create_parser().parse_args(['apply', 'a.aim', 'b.aim', '--primitive', 'sphere', '--dimension', '10'])
        self.assertEqual((args.buffer, args.close, args.erode), (8, 0, 5))
        with self.assertRaises(SystemExit):
            generator.main(['apply', 'a.aim', 'b.aim', '--primitive', 'cube'])

    def test_generated_aim_roundtrip(self):
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
            target = Path(directory) / 'output.aim'
            writer = vtkbone.vtkboneAIMWriter()
            writer.SetInputData(image)
            writer.SetFileName(str(source))
            writer.SetProcessingLog('Synthetic test segmentation')
            writer.Update()
            generator.main(['apply', str(source), str(target), '--primitive', 'sphere', '--dimension', '6', '--buffer', '2', '--erode', '0'])
            reader, output_image, output = generator.read_aim(target)
            _, source_image, native = generator.read_aim(source)
            spacing, origin = generator.image_geometry(source_image)
            matrix = generator.placement(native, spacing, origin)
            mask = generator.primitive_mask(native.shape, spacing, origin, 'sphere', 6, matrix)
            unfiltered, _ = generator.generate(native, mask, 2, 0, 0)
            expected = generator.remove_fragments(unfiltered)
            self.assertEqual(unfiltered[1, 1, 1], 42)
            self.assertEqual(expected[1, 1, 1], 0)
            np.testing.assert_array_equal(output, expected)
            np.testing.assert_allclose(output_image.GetOrigin(), source_image.GetOrigin())
            np.testing.assert_allclose(output_image.GetSpacing(), source_image.GetSpacing())
            self.assertEqual(output_image.GetExtent(), source_image.GetExtent())
            self.assertIn('Synthetic test segmentation', reader.GetProcessingLog())
            self.assertIn('Primitive transform', reader.GetProcessingLog())

            unfiltered_target = Path(directory) / 'unfiltered.aim'
            generator.main(['apply', str(source), str(unfiltered_target), '--primitive', 'sphere',
                            '--dimension', '6', '--buffer', '2', '--erode', '0', '--no-remove_fragments'])
            _, _, unfiltered_saved = generator.read_aim(unfiltered_target)
            np.testing.assert_array_equal(unfiltered_saved, unfiltered)

            preview_target = Path(directory) / 'preview.aim'
            def check_preview(preview_image, preview_data, allow_cancel=False):
                self.assertTrue(allow_cancel)
                from vtkmodules.util.numpy_support import vtk_to_numpy
                self.assertFalse(preview_target.exists(), 'Preview must precede writing.')
                np.testing.assert_array_equal(preview_data, expected)
                pixels = vtk_to_numpy(preview_image.GetPointData().GetScalars())
                np.testing.assert_array_equal(pixels.reshape(expected.shape, order='F'), expected)
                return True
            with patch.object(generator, 'render_image', side_effect=check_preview) as preview:
                generator.main(['apply', str(source), str(preview_target), '--primitive', 'sphere',
                                '--dimension', '6', '--buffer', '2', '--erode', '0', '--visualize'])
                preview.assert_called_once()
            _, _, saved = generator.read_aim(preview_target)
            np.testing.assert_array_equal(saved, expected)

            cancel_target = Path(directory) / 'cancelled.aim'
            command = ['apply', str(source), str(cancel_target), '--primitive', 'sphere',
                       '--dimension', '6', '--buffer', '2', '--erode', '0', '--visualize']
            with patch.object(generator, 'render_image', return_value=False):
                generator.main(command)
                self.assertFalse(cancel_target.exists())
                cancel_target.write_bytes(b'existing output')
                generator.main(command + ['--overwrite'])
                self.assertEqual(cancel_target.read_bytes(), b'existing output')


if __name__ == '__main__':
    unittest.main()
