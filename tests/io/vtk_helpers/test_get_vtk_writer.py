'''Test get_vtk_writer'''

import unittest
import vtk
import vtkbone

from bonelab.io.vtk_helpers import get_vtk_writer


class TestGetVTKWriter(unittest.TestCase):
    '''Test get VTK writer'''

    def test_get_empty(self):
        '''Empty string returns None'''
        expected = None
        self.assertEqual(get_vtk_writer(''), expected)

    def test_get_unknown_filetype(self):
        '''Unknown filetype returns None'''
        expected = None
        self.assertEqual(get_vtk_writer('fake_file.bad.type'), expected)

    def test_get_aim(self):
        '''AIM filetype returns None'''
        expected = type(vtkbone.vtkboneAIMWriter())
        self.assertEqual(type(get_vtk_writer('test25a.AiM')), expected)

    def test_get_nii(self):
        '''nii filetype returns None'''
        expected = type(vtk.vtkNIFTIImageWriter())
        self.assertEqual(type(get_vtk_writer('test.nIi')), expected)

    def test_get_nii_gz(self):
        '''nii.gz filetype returns None'''
        expected = type(vtk.vtkNIFTIImageWriter())
        self.assertEqual(type(get_vtk_writer('test.nIi.gZ')), expected)

    def test_get_mha(self):
        '''mha filetype returns None'''
        expected = type(vtk.vtkMetaImageWriter())
        self.assertEqual(type(get_vtk_writer('test.mHa')), expected)

    def test_get_mhd(self):
        '''mhd filetype returns None'''
        expected = type(vtk.vtkMetaImageWriter())
        self.assertEqual(type(get_vtk_writer('test.mHd')), expected)

    def test_get_mnc(self):
        '''mnc filetype returns None'''
        expected = type(vtk.vtkMINCImageWriter())
        self.assertEqual(type(get_vtk_writer('test.mnC')), expected)

    def test_get_bmp(self):
        '''bmp filetype returns None'''
        expected = type(vtk.vtkBMPWriter())
        self.assertEqual(type(get_vtk_writer('test.Bmp')), expected)

    def test_get_jpeg(self):
        '''jpeg filetype returns None'''
        expected = type(vtk.vtkJPEGWriter())
        self.assertEqual(type(get_vtk_writer('test.jPeg')), expected)

    def test_get_jpg(self):
        '''jpg filetype returns None'''
        expected = type(vtk.vtkJPEGWriter())
        self.assertEqual(type(get_vtk_writer('test.jpG')), expected)

    def test_get_png(self):
        '''png filetype returns None'''
        expected = type(vtk.vtkPNGWriter())
        self.assertEqual(type(get_vtk_writer('test.pNg')), expected)

    def test_get_tiff(self):
        '''tiff filetype returns None'''
        expected = type(vtk.vtkTIFFWriter())
        self.assertEqual(type(get_vtk_writer('test.tIff')), expected)

    def test_get_tif(self):
        '''tif filetype returns None'''
        expected = type(vtk.vtkTIFFWriter())
        self.assertEqual(type(get_vtk_writer('test.Tif')), expected)


if __name__ == '__main__':
    unittest.main()
