
# Imports
import sys
import os
import errno
import time
import argparse
import numpy as np
import pydicom
import SimpleITK as sitk
import glob
#from pydicom.filereader import read_dicomdir

#from pydicom.filereader import read_dicomdir
#from os.path import dirname, join
#from pprint import pprint

from bonelab.util.echo_arguments import echo_arguments

def examine_sitk(img,msg):
    """Print basic statistics on slice.
    """
    print('!--- {0:s}'.format(msg))
    print('!-------------------------------------------------------------------------')
    print('!>')
    print('!> dim                            {: >6}  {: >6}  {: >6}'.format(*img.GetSize()))
    print('!> off                                 x       x       x')
    print('!> pos                            {:.2f}  {:.2f}  {:.2f}'.format(*img.GetOrigin()))
    print('!> element size in mm             {:.4f}  {:.4f}  {:.4f}'.format(*img.GetSpacing()))
    print('!> phys dim in mm                 {:.4f}  {:.4f}  {:.4f}'.format(img.GetSize()[0]*img.GetSpacing()[0],
                                                                            img.GetSize()[1]*img.GetSpacing()[1],
                                                                            img.GetSize()[2]*img.GetSpacing()[2]))
    print('!>')
    #print('!> Type of data               {}'.format(img.GetScalarTypeAsString()))
    #print('!> Total memory size          {:.1f} {: <10}'.format(size, names[i]))
    print('!-------------------------------------------------------------------------')

def examine_numpy(data,msg):
    """Print basic statistics on slice.
    """
    dimension = ('2D', '3D')[data.ndim == 3]
    print('!-------------------------------------------------------------------------')
    print('{0}'.format(msg))
    print('{0:>30s} {1}'.format("Type",data.dtype))
    print('{0:>30s} {1}'.format("Size in bytes",sys.getsizeof(data)))
    print('{0:>30s} {1}'.format("Dimension",dimension))
    if (data.ndim == 3):
      print('{0:>30s} {1} x {2} x {3}'.format("Voxels",data.shape[0],data.shape[1],data.shape[2]))
    else:
      print('{0:>30s} {1} x {2}'.format("Voxels",data.shape[0],data.shape[1]))      
    print('{0:>30s} {1:12.2f}'.format("Min",np.min(data)))
    print('{0:>30s} {1:12.2f}'.format("Max",np.max(data)))
    print('{0:>30s} {1:12.2f}'.format("Mean",np.mean(data)))
    print('{0:>30s} {1:12.2f}'.format("Median",np.median(data)))
    print('!-------------------------------------------------------------------------')

def message(msg, *additionalLines):
    """Print message with time stamp.
    
    The first argument is printed with a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    """
    print(f'{(time.time()-start_time):8.2f} {msg}')
    for line in additionalLines:
        print(" " * 9 + line)
start_time = time.time()

