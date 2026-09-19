"""Block reduction and AIM/NIfTI metadata regression tests."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from bonelab.cli import ImageFilter as filters


class TestImageFilter(unittest.TestCase):
    def test_binary_majority_and_ties(self):
        for label in [1, 127]:
            data = np.zeros((4, 2, 2), dtype=np.int8)
            data[:2].flat[:4] = label
            data[2:].flat[:5] = label
            result, mode = filters.reduce_array(data, 2)
            np.testing.assert_array_equal(result[:, 0, 0], [0, label])
            self.assertEqual(result.dtype, data.dtype)
            self.assertIn('majority', mode)
        data = np.zeros((3, 3, 3), dtype=np.uint8)
        data.flat[:14] = 127
        self.assertEqual(filters.reduce_array(data, 3)[0].item(), 127)

    def test_raw_average_rounding_and_trimming(self):
        data = np.arange(7*8*9, dtype=np.int16).reshape(7, 8, 9) - 250
        for factor in [2, 3]:
            result, mode = filters.reduce_array(data, factor)
            expected = np.empty(tuple(n//factor for n in data.shape), dtype=np.int16)
            for index in np.ndindex(expected.shape):
                block = data[tuple(slice(i*factor, (i+1)*factor) for i in index)]
                expected[index] = np.rint(block.mean())
            np.testing.assert_array_equal(result, expected)
            self.assertEqual(result.dtype, np.int16)
            self.assertIn('raw', mode)
        # Short values in a segmentation-like range must still be averaged.
        data = np.zeros((2, 2, 2), dtype=np.int16)
        data.flat[:4] = 127
        self.assertEqual(filters.reduce_array(data, 2)[0].item(), 64)
        data.fill(-32768)
        self.assertEqual(filters.reduce_array(data, 2)[0].item(), -32768)

    def test_invalid_inputs(self):
        for factor in [0, 1, 1.5, 4]:
            with self.assertRaises(ValueError):
                filters.reduce_array(np.zeros((3, 3, 3), dtype=np.int8), factor)
        for data in [np.array([0, 1, 2, 0, 0, 0, 0, 0], dtype=np.int8).reshape(2,2,2),
                     np.full((2,2,2), -1, dtype=np.int8),
                     np.full((2,2,2), 255, dtype=np.uint8),
                     np.zeros((2,2,2), dtype=float)]:
            with self.assertRaises(ValueError):
                filters.reduce_array(data, 2)
        np.testing.assert_array_equal(filters.reduce_array(np.zeros((2,2,2), dtype=np.int8),2)[0], 0)

    def test_names_and_parser(self):
        for source, expected in [('x.AIM','x_R02.AIM'), ('x.nii','x_R02.nii'), ('a/x.nii.gz','a/x_R02.nii.gz')]:
            self.assertEqual(filters.reduced_filename(source,2),expected)
        self.assertEqual(filters.reduced_filename('x.aim',100),'x_R100.aim')
        for factor in ['1','2.5','-2']:
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                filters.create_parser().parse_args(['reduce','x.aim','--factor',factor])

    def make_image(self, data):
        from vtkmodules.vtkCommonDataModel import vtkImageData
        from vtkmodules.util.numpy_support import numpy_to_vtk
        image = vtkImageData()
        image.SetDimensions(*data.shape)
        image.SetSpacing(0.1,0.2,0.3)
        image.SetOrigin(1,2,3)
        image.GetPointData().SetScalars(numpy_to_vtk(data.ravel(order='F'), deep=True))
        return image

    def write_source(self, filename, data, qfac=1):
        from vtkmodules.vtkCommonMath import vtkMatrix4x4
        from vtkmodules.vtkIOImage import vtkNIFTIImageWriter
        image = self.make_image(data)
        if str(filename).endswith('.aim'):
            import vtkbone
            writer = vtkbone.vtkboneAIMWriter()
            writer.SetProcessingLog('Synthetic ImageFilter source')
        else:
            writer = vtkNIFTIImageWriter()
            image.SetOrigin(0,0,0)
            matrix = vtkMatrix4x4()
            for i,row in enumerate([[0,-1,0,11],[1,0,0,22],[0,0,1,33],[0,0,0,1]]):
                for j,value in enumerate(row): matrix.SetElement(i,j,value)
            writer.SetQFormMatrix(matrix)
            writer.SetSFormMatrix(matrix)
            writer.SetQFac(qfac)
            writer.SetRescaleSlope(2)
            writer.SetRescaleIntercept(-7)
        writer.SetInputData(image)
        writer.SetFileName(str(filename))
        filters.update_checked(writer)

    def test_aim_all_commands_and_scalar_preservation(self):
        with tempfile.TemporaryDirectory() as folder:
            for dtype in [np.int8, np.int16]:
                data = np.zeros((7,8,9), dtype=dtype)
                if dtype == np.int8:
                    data[1:6,1:7,1:8] = 127
                else:
                    data[:] = np.arange(data.size).reshape(data.shape) - 250
                source=Path(folder)/f'{np.dtype(dtype).name}.aim'
                self.write_source(source,data)
                _, original=filters.read_image(source)
                native=filters.image_array(original).copy()
                for factor in [2,3]:
                    with contextlib.redirect_stdout(io.StringIO()) as output:
                        filters.main(['reduce',str(source),'--factor',str(factor)])
                    self.assertIn('Trimming incomplete blocks',output.getvalue())
                    reader,image=filters.read_image(filters.reduced_filename(source,factor))
                    np.testing.assert_array_equal(filters.image_array(image),filters.reduce_array(native,factor)[0])
                    self.assertEqual(image.GetScalarType(),original.GetScalarType())
                    np.testing.assert_allclose(image.GetSpacing(),np.array(original.GetSpacing())*factor)
                    self.assertIn('Synthetic ImageFilter source', reader.GetProcessingLog())
                    self.assertIn(f'reduce factor={factor}',reader.GetProcessingLog())
                    requested=filters.first_voxel_origin(original)+(factor-1)/2*np.array(original.GetSpacing())
                    delta=np.abs(np.array(image.GetOrigin())-requested)
                    self.assertTrue(np.all(delta <= np.array(image.GetSpacing())+1e-6))
                target=Path(folder)/f'threshold_{np.dtype(dtype).name}.aim'
                filters.main(['thres',str(source),str(target),'--range','-5','5'])
                _,image=filters.read_image(target)
                np.testing.assert_array_equal(filters.image_array(image),np.where((native>=-5)&(native<=5),native,0))
                target=Path(folder)/f'crop_{np.dtype(dtype).name}.aim'
                filters.main(['subvol',str(source),str(target),'--voi','1','4','2','5','3','7'])
                _,image=filters.read_image(target)
                np.testing.assert_array_equal(filters.image_array(image),native[1:5,2:6,3:8])
                np.testing.assert_allclose(image.GetOrigin(),filters.first_voxel_origin(original)+np.array(original.GetSpacing())*[1,2,3],atol=1e-6)
                filters.main(['exam',str(source)])

    def test_nifti_forms_qfac_scaling_and_geometry(self):
        with tempfile.TemporaryDirectory() as folder:
            for extension in ['.nii','.nii.gz']:
                for qfac in [-1,1]:
                    for dtype in [np.uint8,np.int16]:
                        data=np.zeros((6,8,10),dtype=dtype)
                        data[1:5,1:7,1:9]=127
                        source=Path(folder)/f'source_{qfac}_{np.dtype(dtype).name}{extension}'
                        self.write_source(source,data,qfac)
                        reader, original=filters.read_image(source)
                        native=filters.image_array(original).copy()
                        for operation,options,offset in [
                            ('reduce',['--factor','2'],np.array([.5,.5,.5])),
                            ('subvol',['--voi','1','4','2','5','3','7'],np.array([1,2,3])),
                            ('thres',['--range','100','127'],np.zeros(3))]:
                            target=Path(folder)/(operation+source.name)
                            command=[operation,str(source)]
                            if operation!='reduce': command.append(str(target))
                            else: target=Path(filters.reduced_filename(source,2))
                            filters.main(command+options)
                            out_reader,out=filters.read_image(target)
                            for getter in ['GetQFormMatrix','GetSFormMatrix']:
                                before=getattr(reader,getter)(); after=getattr(out_reader,getter)()
                                expected=filters.shifted_matrix(before,offset*np.array(original.GetSpacing()))
                                a=np.array([[after.GetElement(i,j) for j in range(4)] for i in range(4)])
                                b=np.array([[expected.GetElement(i,j) for j in range(4)] for i in range(4)])
                                np.testing.assert_allclose(a,b,atol=2e-5)
                            self.assertEqual(out_reader.GetQFac(),reader.GetQFac())
                            self.assertEqual(out_reader.GetRescaleSlope(),2)
                            self.assertEqual(out_reader.GetRescaleIntercept(),-7)
                            self.assertEqual(out.GetScalarType(),original.GetScalarType())
                            expected_data=(filters.reduce_array(native,2)[0] if operation=='reduce' else
                                           native[1:5,2:6,3:8] if operation=='subvol' else native)
                            np.testing.assert_array_equal(filters.image_array(out),expected_data)

    def test_output_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.aim'; target=Path(folder)/'target.aim'
            target.write_bytes(b'existing')
            with patch('builtins.input',return_value='n'):
                self.assertFalse(filters.output_allowed(source,target,False))
            self.assertEqual(target.read_bytes(),b'existing')
            with self.assertRaises(ValueError): filters.output_allowed(source,source,True)


if __name__=='__main__':
    unittest.main()
