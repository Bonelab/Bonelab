'''
Written by Nathan Neeteson
Python / VTK Implementation of Buie's autocontour algorithm.
https://doi.org/10.1016/j.bone.2007.07.007
v0.1: (2022/04/13, Nathan Neeteson) First complete implementation
'''
import os
import vtk
import vtkbone
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import datetime
from glob import glob

from bonelab.util.aim_calibration_header import get_aim_density_equation
from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.io.vtk_helpers import get_vtk_writer, handle_filetype_writing_special_cases

def create_parser():

    parser = ArgumentParser(
        description = 'Buie\'s Autocontour Algorithm',
        formatter_class = ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'aim_dir', type=str, metavar='AIM_DIR',
        help = 'directory containing AIM images'
    )

    parser.add_argument(
        '--aim-pattern', '-ap', type=str, default='*_*_??.AIM', metavar='STR',
        help = 'file name pattern to use to find AIMs'
    )

    parser.add_argument(
        '--threshold-1', '-t1', type=float, default=450, metavar='T1',
        help = 'user input threshold 1'
    )

    parser.add_argument(
        '--threshold-2', '-t2', type=float, default=320, metavar='T1',
        help = 'user input threshold 2'
    )

    return parser

def convert_aim_to_density(img, m, b):
    mult = vtk.vtkImageMathematics()
    mult.SetOperationToMultiplyByK()
    mult.SetConstantK(m)
    mult.SetInputData(img)
    add = vtk.vtkImageMathematics()
    add.SetOperationToAddConstant()
    add.SetConstantC(b)
    add.SetInputConnection(mult.GetOutputPort())
    add.Update()
    return add.GetOutput()

def autocontour_buie(img, thresh1, thresh2):

    # constants/parameters from Buie 2007

    IN_VALUE = 127
    OUT_VALUE = 0

    S3_MEDIAN_KERNEL = [3,3,1]
    S4_DILATE_KERNEL = [15,15,1]
    S5_CONN_SCALAR_RANGE = [1,200]
    S5_CONN_SIZE_RANGE = [0,int(1E8)]
    S6_ERODE_KERNEL = [15,15,1]
    S9_DILATE_KERNEL = [10,10,1]
    S10_CONN_SCALAR_RANGE = [1,200]
    S10_CONN_SIZE_RANGE = [0,int(1E8)]
    S11_ERODE_KERNEL = [10,10,1]
    S12_GAUSSIAN_STD_DEV = 0.8
    S12_GAUSSIAN_KERNEL = [3,3,1]
    S13_THRESH = 100

    # Step 1 was just loading the AIM

    # Step 2: Threshold
    s2_threshold = vtk.vtkImageThreshold()
    s2_threshold.ThresholdByUpper(thresh1)
    s2_threshold.SetInValue(IN_VALUE)
    s2_threshold.SetOutValue(OUT_VALUE)
    s2_threshold.SetInputData(img)

    # Step 3: Median
    s3_median = vtk.vtkImageMedian3D()
    s3_median.SetKernelSize(*S3_MEDIAN_KERNEL)
    s3_median.SetInputConnection(s2_threshold.GetOutputPort())

    # Step 4: Dilate
    s4_dilate = vtk.vtkImageDilateErode3D()
    s4_dilate.SetDilateValue(IN_VALUE)
    s4_dilate.SetErodeValue(OUT_VALUE)
    s4_dilate.SetKernelSize(*S4_DILATE_KERNEL)
    s4_dilate.SetInputConnection(s3_median.GetOutputPort())

    # Step 5: Connectivity (applied to non-bone)
    # first flip 0 <-> 127
    s5a_invert = vtk.vtkImageThreshold()
    s5a_invert.ThresholdByLower(IN_VALUE/2)
    s5a_invert.SetInValue(IN_VALUE)
    s5a_invert.SetOutValue(OUT_VALUE)
    s5a_invert.SetInputConnection(s4_dilate.GetOutputPort())

    # then connectivity
    s5b_connectivity = vtk.vtkImageConnectivityFilter()
    s5b_connectivity.SetExtractionModeToLargestRegion()
    s5b_connectivity.SetScalarRange(*S5_CONN_SCALAR_RANGE)
    s5b_connectivity.SetSizeRange(*S5_CONN_SIZE_RANGE)
    s5b_connectivity.SetInputConnection(s5a_invert.GetOutputPort())

    # then flip 0 <-> 127 again
    s5c_invert = vtk.vtkImageThreshold()
    s5c_invert.ThresholdByLower(0.5)
    s5c_invert.SetInValue(IN_VALUE)
    s5c_invert.SetOutValue(OUT_VALUE)
    s5c_invert.SetInputConnection(s5b_connectivity.GetOutputPort())

    # Step 6: Erode
    s6_erode = vtk.vtkImageDilateErode3D()
    s6_erode.SetDilateValue(OUT_VALUE)
    s6_erode.SetErodeValue(IN_VALUE)
    s6_erode.SetKernelSize(*S6_ERODE_KERNEL)
    s6_erode.SetInputConnection(s5c_invert.GetOutputPort())

    # Step 7: Threshold
    s7_threshold = vtk.vtkImageThreshold()
    s7_threshold.ThresholdByLower(thresh2)
    s7_threshold.SetInValue(IN_VALUE)
    s7_threshold.SetOutValue(OUT_VALUE)
    s7_threshold.SetInputData(img)

    # Step 8: Mask
    s8a_mask = vtk.vtkImageMask()
    s8a_mask.SetInputConnection(0,s7_threshold.GetOutputPort())
    s8a_mask.SetInputConnection(1,s6_erode.GetOutputPort())

    s8b_invert = vtk.vtkImageThreshold()
    s8b_invert.ThresholdByLower(IN_VALUE/2)
    s8b_invert.SetInValue(IN_VALUE)
    s8b_invert.SetOutValue(OUT_VALUE)
    s8b_invert.SetInputConnection(s8a_mask.GetOutputPort())

    # Step 9: Dilate
    s9_dilate = vtk.vtkImageDilateErode3D()
    s9_dilate.SetDilateValue(OUT_VALUE)
    s9_dilate.SetErodeValue(IN_VALUE)
    s9_dilate.SetKernelSize(*S9_DILATE_KERNEL)
    s9_dilate.SetInputConnection(s8b_invert.GetOutputPort())

    # Step 10: Connectivity
    # connectivity
    s10a_connectivity = vtk.vtkImageConnectivityFilter()
    s10a_connectivity.SetExtractionModeToLargestRegion()
    s10a_connectivity.SetScalarRange(*S10_CONN_SCALAR_RANGE)
    s10a_connectivity.SetSizeRange(*S10_CONN_SIZE_RANGE)
    s10a_connectivity.SetInputConnection(s9_dilate.GetOutputPort())

    # then convert to 127 and 0 again
    s10b_convert = vtk.vtkImageThreshold()
    s10b_convert.ThresholdByLower(0.5)
    s10b_convert.SetInValue(OUT_VALUE)
    s10b_convert.SetOutValue(IN_VALUE)
    s10b_convert.SetInputConnection(s10a_connectivity.GetOutputPort())

    # Step 11: Erode
    s11_erode = vtk.vtkImageDilateErode3D()
    s11_erode.SetDilateValue(IN_VALUE)
    s11_erode.SetErodeValue(OUT_VALUE)
    s11_erode.SetKernelSize(*S11_ERODE_KERNEL)
    s11_erode.SetInputConnection(s10b_convert.GetOutputPort())

    # Step 12: Gaussian Smooth
    s12_gauss = vtk.vtkImageGaussianSmooth()
    s12_gauss.SetStandardDeviation(S12_GAUSSIAN_STD_DEV)
    s12_gauss.SetRadiusFactors(*S12_GAUSSIAN_KERNEL)
    s12_gauss.SetInputConnection(s11_erode.GetOutputPort())

    # Step 13: Threshold
    s13_threshold = vtk.vtkImageThreshold()
    s13_threshold.ThresholdByLower(S13_THRESH)
    s13_threshold.SetInValue(OUT_VALUE)
    s13_threshold.SetOutValue(IN_VALUE)
    s13_threshold.SetInputConnection(s12_gauss.GetOutputPort())

    # Step 14: Mask
    s14_mask = vtk.vtkImageMask()
    s14_mask.SetInputConnection(0,s6_erode.GetOutputPort())
    s14_mask.SetInputConnection(1,s13_threshold.GetOutputPort())

    # Step 15: Invert the Trabecular Mask
    s15_invert = vtk.vtkImageThreshold()
    s15_invert.ThresholdByLower(IN_VALUE/2)
    s15_invert.SetInValue(IN_VALUE)
    s15_invert.SetOutValue(OUT_VALUE)
    s15_invert.SetInputConnection(s13_threshold.GetOutputPort())

    # update the pipeline
    s14_mask.Update()
    s15_invert.Update()

    # get masks
    cort_mask = s14_mask.GetOutput()
    trab_mask = s15_invert.GetOutput()


    return cort_mask, trab_mask

