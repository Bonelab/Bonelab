'''Test handle_filetype_writing_special_cases'''

import unittest
import vtk
import vtkbone
import shutil, tempfile
import os
import vtk
import vtkbone

from bonelab.io.vtk_helpers import handle_filetype_writing_special_cases


class TestHandleFiletypeWritingSpecialCases(unittest.TestCase):
    '''Test handle_filetype_writing_special_cases'''

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def generate_image(self, scalar_type):
        # Create source
        source = vtk.vtkImageEllipsoidSource()
        source.SetWholeExtent(0, 20, 0, 20, 0, 0)
        source.SetCenter(10, 10, 0)
        source.SetRadius(3, 4, 0)
        source.SetOutputScalarType(scalar_type)

        return source

    def test_passes_unsupported_filters(self):
        '''Passes unsupported filters'''
        writer = vtk.vtkImageCast()
        handle_filetype_writing_special_cases(writer)

    def test_write_aim_short(self):
        '''Can write aim file with type short'''
        extension='.aim'
        filename = os.path.join(self.test_dir, 'file'+extension)
        scalar_type = vtk.VTK_SHORT

        source = self.generate_image(scalar_type)
        writer = vtkbone.vtkboneAIMWriter()
        writer.SetInputConnection(source.GetOutputPort())
        writer.SetFileName(filename)

        handle_filetype_writing_special_cases(writer)

        writer.Update()
        self.assertTrue(os.path.isfile(filename))

        reader = vtkbone.vtkboneAIMReader()
        reader.DataOnCellsOff()
        reader.SetFileName(filename)
        reader.Update()

        self.assertEqual(reader.GetOutput().GetScalarType(), vtk.VTK_SHORT)

    def test_write_aim_unsigned_long(self):
        '''Can write aim file with type unsigned long'''
        extension='.aim'
        filename = os.path.join(self.test_dir, 'file'+extension)
        scalar_type = vtk.VTK_UNSIGNED_LONG

        source = self.generate_image(scalar_type)
        writer = vtkbone.vtkboneAIMWriter()
        writer.SetInputConnection(source.GetOutputPort())
        writer.SetFileName(filename)

        handle_filetype_writing_special_cases(writer)

        writer.Update()
        self.assertTrue(os.path.isfile(filename))

        reader = vtkbone.vtkboneAIMReader()
        reader.DataOnCellsOff()
        reader.SetFileName(filename)
        reader.Update()

        self.assertEqual(reader.GetOutput().GetScalarType(), vtk.VTK_FLOAT)

    def test_write_aim_set_log(self):
        '''Can write aim file with processing log'''
        extension='.aim'
        filename = os.path.join(self.test_dir, 'file'+extension)
        scalar_type = vtk.VTK_SHORT
        processing_log = 'This is a fake processing log'

        source = self.generate_image(scalar_type)
        writer = vtkbone.vtkboneAIMWriter()
        writer.SetInputConnection(source.GetOutputPort())
        writer.SetFileName(filename)

        handle_filetype_writing_special_cases(writer, processing_log=processing_log)

        writer.Update()
        self.assertTrue(os.path.isfile(filename))

        reader = vtkbone.vtkboneAIMReader()
        reader.DataOnCellsOff()
        reader.SetFileName(filename)
        reader.Update()

        self.assertEqual(reader.GetOutput().GetScalarType(), vtk.VTK_SHORT)

        # A dummy log is created in this instance. Only check that our log was appended
        self.assertEqual(reader.GetProcessingLog().split(os.linesep)[-1], processing_log)

    def test_write_tiff_unsigned_short(self):
        '''Can write tiff file with type unsigned short'''
        extension='.tiff'
        filename = os.path.join(self.test_dir, 'file'+extension)
        scalar_type = vtk.VTK_UNSIGNED_SHORT

        source = self.generate_image(scalar_type)
        writer = vtk.vtkTIFFWriter()
        writer.SetInputConnection(source.GetOutputPort())
        writer.SetFileName(filename)

        handle_filetype_writing_special_cases(writer)

        writer.Update()
        self.assertTrue(os.path.isfile(filename))

        reader = vtk.vtkTIFFReader()
        reader.SetFileName(filename)
        reader.Update()

        self.assertEqual(reader.GetOutput().GetScalarType(), vtk.VTK_UNSIGNED_SHORT)

    def test_write_tiff_unsigned_long(self):
        '''Can write tiff file with type unsigned long'''
        extension='.tiff'
        filename = os.path.join(self.test_dir, 'file'+extension)
        scalar_type = vtk.VTK_UNSIGNED_LONG

        source = self.generate_image(scalar_type)
        writer = vtk.vtkTIFFWriter()
        writer.SetInputConnection(source.GetOutputPort())
        writer.SetFileName(filename)

        handle_filetype_writing_special_cases(writer)

        writer.Update()
        self.assertTrue(os.path.isfile(filename))

        reader = vtk.vtkTIFFReader()
        reader.SetFileName(filename)
        reader.Update()

        self.assertEqual(reader.GetOutput().GetScalarType(), vtk.VTK_FLOAT)


if __name__ == '__main__':
    unittest.main()