def PseudoCT(input_directory, output_directory, expression, overwrite=False, verbose=False):
    # Python 2/3 compatible input
    from six.moves import input

    # Check if output directory exists and should overwrite
    if os.path.isdir(output_directory) and not overwrite:
        result = input('Directory \"{}\" already exists. Overwrite? [y/n]: '.format(output_directory))
        if result.lower() not in ['y', 'yes']:
            message('Not overwriting. Exiting...')
            os.sys.exit()

    # Create the directory
    message("Create the output DICOM directory.")
    if (output_directory[len(output_directory)-1] != '/'):  # Ends with slash?
      output_directory = output_directory + '/'
    if not os.path.exists(os.path.dirname(output_directory)):
        try:
            os.makedirs(os.path.dirname(output_directory))
            message ("Output directory created.")
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    
    # First, we assume it is a DICOM series. If GDCM finds no DICOM files we assume it is otherwise
    is_dicom = True
    sitk.ProcessObject.GlobalWarningDisplayOff()
    filenames = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(input_directory)
    sitk.ProcessObject.GlobalWarningDisplayOn()
    filenames = [x for x in filenames]

    if len(filenames)==0:
        is_dicom = False
        filenames = glob.glob(os.path.join(input_directory, expression))
        filenames.sort()

    message('Found {} slices.'.format(len(filenames)))

    if len(filenames) < 0:
        os.sys.exit('Found no files')

    # Print to screen the filenames
    if verbose:
        dotdotdot=True
        idx=0
        for fname in filenames:
          if (idx<10 or idx>(len(filenames))-10):
            print('{0:3d}: {1:s}'.format(idx,fname))
          else:
            if (dotdotdot):
              print('...')
              dotdotdot=False
          idx += 1
        print('')

    message('Reading in {} slices.'.format(len(filenames)))
    image = sitk.ReadImage(filenames)

    data_array = sitk.GetArrayFromImage( image ) # Convert from SimpleITK to numpy
    if verbose:
        examine_numpy( data_array, "data_array")
        examine_sitk( image ,"image")

    # Create a mask with a simple threshold. We select 0 to 10 as 'background'
    lt = 0
    ut = 1
    message('Creating a mask using {0} to {1} as range.'.format(lt,ut))
    
    MaskFilter = sitk.BinaryThresholdImageFilter()
    MaskFilter.SetLowerThreshold( lt )
    MaskFilter.SetUpperThreshold( ut )
    MaskFilter.SetInsideValue( 0 )
    MaskFilter.SetOutsideValue( 1 )
    mask_img_rough = MaskFilter.Execute( image )

    kernelRadius = 1
    message('Morphological closing function on mask (radius = {0:d}).'.format(kernelRadius))
    
    CloseFilter =	sitk.BinaryMorphologicalClosingImageFilter()
    CloseFilter.SetForegroundValue( 1 )
    CloseFilter.SetKernelRadius( kernelRadius )
    mask_img = CloseFilter.Execute( mask_img_rough )
            
    mask_array = sitk.GetArrayFromImage( mask_img ) # Convert from SimpleITK to numpy
    mask_array = mask_array.astype(dtype=np.uint16) # Cast results to uint16
    
    if verbose:
        examine_numpy( mask_array, "mask_array")
        examine_sitk( mask_img ,"mask_img")

    #  Perform inverted log procedure    
    message("Calculating inverted log.")
    img_min = np.min(data_array)
    img_max = np.max(data_array)
    img_range = (img_max - img_min).astype(dtype=np.float32)
    message('{0}: {1} to {2} ({3}).'.format("Input image data range",img_min,img_max,img_range))
    
    if (np.min(data_array) < 0):
      message('ERROR: Input data array cannot contain negative values.')
      exit(1)
      
    # Log
    data_log = np.log(data_array+1)
    data_log_min = np.min(data_log)
    data_log_max = np.max(data_log)
    data_log_range = data_log_max - data_log_min
  
    # Invert
    data_inv = -(img_range/data_log_range) * ((data_log - data_log_max))
    data_array = data_inv.astype(dtype=np.uint16) # Cast results to uint16
    message("Finished calculating inverted log.")
    
    # Mask
    message("Apply mask.")
    img = sitk.GetImageFromArray( data_array ) # Convert numpy to SimpleITK
    mask = sitk.GetImageFromArray( mask_array ) # Convert numpy to SimpleITK
  
    mask_filter = sitk.MaskImageFilter()
    mask_filter.SetMaskingValue(0)
    masked_img = mask_filter.Execute(img,mask)
  
    data_array = sitk.GetArrayFromImage( masked_img ) # Convert from SimpleITK to numpy
    data_array = data_array.astype(dtype=np.uint16) # Cast results to uint16
    
    # Write
    message("Writing output DICOM slices.")

    study_instance_uid = pydicom.uid.generate_uid()
    series_instance_uid = pydicom.uid.generate_uid()
    window_center = np.mean(data_array) # (np.max(data_array)-np.min(data_array))/2.0
    window_width = (np.max(data_array)-np.min(data_array))*0.75
    #message("Created new Study Instance UID:","{}".format(study_instance_uid))
    #message("Created new Series Instance UID:","{}".format(series_instance_uid))
    
    PrintSample = 0
    idx=0
    for fname in filenames:
      ds = pydicom.dcmread(fname,force=True)
      if ds.file_meta.TransferSyntaxUID.is_compressed is True:
        ds.decompress()
      
      # Update meta data in dicom slice
      ds.StudyInstanceUID = study_instance_uid
      ds.SeriesInstanceUID = series_instance_uid
      ds.PatientID = ds.PatientID + ' pseudoCT'
      ds.PatientName = str(ds.PatientName) + " pseudoCT"
      ds.WindowCenter = window_center
      ds.WindowWidth = window_width
      
      #ds.PatientName = patient_name
      #ds.PatientID = patient_id

      if (verbose and PrintSample<10):
        print('--- {0:s} ---'.format(fname))
        print('    StudyInstanceUID:  {0:s}'.format(ds.StudyInstanceUID))
        print('    SeriesInstanceUID: {0:s}'.format(ds.SeriesInstanceUID))
        print('    PatientName:       {0}'.format(ds.PatientName))
        print('    PatientID:         {0:s}'.format(ds.PatientID))
        print('    Window Center:         {0:12.4f}'.format(ds.WindowCenter))
        print('    Window Width:         {0:12.4f}'.format(ds.WindowWidth))
        #print(ds)
        PrintSample += 1

      ds.PixelData = (data_array[idx,:,:]).tobytes()
      idx += 1
      
      dcm_fn_output = os.path.join(output_directory,os.path.split(fname)[1])

      pydicom.dcmwrite(dcm_fn_output,ds,True)
      del ds
        
    message("Finished.")

def main():
    # Setup description
    description='''Convert a series of 2D images to one 3D image

Example usage:

    blPseudoCT ZTE_DATASET/1700-PUZTE_FA_1_NEX2_1.3mm 1700-PUZTE_FA_1_NEX2_1.3mm_CT
    
    blPseudoCT /Volumes/ZTE_Study/1700-PUZTE_FA_1_NEX2_1.3mm/ /Volumes/ZTE_Study/1700-PUZTE_FA_1_NEX2_1.3mm_CT/
    blPseudoCT /Volumes/ZTE_Study/1100-PUZTE_FA_1_NEX2_1.3mm/ /Volumes/ZTE_Study/1100-PUZTE_FA_1_NEX2_1.3mm_CT/
    blPseudoCT /Volumes/ZTE_Study/700-PUZTE_FA_1_NEX2_1.3mm/ /Volumes/ZTE_Study/700-PUZTE_FA_1_NEX2_1.3mm_CT/
    blPseudoCT /Volumes/ZTE_Study/400-PUZTE_FA_1_NEX2_1.3mm/ /Volumes/ZTE_Study/400-PUZTE_FA_1_NEX2_1.3mm_CT/

There are a great deal of details in the DICOM standard and not
all are handled by this function. If you experience problematic outputs,
please consult a commercial DICOM importer.

Stacking of slices will be determined by GDCM if the input is a DICOM
series, otherwise an alpha-numeric sort.

The output will be a DICOM file.
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blPseudoCT",
        description=description
    )
    parser.add_argument('input_directory', help='Input DICOM series directory')
    parser.add_argument('output_directory', help='Output DICOM series directory')
    parser.add_argument( '-e', '--expression', default='*', type=str,
                        help='An expression for matching files (default: %(default)s)')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('PseudoCT', vars(args)))

    # Run program
    PseudoCT(**vars(args))

if __name__ == '__main__':
    main()