def write_mask(reader,mask,mask_fn,label,software,version):

    processing_log = (
        reader.GetProcessingLog()
        + os.linesep
        + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {label} created by {software}, version {version}."
    )

    writer = get_vtk_writer(mask_fn)
    if writer is None:
        raise RuntimeError(f'Cannot find writer for file {mask_fn}')

    writer.SetFileName(mask_fn)
    writer.SetInputData(mask)
    handle_filetype_writing_special_cases(
        writer,
        processing_log=processing_log
    )

    writer.Update()

def main():

    SOFTWARE = 'Buie-Burghardt-Scanco Autocontour VTK Implemention'
    VERSION = 0.1

    args = create_parser().parse_args()
    aim_fn_list = glob(os.path.join(args.aim_dir,args.aim_pattern))

    reader = vtkbone.vtkboneAIMReader()
    reader.DataOnCellsOff()

    for aim_fn in aim_fn_list:

        print(aim_fn)

        cort_mask_fn = aim_fn.replace('.AIM','_CORT_MASK.AIM')
        trab_mask_fn = aim_fn.replace('.AIM','_TRAB_MASK.AIM')

        reader.SetFileName(aim_fn)
        reader.Update()

        img = reader.GetOutput()
        m,b = get_aim_density_equation(reader.GetProcessingLog())
        img = convert_aim_to_density(img,m,b)

        cort_mask, trab_mask = autocontour_buie(img,args.threshold_1,args.threshold_2)

        write_mask(reader,cort_mask,cort_mask_fn,'CORT_MASK',SOFTWARE,VERSION)
        write_mask(reader,trab_mask,trab_mask_fn,'TRAB_MASK',SOFTWARE,VERSION)


if __name__ == '__main__':
    main()
