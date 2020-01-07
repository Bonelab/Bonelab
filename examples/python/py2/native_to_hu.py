# History:
#   2017.03.16  babesler@ucalgary.ca    Created
#
# Description:
#   Function to convert an AIM to another image format and scale it to HU from
#       SCANCO native units.
#
# Notes:
#   - This uses the processing log entries 'Mu_Scaling' and 'HU: mu water' to
#       determine the linear equation between native units and HU
#   - Outut is a float
#   - I don't think it is working perfectly yet
#
# Usage: python native_to_hu.py input.aim output.nii

# Imports
import argparse
import vtk
import re
import os
try:
    import vtkbone
    reader = vtkbone.vtkboneAIMReader()
except ImportError:
    try:
        import vtkn88
        reader = vtkn88.vtkn88AIMReader()
    except ImportError:
        try:
            import vtkbonelab
            reader = vtkbonelab.vtkbonelabAIMReader()
        except ImportError:
            os.sys.exit('Unable to import vtkbone, vtkn88, or vtkbonelab. Exiting...')

# Argument parser
parser = argparse.ArgumentParser(
    description='Subget medical data',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    'inputImage',
    help='The input AIM (*.aim) image)')
parser.add_argument(
    'outputImage',
    help='The output NIfTI (*.nii) image)')
parser.add_argument(
    '-f', '--force',
    action='store_true',
    help='Set to overwrite output without asking')
args = parser.parse_args()

# Test inputs
if not os.path.isfile(args.inputImage):
    os.sys.exit('Input file \"{inputImage}\" does not exist. Exiting...'.format(inputImage=args.inputImage))
if not args.inputImage.lower().endswith('.aim'):
    os.sys.exit('Input file \"{inputImage}\" is not of type AIM. Exiting...'.format(inputImage=args.inputImage))
if not args.outputImage.lower().endswith('.nii'):
    os.sys.exit('Output file \"{outputImage}\" is not of type AIM. Exiting...'.format(outputImage=args.outputImage))
if os.path.isfile(args.outputImage):
    if not args.force:
        answer = raw_input('Output file \"{outputImage}\" exists. Overwrite? [Y/n]'.format(outputImage=args.outputImage))
        if str(answer).lower() not in set(['yes','y', 'ye', '']):
            os.sys.exit('Will not overwrite \"{outputImage}\". Exiting...'.
            format(outputImage=args.outputImage))

# Read in the AIM file
reader.SetFileName(args.inputImage)
reader.DataOnCellsOff()
print("Reading in {}...".format(args.inputImage))
reader.Update()

# Parse proc log
print("Processing the proc log...")
proclog = reader.GetProcessingLog()
mu_scaling_match = re.search(r'Mu_Scaling\s+(\d+)', proclog)
hu_mu_water_match = re.search(r'HU: mu water\s+(\d+.\d+)', proclog)
mu_scaling = int(mu_scaling_match.group(1))
hu_mu_water = float(hu_mu_water_match.group(1))
hu_mu_air = 0
print('Found the following calibration data in the header:')
print('\tmu_scaling: {}'.format(mu_scaling))
print('\thu_mu_water: {}'.format(hu_mu_water))

# First convert Native -> mu (linear attenuation)
#   mu = Native / mu_scaling
# Second convert mu -> HU
#   HU = 1000 * (mu - mu_water) / (mu_water - mu_air)

m = 1000.0 / mu_scaling / (hu_mu_water - hu_mu_air)
b = -1000.0 * hu_mu_water / (hu_mu_water - hu_mu_air)

print "Proc. log eq: {0} * x {1:+f}".format(m,b)
print "Proc. log eq: {0} * (x {1:+f})".format(m,b/m)

# Apply shift
caster = vtk.vtkImageShiftScale()
caster.SetOutputScalarTypeToFloat()
caster.ClampOverflowOn()
caster.SetInputConnection(reader.GetOutputPort())
caster.SetShift(b/m)
caster.SetScale(m)
print("Shifting and scaling input...")
caster.Update()

# Write outputImage
writer = vtk.vtkNIFTIImageWriter()
writer.SetFileName(args.outputImage)
writer.SetInputConnection(caster.GetOutputPort())
print("Writing to {}".format(args.outputImage))
writer.Update()
