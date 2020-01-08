'''Test write csv functionality'''

import unittest
from bonelab.util.write_csv import write_csv
import subprocess
import shutil, tempfile, filecmp
import os
from collections import OrderedDict


class TestWriteCSV(unittest.TestCase):
    '''Test write csv functionality'''

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.csv_file_name = os.path.join(self.test_dir, 'test.csv')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_file(self):
        # Create test data
        data = OrderedDict()
        data['FileName'] = 'filename.txt'
        data['A'] = 2
        data['B'] = 'b'

        # Create the expected file
        correct_file_name = os.path.join(self.test_dir, 'test_correct.csv')
        with open(correct_file_name, 'w') as f:
            f.write('FileName,A,B' + os.linesep)
            f.write('filename.txt,2,b' + os.linesep)

        # Print result
        write_csv(data, self.csv_file_name)

        # Test
        self.assertTrue(os.path.exists(self.csv_file_name),
          'Could not create file')
        self.assertTrue(filecmp.cmp(correct_file_name, self.csv_file_name),
          'Files are not the same')

    def test_delimiter(self):
        # Create test data
        data = OrderedDict()
        data['FileName'] = 'filename.txt'
        data['A'] = 2
        data['B'] = 'b'

        # Create the expected file
        correct_file_name = os.path.join(self.test_dir, 'test_correct.csv')
        with open(correct_file_name, 'w') as f:
            f.write('FileName;A;B' + os.linesep)
            f.write('filename.txt;2;b' + os.linesep)

        # Print result
        write_csv(data, self.csv_file_name, delimiter=';')

        # Test
        self.assertTrue(os.path.exists(self.csv_file_name),
          'Could not create file')
        self.assertTrue(filecmp.cmp(correct_file_name, self.csv_file_name),
          'Files are not the same')

    def test_append_file(self):
        # Create test data
        data = OrderedDict()
        data['FileName'] = 'filename.txt'
        data['A'] = 2
        data['B'] = 'b'

        # First write
        write_csv(data, self.csv_file_name)

        self.assertTrue(os.path.exists(self.csv_file_name),
          'Could not create file')

        # Second write
        write_csv(data, self.csv_file_name)

        # Create the expected file
        correct_file_name = os.path.join(self.test_dir, 'test_correct.csv')
        with open(correct_file_name, 'w') as f:
            f.write('FileName,A,B' + os.linesep)
            f.write('filename.txt,2,b' + os.linesep)
            f.write('filename.txt,2,b' + os.linesep)

        # Test
        self.assertTrue(filecmp.cmp(correct_file_name, self.csv_file_name),
          'Files are not the same')

    def test_special_characters(self):
        # Create test data
        data = OrderedDict()
        data['Spacing.X [mm]'] = 3
        data['C^asdf'] = 'Hello'

        # Create the expected file
        correct_file_name = os.path.join(self.test_dir, 'test_correct.csv')
        with open(correct_file_name, 'w') as f:
            f.write('Spacing.X [mm],C^asdf' + os.linesep)
            f.write('3,Hello' + os.linesep)

        # Print result
        write_csv(data, self.csv_file_name)

        # Test
        self.assertTrue(os.path.exists(self.csv_file_name),
          'Could not create file')
        self.assertTrue(filecmp.cmp(correct_file_name, self.csv_file_name),
          'Files are not the same')

if __name__ == '__main__':
    unittest.main()
