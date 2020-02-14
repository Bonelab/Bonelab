
import os
import unittest
import shutil, tempfile
import subprocess


class TestScrubVMSExtensions(unittest.TestCase):
    def setUp(self):
        # Create temporary directory to work in
        self.test_dir = tempfile.mkdtemp()

        self.input_filenames = [
            'a.txt', 'b.AIM',
            'D0001274_OBLIQUE.TIF;1',
            'RETRO_001572.AIM;1234'

        ]
        self.output_filenames = [
            'a.txt', 'b.AIM',
            'D0001274_OBLIQUE.TIF',
            'RETRO_001572.AIM'
        ]

        # Create fake files
        for filename in self.input_filenames:
            with open(os.path.join(self.test_dir, filename), 'w') as fp:
                fp.write('')

        for input_filename, output_filename in zip(self.input_filenames, self.output_filenames):
            self.assertTrue(os.path.isfile(os.path.join(self.test_dir, input_filename)))

        # Run commands
        command = ['scrub_vms_extension']
        for filename in self.input_filenames:
            command.append(os.path.join(self.test_dir, filename))
        self.output = subprocess.check_output(command).decode("utf-8")

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def test_scrub_vms_extensions_renames_files(self):
        '''scrub_vms_extensions correctly renames all files'''
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, 'a.txt')))
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, 'b.AIM')))
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, 'D0001274_OBLIQUE.TIF')))
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, 'RETRO_001572.AIM')))

        self.assertFalse(os.path.isfile(os.path.join(self.test_dir, 'D0001274_OBLIQUE.TIF;1')))
        self.assertFalse(os.path.isfile(os.path.join(self.test_dir, 'RETRO_001572.AIM;1234')))


if __name__ == '__main__':
    unittest.main()