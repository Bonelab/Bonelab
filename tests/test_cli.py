'''Test command line interface'''

import unittest
import subprocess


class TestCommandLineInterfece(unittest.TestCase):
    '''Test command line interface'''

    def run_command(self, command):
        try:
            subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            return False
        except OSError as e:
            return False
        return True

    def runner(self, entry_point):
        command = [entry_point, '-h']
        self.assertTrue(
            self.run_command(command),
            'Could not run command \"{}\"'.format(' '.join(command))
        )

    def test_blDownloadData(self):
        '''Can run `blDownloadData`'''
        self.runner('blDownloadData')


if __name__ == '__main__':
    unittest.main()
