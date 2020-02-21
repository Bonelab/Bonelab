'''Test aimod'''

import unittest
import subprocess
import shutil, tempfile
import os
try:
    # Python 2
    from StringIO import StringIO
except ModuleNotFoundError:
    # Python 3
    from io import StringIO
import vtkbone

from tests.config_cli import cfg
from bonelab.cli.aimod import aimod


class TestAimod(unittest.TestCase):
    '''Test aimod
    
    We do a small hack here to mimick stdin by setting os.sys.stdin
    explicitely using a StringIO object.
    '''
    filenames = [
        'test25a.aim'
    ]

    def setUp(self):
        # Create temporary directory to work in
        self.test_dir = tempfile.mkdtemp()

        # Download testing data
        for filename in self.filenames:
            # Fetch the data
            download_location = cfg['DOWNLOAD_TESTING_DATA'](filename)
            self.assertNotEqual(download_location, '', 'Unable to download file ' + filename)

            # Copy to temporary directory
            shutil.copy(download_location, self.test_dir)
            self.assertTrue(os.path.isfile(os.path.join(self.test_dir, filename)))

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def test_run(self):
        '''Can run `aimod`'''
        stdin = os.linesep*9
        input_file = os.path.join(self.test_dir, 'test25a.aim')
        output_file = os.path.join(self.test_dir, 'test.aim')
        os.sys.stdin = StringIO(stdin)
        aimod(input_file,output_file)
        self.assertTrue(os.path.isfile(output_file))

    def test_quit(self):
        '''Can run `aimod` with quit'''
        stdin = os.linesep*3 + 'q' + os.linesep*6
        input_file = os.path.join(self.test_dir, 'test25a.aim')
        output_file = os.path.join(self.test_dir, 'test.aim')
        os.sys.stdin = StringIO(stdin)
        with self.assertRaises(SystemExit) as context:
            aimod(input_file,output_file)
        self.assertFalse(os.path.isfile(output_file))

    def test_exit(self):
        '''Can run `aimod` with exit'''
        stdin = os.linesep*3 + 'e' + os.linesep*6
        input_file = os.path.join(self.test_dir, 'test25a.aim')
        output_file = os.path.join(self.test_dir, 'test.aim')
        os.sys.stdin = StringIO(stdin)
        aimod(input_file,output_file)
        self.assertTrue(os.path.isfile(output_file))

    def test_spacing(self):
        '''Can run `aimod` changing spacing'''
        stdin = os.linesep.join(['1', '2', '3']) + os.linesep*7
        input_file = os.path.join(self.test_dir, 'test25a.aim')
        output_file = os.path.join(self.test_dir, 'test.aim')
        os.sys.stdin = StringIO(stdin)
        aimod(input_file,output_file)
        self.assertTrue(os.path.isfile(output_file))

        reader = vtkbone.vtkboneAIMReader()
        reader.DataOnCellsOff()
        reader.SetFileName(output_file)
        reader.Update()
        image = reader.GetOutput()

        self.assertAlmostEqual(image.GetSpacing()[0], 1.0)
        self.assertAlmostEqual(image.GetSpacing()[1], 2.0)
        self.assertAlmostEqual(image.GetSpacing()[2], 3.0)

    def test_position(self):
        '''Can run `aimod` changing position'''
        stdin = os.linesep*3 + os.linesep.join(['10.0', '11.2', '13.5']) + os.linesep*4
        input_file = os.path.join(self.test_dir, 'test25a.aim')
        output_file = os.path.join(self.test_dir, 'test.aim')
        os.sys.stdin = StringIO(stdin)
        aimod(input_file,output_file)
        self.assertTrue(os.path.isfile(output_file))

        reader = vtkbone.vtkboneAIMReader()
        reader.DataOnCellsOff()
        reader.SetFileName(output_file)
        reader.Update()
        image = reader.GetOutput()

        self.assertAlmostEqual(image.GetOrigin()[0], 10.0, places=1)
        self.assertAlmostEqual(image.GetOrigin()[1], 11.2, places=1)
        self.assertAlmostEqual(image.GetOrigin()[2], 13.5, places=1)

    def test_dimension(self):
        '''Can run `aimod` changing dimension'''
        stdin = os.linesep*6 + os.linesep.join(['2', '3', '4']) + os.linesep*1
        input_file = os.path.join(self.test_dir, 'test25a.aim')
        output_file = os.path.join(self.test_dir, 'test.aim')
        os.sys.stdin = StringIO(stdin)
        aimod(input_file,output_file)
        self.assertTrue(os.path.isfile(output_file))

        reader = vtkbone.vtkboneAIMReader()
        reader.DataOnCellsOff()
        reader.SetFileName(output_file)
        reader.Update()
        image = reader.GetOutput()

        self.assertEqual(image.GetDimensions()[0], 2)
        self.assertEqual(image.GetDimensions()[1], 3)
        self.assertEqual(image.GetDimensions()[2], 4)

if __name__ == '__main__':
    unittest.main()
