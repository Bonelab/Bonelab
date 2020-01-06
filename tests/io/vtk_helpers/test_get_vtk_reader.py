'''Test get_vtk_reader'''

import unittest
import vtk
import vtkbone
import shutil, tempfile
import os

from bonelab.io.vtk_helpers import get_vtk_reader


class TestGetVTKReader(unittest.TestCase):
    '''Test get VTK reader
    
    Note that DICOM reading is not tested
    '''

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def generate_image(self, filename, writer):
        # Create source
        source = vtk.vtkImageEllipsoidSource()
        source.SetWholeExtent(0, 20, 0, 20, 0, 0)
        source.SetCenter(10, 10, 0)
        source.SetRadius(3, 4, 0)
        source.SetOutputScalarTypeToFloat()

        writer.SetInputConnection(source.GetOutputPort())
        writer.SetFileName(filename)
        writer.Update()

        self.assertTrue(os.path.isfile(filename))

    def test_get_nonexistent_file(self):
        '''Nonexistent file returns None'''
        expected = None
        self.assertEqual(get_vtk_reader(''), expected)

    def test_get_aim(self):
        '''AIM file returns correct reader'''
        extension='.aim'
        expected = type(vtkbone.vtkboneAIMReader())
        writer = vtkbone.vtkboneAIMWriter()

        filename = os.path.join(self.test_dir, 'file'+extension)
        self.generate_image(filename, writer)
        self.assertEqual(type(get_vtk_reader(filename)), expected)

    def test_get_nii(self):
        '''nifti file returns correct reader'''
        extension='.nii'
        expected = type(vtk.vtkNIFTIImageReader())
        writer = vtk.vtkNIFTIImageWriter()

        filename = os.path.join(self.test_dir, 'file'+extension)
        self.generate_image(filename, writer)
        self.assertEqual(type(get_vtk_reader(filename)), expected)

    def test_get_nii_gz(self):
        '''compressed nifti file returns correct reader'''
        extension='.nii.gz'
        expected = type(vtk.vtkNIFTIImageReader())
        writer = vtk.vtkNIFTIImageWriter()

        filename = os.path.join(self.test_dir, 'file'+extension)
        self.generate_image(filename, writer)
        self.assertEqual(type(get_vtk_reader(filename)), expected)

    def test_get_tiff(self):
        '''tiff file returns correct reader'''
        extension='.tiff'
        expected = type(vtk.vtkTIFFReader())
        writer = vtk.vtkTIFFWriter()

        filename = os.path.join(self.test_dir, 'file'+extension)
        self.generate_image(filename, writer)
        self.assertEqual(type(get_vtk_reader(filename)), expected)

    def test_get_tif(self):
        '''tif file returns correct reader'''
        extension='.tif'
        expected = type(vtk.vtkTIFFReader())
        writer = vtk.vtkTIFFWriter()

        filename = os.path.join(self.test_dir, 'file'+extension)
        self.generate_image(filename, writer)
        self.assertEqual(type(get_vtk_reader(filename)), expected)


if __name__ == '__main__':
    unittest.main()
