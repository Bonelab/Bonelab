'''Utility functions for working with vtk'''
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy

def numpy_to_vtkImageData(array, spacing=None, origin=None, array_type=vtk.VTK_FLOAT):
    '''Convert numpy array to vtkImageData

    Default spacing is 1 and default origin is 0.

    Args:
        array (np.ndarray):     Image to be read in
        spacing (np.ndarray):   Image spacing
        origin (np.ndarray):    Image orign
        array_type (int):       Datatype from vtk

    Returns:
        vtkImageReader:         The corresponding vtkImageReader or None
                                if one cannot be found.
    '''
    # Set default values
    if spacing is None: spacing = np.ones_like(array.shape)
    if origin is None: origin = np.zeros_like(array.shape)

    # Convert
    temp = np.ascontiguousarray(np.atleast_3d(array))
    image = vtk.vtkImageData()
    vtkArray = numpy_to_vtk(
        temp.ravel(order='F'),
        deep=True, array_type=array_type
    )
    image.SetDimensions(array.shape)
    image.SetSpacing(spacing)
    image.SetOrigin(origin)
    image.GetPointData().SetScalars(vtkArray)

    return image

def vtkImageData_to_numpy(image):
    '''Convert numpy array to vtkImageData

    Args:
        image (vtkImageReader):  Input data

    Returns:
        np.ndarray:              Image converted to array
    '''
    array = vtk_to_numpy(image.GetPointData().GetScalars())
    array = array.reshape(image. GetDimensions(), order='F')
    return array
