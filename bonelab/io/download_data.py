'''Collection of variables defining defaults for data downloading'''

from collections import namedtuple
import os

# Default URL
BL_DATA_DEFAULT_URL = 'https://github.com/Bonelab/BonelabData.git'

# Environment variable for user defined bonelab data directory
BL_DATA_DIRECTORY_ENVIRONMENT_VARIABLE = 'BL_DATA_DIRECTORY'

# Default bonelab data directory
BL_DATA_DIRECTORY_DEFAULT = os.path.join(os.path.expanduser("~"), '.bldata')
