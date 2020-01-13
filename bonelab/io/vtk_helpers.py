'''Helper functions for VTK Input/Output'''

import vtk
import vtkbone
import os

def get_vtk_reader(filename):
    '''Get the appropriate vtkImageReader given the filename

    This function utilizes the factory method classes in VTK with
    some added functionality for working with the AIM, nifti, and
    dicom readers.

    Args:
        filename (string):      Image to be read in

    Returns:
        vtkImageReader:         The corresponding vtkImageReader or None
                                if one cannot be found.
    '''
    # Try factory method
    reader = vtk.vtkImageReader2Factory.CreateImageReader2(filename)

    # If it doesn't work, try specific cases
    if reader is None:
        if filename.lower().endswith('.aim'):
            reader = vtkbone.vtkboneAIMReader()
            reader.DataOnCellsOff()
        elif filename.lower().endswith('.nii'):
            reader = vtk.vtkNIFTIImageReader()
        elif filename.lower().endswith('.nii.gz'):
            reader = vtk.vtkNIFTIImageReader()
        elif filename.lower().endswith('.dcm'):
            reader = vtk.vtkDICOMImageReader()

    return reader

def get_vtk_writer(filename):
    '''Get the appropriate vtkImageWriter given the filename
    
    Args:
        filename (string):      Image to be read out

    Returns:
        vtkImageReader:         The corresponding vtkImageWriter or None
                                if one cannot be found.
    '''
    # Map from ending to writer
    writer_map = {
        'aim':      vtkbone.vtkboneAIMWriter,
        'nii':      vtk.vtkNIFTIImageWriter,
        'mha':      vtk.vtkMetaImageWriter,
        'mnc':      vtk.vtkMINCImageWriter,
        'bmp':      vtk.vtkBMPWriter,
        'jpeg':     vtk.vtkJPEGWriter,
        'png':      vtk.vtkPNGWriter,
        'tiff':     vtk.vtkTIFFWriter
    }
    writer_map['nii.gz'] = writer_map['nii']
    writer_map['jpg'] = writer_map['jpeg']
    writer_map['tif'] = writer_map['tiff']
    writer_map['mhd'] = writer_map['mha']

    for ending, writer in writer_map.items():
        if filename.lower().endswith(ending):
            return writer()
    return None

def handle_filetype_writing_special_cases(writer, **kwargs):
    '''Handle intermediate steps for writing filetype

    Calls the associated function for each writer type to try
    and handle the output. These may add filters before the
    writer such as casting. It is recommended to set the writer
    input data or input connection before calling this function.

    If no special cases are known for a writer type, nothing
    is done.

    In general, it is recommended to call this on your vtkImageWriter
    class just before calling update to avoid common data typing errors.
    
    Args:
        writer (vtk.vtkImageWriter):    The file writer
        kwargs (dict):                  Dictionary of args passed to subsequent functions

    Returns:
        None
    '''
    step_map = {
        type(vtkbone.vtkboneAIMWriter()):   handle_aim_writing_special_cases,
        type(vtk.vtkTIFFWriter()):          handle_tiff_writing_special_cases,
        type(vtk.vtkPNGWriter()):           handle_png_writing_special_cases,
        type(vtk.vtkBMPWriter()):           handle_bmp_writing_special_cases
    }

    if type(writer) in step_map:
        return step_map[type(writer)](writer, **kwargs)
    return None

def handle_supported_types(writer, typelist, output_type=vtk.VTK_FLOAT):
    '''Cast to float if input data is not correct type'''
    # Determine input scalar type
    input_algorithm = writer.GetInputAlgorithm()
    # Input set with SetInputData?
    if type(input_algorithm) == type(vtk.vtkTrivialProducer()):
        scalar_type = writer.GetInput().GetScalarType()
    # Input set with SetInputConnection
    else:
        input_algorithm.Update()
        scalar_type = input_algorithm.GetOutput().GetScalarType()

    # Cast if not appropriate
    if scalar_type not in typelist:
        # If we can cast to float, just cast to float
        if output_type != output_type:
            pass
        else:
            caster = vtk.vtkImageCast()
            caster.SetInputConnection(input_algorithm.GetOutputPort())
            caster.SetOutputScalarType(output_type)

        writer.SetInputConnection(caster.GetOutputPort())

def handle_aim_writing_special_cases(writer, processing_log='', output_type=vtk.VTK_FLOAT, **kwargs):
    '''Specific handling of AIM data writting
    
    This includes functionality to:
        - Set processing log
        - Convert to supported types

    Args:
        writer (vtkbone.vtkboneAIMWriter):  The file writer
        processing_log (string):            An optional processing log
        kwargs (dict):                      Dictionary of args used for 

    Returns:
        Nothing
    '''
    # Handle setting processing log
    if len(processing_log) > 0:
        writer.SetProcessingLog(processing_log)

    # Handle supported types
    handle_supported_types(
        writer,
        [vtk.VTK_CHAR, vtk.VTK_SHORT, vtk.VTK_FLOAT],
        output_type
    )

def handle_tiff_writing_special_cases(writer, output_type=vtk.VTK_FLOAT, **kwargs):
    '''Specific handling of tiff data writting
    
    This includes functionality to:
        - Convert to supported types

    Args:
        writer (vtk.vtkTIFFWriter):     The file writer
        kwargs (dict):                  Dictionary of args used for 

    Returns:
        Nothing
    '''
    # Handle supported types
    handle_supported_types(
        writer,
        [vtk.VTK_UNSIGNED_CHAR, vtk.VTK_UNSIGNED_SHORT, vtk.VTK_FLOAT],
        output_type
    )

def handle_png_writing_special_cases(writer, output_type=vtk.VTK_FLOAT, **kwargs):
    '''Specific handling of png data writting
    
    This includes functionality to:
        - Convert to supported types

    Args:
        writer (vtk.vtkPNGWriter):      The file writer
        kwargs (dict):                  Dictionary of args used for 

    Returns:
        Nothing
    '''
    # Handle supported types
    handle_supported_types(
        writer,
        [vtk.VTK_UNSIGNED_CHAR, vtk.VTK_UNSIGNED_SHORT, vtk.VTK_FLOAT],
        output_type
    )

def handle_bmp_writing_special_cases(writer, output_type=vtk.VTK_FLOAT, **kwargs):
    '''Specific handling of bmp data writting
    
    This includes functionality to:
        - Convert to supported types

    Args:
        writer (vtk.vtkBMPWriter):      The file writer
        kwargs (dict):                  Dictionary of args used for 

    Returns:
        Nothing
    '''
    # Handle supported types
    handle_supported_types(
        writer,
        [vtk.VTK_UNSIGNED_CHAR, vtk.VTK_UNSIGNED_SHORT, vtk.VTK_FLOAT],
        output_type
    )
