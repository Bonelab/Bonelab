
# Imports
import argparse
import os
import vtk
import SimpleITK as sitk
import vtkbone
import copy
import numpy as np
from collections import OrderedDict

from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.aim_calibration_header import get_aim_density_equation
from bonelab.util.write_csv import write_csv
from .ImageConverter import ImageConverter


def segment_bone(image, threshold):
    soft_tissue = image<threshold
    largest = sitk.RelabelComponent(sitk.ConnectedComponent(soft_tissue))==1
    return 1-largest

def Muscle(input_filename, converted_filename, csv_filename, tiff_filename, segmentation_filename, bone_threshold, smoothing_iterations, segmentation_iterations, segmentation_multiplier, initial_neighborhood_radius, closing_radius):
    # Python 2/3 compatible input
    from six.moves import input

    # Input must be an AIM
    if not input_filename.lower().endswith('.aim'):
        os.sys.exit('[ERROR] Input \"{}\" must be an AIM'.format(input_filename))

    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    # Internal constants
    bone_label = 1
    muscle_label = 2

    # Compute calibration constants
    print('Computing calibration constants')
    reader = vtkbone.vtkboneAIMReader()
    reader.SetFileName(input_filename)
    reader.DataOnCellsOff()
    reader.Update()
    m,b = get_aim_density_equation(reader.GetProcessingLog())
    del reader
    print('  m: {}'.format(m))
    print('  b: {}'.format(b))
    print('')

    # Converting image
    print('Converting {} to {}'.format(input_filename, converted_filename))
    ImageConverter(input_filename, converted_filename, overwrite=True)
    print('')

    print('Reading in converted image')
    image = sitk.ReadImage(converted_filename)

    # Segment bone
    print('Segmenting bone')
    seg_bone = segment_bone(image, (bone_threshold - b)/m)
    seg_bone = (seg_bone>0)*bone_label
    print('')

    # Find centroid
    print('Finding centroid of the two largest bones')
    stat_filter = sitk.LabelShapeStatisticsImageFilter()
    stat_filter.Execute(sitk.RelabelComponent(sitk.ConnectedComponent(seg_bone)))
    centroids = [
        stat_filter.GetCentroid(1),
        stat_filter.GetCentroid(2)
    ]
    seed = [0 for i in range(len(centroids[0]))]
    for i in range(len(seed)):
        seed[i] = 0.5*(centroids[0][i] + centroids[1][i])
    seed_index = image.TransformPhysicalPointToIndex(seed)
    print('  Centroid1:       {}'.format(centroids[0]))
    print('  Centroid2:       {}'.format(centroids[1]))
    print('  Seed (physical): {}'.format(seed))
    print('  Seed (index):    {}'.format(seed_index))
    print('')

    # Smooth image
    print('Performing anisotropic smoothing')
    timeStep = image.GetSpacing()[0] / 2.0**4
    smooth_image = sitk.GradientAnisotropicDiffusion(
        sitk.Cast(image, sitk.sitkFloat32),
        timeStep=timeStep,
        numberOfIterations=smoothing_iterations
    )
    sitk.WriteImage(smooth_image, 'aniso.nii')
    print('')

    # Segment muscle
    print('Segmenting muscle')
    seg_muscle = sitk.ConfidenceConnected(
        smooth_image,
        seedList=[seed_index],
        numberOfIterations=segmentation_iterations,
        multiplier=segmentation_multiplier,
        initialNeighborhoodRadius=initial_neighborhood_radius,
        replaceValue=1
    )

    # Take largest component
    seg_muscle = (sitk.RelabelComponent(sitk.ConnectedComponent(seg_muscle>0))==1)*muscle_label
    print('')

    # One, solid peice of background
    print('Cleaning up segmentation')
    vector_radius = [int(max(1, closing_radius//s)) for s in image.GetSpacing()]
    print('  Closing radius [mm]:    {}'.format(closing_radius))
    print('  Vector radius [voxels]: {}'.format(vector_radius))
    seg = (seg_bone+seg_muscle)>0
    seg = sitk.BinaryDilate(seg, vector_radius)
    background = sitk.RelabelComponent(sitk.ConnectedComponent(seg<1))==1
    seg_muscle = sitk.BinaryErode(background<1, vector_radius)*muscle_label
    print('')

    # Join segmentation
    seg_muscle = sitk.Mask(seg_muscle, 1-(seg_bone>0))
    seg = seg_bone + seg_muscle

    # Write segmentation
    print('Writing segmentation to ' + segmentation_filename)
    sitk.WriteImage(seg, segmentation_filename)
    print('')

    print('Performing quantification')
    # Quantify Density
    intensity_filter = sitk.LabelIntensityStatisticsImageFilter()
    intensity_filter.Execute(seg, image)
    muscle_density = intensity_filter.GetMean(muscle_label)

    # Quantify cross sectional area
    # Note that since 
    stat_filter = sitk.LabelShapeStatisticsImageFilter()
    stat_filter.Execute(seg)
    ave_cross_area = stat_filter.GetNumberOfPixels(muscle_label) / seg.GetSize()[2]

    print('  density:       {}'.format(muscle_density))
    print('  cross section: {}'.format(ave_cross_area))
    print('')

    # Write results
    entry = OrderedDict()
    entry['Filename'] = input_filename
    entry['Spacing.X [mm]'] = image.GetSpacing()[0]
    entry['Spacing.Y [mm]'] = image.GetSpacing()[1]
    entry['Spacing.Z [mm]'] = image.GetSpacing()[2]
    entry['density_slope'] = m
    entry['density_intercept'] = b
    entry['muscle density [native]'] = muscle_density
    entry['A.Cross [vox^2]'] = ave_cross_area
    print(echo_arguments('Muscle Outcomes:', entry))

    # Write CSV
    if len(csv_filename)>0:
        print('  Writing to csv file ' + csv_filename)
        write_csv(entry, csv_filename)

    # Write TIFF
    if len(tiff_filename)>0:
        overlay = sitk.LabelOverlay(
            sitk.Cast(sitk.IntensityWindowing(
                sitk.Cast(image, sitk.sitkFloat32),
                windowMinimum = 0,
                windowMaximum = (bone_threshold - b)/m,
                outputMinimum = 0.0,
                outputMaximum = 255.0
            ), sitk.sitkUInt8),
            seg,
            opacity=0.3
        )

        size = list(overlay.GetSize())
        index = [0, 0, int(size[2]//2)]
        size[2]=0

        #Step 5: Extract that specific slice using the Extract Image Filter
        tiff_image = sitk.Extract(
            overlay,
            size=size,
            index=index
        )

        print('  Save single slice to ' + tiff_filename)
        sitk.WriteImage(tiff_image, tiff_filename)

def main():
    # Setup description
    description='''Muscle segmentation and quantification

It is assumed that the voxel coordinate z-axis corresponds to the
proximal-distal direction in the image. If strange cross sectional
areas are being found, check the `converted_filename` image
orientation in itksnap.

It is assumed the image is tightly cropped to the bone in the z-axes.
This would affect the cross sectional area calculation by adding zero
values before averaging.

Finally, it is assumed that the image voxels are isotropic.

Output TIFFs have been window/leveled to have display range (0, `bone_threshold`).

To compute the real density and cross sectional area, use the following formulas:
    density = density_slope * 'muscle density [native]' + density_intercept
    Cross.A = 'Spacing.X [mm]' * 'Spacing.Y [mm]' * 'A.Cross [vox^2]'
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blMuscle",
        description=description
    )
    parser.add_argument('input_filename', help='Input image')
    parser.add_argument('converted_filename', help='Output converted image (typically .nii)')
    parser.add_argument('segmentation_filename', help='Input image (typically .nii)')
    parser.add_argument('--csv_filename',
                        default='', type=str,
                        help='Write results to CSV file (empty string causes no write)')
    parser.add_argument('--tiff_filename',
                        default='', type=str,
                        help='Write one slice to a TIFF image (empty string causes no write)')
    parser.add_argument('--bone_threshold',
                        default=800.0, type=float,
                        help='Threshold for selecting bone (default: %(default)s mg HA/cc)')
    parser.add_argument('--smoothing_iterations',
                        default=10, type=int,
                        help='Number of iterations of Perona-Malik anisotropic filtering (default: %(default)s)')
    parser.add_argument('--segmentation_iterations',
                        default=2, type=int,
                        help='Number of iterations in confidence connected thresholding (default: %(default)s)')
    parser.add_argument('--segmentation_multiplier',
                        default=3.5, type=float,
                        help='Multiplier in confidence connected thresholding (default: %(default)s)')
    parser.add_argument('--initial_neighborhood_radius',
                        default=1, type=int,
                        help='Initial neighborhood radius in confidence connected thresholding (default: %(default)s)')
    parser.add_argument('--closing_radius',
                        default=0.5, type=float,
                        help='Morphological closing radius for cleaning up image (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('Muscle', vars(args)))

    # Run program
    Muscle(**vars(args))

if __name__ == '__main__':
    main()
