'''
Written by Nathan Neeteson
Python / VTK Implementation of Buie's autocontour algorithm.
https://doi.org/10.1016/j.bone.2007.07.007
v0.1: (2022/04/13, Nathan Neeteson) First complete implementation
v0.2: (2022/04/14, Nathan Neeteson) Expose all relevant parameters in the CLI
'''
import os
import vtk
import vtkbone
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentTypeError
from datetime import datetime
from glob import glob

from bonelab.util.aim_calibration_header import get_aim_density_equation
from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.io.vtk_helpers import get_vtk_writer, handle_filetype_writing_special_cases

def positive_int(n):
    n = int(n)
    if n < 0:
        raise ArgumentTypeError('this argument only takes positive integers')
    return n

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

    parser.add_argument(
        '--in-value', '-iv', type=positive_int, default=127, metavar='IV',
        help = 'value to use for voxels in a binary mask'
    )

    parser.add_argument(
        '--out-value', '-ov', type=positive_int, default=0, metavar='IV',
        help = 'value to use for voxels not in a binary mask'
    )

    parser.add_argument(
        '--step-3-median-kernel', '-s3mk', type=positive_int, nargs=3,
        default=[3,3,1], metavar='N',
        help = 'kernel for median filter in step 3: if given, must be 3 ints'
    )

    parser.add_argument(
        '--step-4-and-6-dilate-erode-kernel', '-s46dek', type=positive_int, nargs=3,
        default=[15,15,1], metavar='N',
        help = 'kernel for dilate and erode filter in steps 4 and 6: if given, must be 3 ints'
    )

    parser.add_argument(
        '--step-9-and-11-dilate-erode-kernel', '-s911dek', type=positive_int, nargs=3,
        default=[10,10,1], metavar='N',
        help = 'kernel for dilate and erode filter in steps 4 and 6: if given, must be 3 ints'
    )

    parser.add_argument(
        '--step-12-gaussian-std', '-s12gs', type=float, default=0.8, metavar='N',
        help = 'gaussian filter standard deviation for step 12'
    )

    parser.add_argument(
        '--step-12-gaussian-kernel', '-s12gk', type=positive_int, nargs=3,
        default=[3,3,1], metavar='N',
        help = 'kernel for gaussian filter in step 12: if given, must be 3 ints'
    )

    parser.add_argument(
        '--step-13-threshold', '-s13t', type=float, default=100, metavar='N',
        help = 'threshold for rebinarizing after gaussian in step 13'
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

def autocontour_buie(img, args):

    # these hard-coded constants just make sure that the connectivity filter
    # actually works, they don't need to be configuable in my opinion
    CONN_SCALAR_RANGE = [1,args.in_value+1]
    CONN_SIZE_RANGE = [0,int(1E10)]

    # Step 1 was just loading the AIM

    # Step 2: Threshold
    s2_threshold = vtk.vtkImageThreshold()
    s2_threshold.ThresholdByUpper(args.threshold_1)
    s2_threshold.SetInValue(args.in_value)
    s2_threshold.SetOutValue(args.out_value)
    s2_threshold.SetInputData(img)

    # Step 3: Median
    s3_median = vtk.vtkImageMedian3D()
    s3_median.SetKernelSize(*args.step_3_median_kernel)
    s3_median.SetInputConnection(s2_threshold.GetOutputPort())

    # Step 4: Dilate
    s4_dilate = vtk.vtkImageDilateErode3D()
    s4_dilate.SetDilateValue(args.in_value)
    s4_dilate.SetErodeValue(args.out_value)
    s4_dilate.SetKernelSize(*args.step_4_and_6_dilate_erode_kernel)
    s4_dilate.SetInputConnection(s3_median.GetOutputPort())

    # Step 5: Connectivity (applied to non-bone)
    # first flip 0 <-> 127
    s5a_invert = vtk.vtkImageThreshold()
    s5a_invert.ThresholdByLower(args.in_value/2)
    s5a_invert.SetInValue(args.in_value)
    s5a_invert.SetOutValue(args.out_value)
    s5a_invert.SetInputConnection(s4_dilate.GetOutputPort())

    # then connectivity
    s5b_connectivity = vtk.vtkImageConnectivityFilter()
    s5b_connectivity.SetExtractionModeToLargestRegion()
    s5b_connectivity.SetScalarRange(*CONN_SCALAR_RANGE)
    s5b_connectivity.SetSizeRange(*CONN_SIZE_RANGE)
    s5b_connectivity.SetInputConnection(s5a_invert.GetOutputPort())

    # then flip 0 <-> 127 again
    s5c_invert = vtk.vtkImageThreshold()
    s5c_invert.ThresholdByLower(0.5)
    s5c_invert.SetInValue(args.in_value)
    s5c_invert.SetOutValue(args.out_value)
    s5c_invert.SetInputConnection(s5b_connectivity.GetOutputPort())

    # Step 6: Erode
    s6_erode = vtk.vtkImageDilateErode3D()
    s6_erode.SetDilateValue(args.out_value)
    s6_erode.SetErodeValue(args.in_value)
    s6_erode.SetKernelSize(*args.step_4_and_6_dilate_erode_kernel)
    s6_erode.SetInputConnection(s5c_invert.GetOutputPort())

    # Step 7: Threshold
    s7_threshold = vtk.vtkImageThreshold()
    s7_threshold.ThresholdByLower(args.threshold_2)
    s7_threshold.SetInValue(args.in_value)
    s7_threshold.SetOutValue(args.out_value)
    s7_threshold.SetInputData(img)

    # Step 8: Mask
    s8a_mask = vtk.vtkImageMask()
    s8a_mask.SetInputConnection(0,s7_threshold.GetOutputPort())
    s8a_mask.SetInputConnection(1,s6_erode.GetOutputPort())

    s8b_invert = vtk.vtkImageThreshold()
    s8b_invert.ThresholdByLower(args.in_value/2)
    s8b_invert.SetInValue(args.in_value)
    s8b_invert.SetOutValue(args.out_value)
    s8b_invert.SetInputConnection(s8a_mask.GetOutputPort())

    # Step 9: Dilate
    s9_dilate = vtk.vtkImageDilateErode3D()
    s9_dilate.SetDilateValue(args.out_value)
    s9_dilate.SetErodeValue(args.in_value)
    s9_dilate.SetKernelSize(*args.step_9_and_11_dilate_erode_kernel)
    s9_dilate.SetInputConnection(s8b_invert.GetOutputPort())

    # Step 10: Connectivity
    # connectivity
    s10a_connectivity = vtk.vtkImageConnectivityFilter()
    s10a_connectivity.SetExtractionModeToLargestRegion()
    s10a_connectivity.SetScalarRange(*CONN_SCALAR_RANGE)
    s10a_connectivity.SetSizeRange(*CONN_SIZE_RANGE)
    s10a_connectivity.SetInputConnection(s9_dilate.GetOutputPort())

    # then convert to 127 and 0 again
    s10b_convert = vtk.vtkImageThreshold()
    s10b_convert.ThresholdByLower(0.5)
    s10b_convert.SetInValue(args.out_value)
    s10b_convert.SetOutValue(args.in_value)
    s10b_convert.SetInputConnection(s10a_connectivity.GetOutputPort())

    # Step 11: Erode
    s11_erode = vtk.vtkImageDilateErode3D()
    s11_erode.SetDilateValue(args.in_value)
    s11_erode.SetErodeValue(args.out_value)
    s11_erode.SetKernelSize(*args.step_9_and_11_dilate_erode_kernel)
    s11_erode.SetInputConnection(s10b_convert.GetOutputPort())

    # Step 12: Gaussian Smooth
    s12_gauss = vtk.vtkImageGaussianSmooth()
    s12_gauss.SetStandardDeviation(args.step_12_gaussian_std)
    s12_gauss.SetRadiusFactors(*args.step_12_gaussian_kernel)
    s12_gauss.SetInputConnection(s11_erode.GetOutputPort())

    # Step 13: Threshold
    s13_threshold = vtk.vtkImageThreshold()
    s13_threshold.ThresholdByLower(args.step_13_threshold)
    s13_threshold.SetInValue(args.out_value)
    s13_threshold.SetOutValue(args.in_value)
    s13_threshold.SetInputConnection(s12_gauss.GetOutputPort())

    # Step 14: Mask
    s14_mask = vtk.vtkImageMask()
    s14_mask.SetInputConnection(0,s6_erode.GetOutputPort())
    s14_mask.SetInputConnection(1,s13_threshold.GetOutputPort())

    # Step 15: Invert the Trabecular Mask
    s15_invert = vtk.vtkImageThreshold()
    s15_invert.ThresholdByLower(args.in_value/2)
    s15_invert.SetInValue(args.in_value)
    s15_invert.SetOutValue(args.out_value)
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
    VERSION = 0.2

    args = create_parser().parse_args()

    if args.out_value >= args.in_value:
        raise ValueError('please make `in-value` larger than `out-value`')

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

        cort_mask, trab_mask = autocontour_buie(img,args)

        write_mask(reader,cort_mask,cort_mask_fn,'CORT_MASK',SOFTWARE,VERSION)
        write_mask(reader,trab_mask,trab_mask_fn,'TRAB_MASK',SOFTWARE,VERSION)


if __name__ == '__main__':
    main()
