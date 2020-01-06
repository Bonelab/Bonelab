'''Scripts for working with computed tomography data'''

__all__ = (
  '__version__',
  'version_info',
)
from pbr.version import VersionInfo

_v = VersionInfo('bonelab').semantic_version()
__version__ = _v.release_string()
version_info = _v.version_tuple()
