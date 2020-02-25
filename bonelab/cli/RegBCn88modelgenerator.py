# Import packages:
import os
import sys
import time
import numpy as np
import argparse
import vtk
import vtkbone

from bonelab.util.echo_arguments import echo_arguments


# Utility functions:
def message(msg, *additionalLines):
    """Print message with time stamp.

    The first argument is printed with the a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    """
    print(('{0:8.2f} {1:s}'.format(time.time() - start_time, msg)))
    for line in additionalLines:
        print((" " * 9 + line))


start_time = time.time()


def CreateN88Model(input_file, config_file, correction, transform, overwrite, fixed_boundary):

    # Assign output file name:
    filename, ext = os.path.splitext(input_file)
    if (correction):
        output_file = filename + '.n88model'
    else:
        output_file = filename + '_NOROTATE.n88model'

    # Check if output file already exists, and ask permission to overwrite if not specified:
    if os.path.isfile(output_file) and not overwrite:
        result = eval(input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file)))
        if result.lower() not in ['y', 'yes']:
            print('Not overwriting. Exiting...')
            os.sys.exit()

    # Read input image:
    if not os.path.isfile(input_file):
        os.sys.exit('[ERROR] File \"{}\" not found!'.format(input_file))

    message("Reading AIM file " + input_file + " as input...")
    reader = vtkbone.vtkboneAIMReader()
    reader.SetFileName(input_file)
    reader.DataOnCellsOn()
    reader.Update()

    image = reader.GetOutput()
    if not reader.GetOutput():
        message("[ERROR] No image data read!")
        sys.exit(1)

    message("Image bounds:", (" %.4f" * 6) % image.GetBounds())

    # Read the configuration file:
    message("Reading configuration file...")
    exec(compile(open(config_file).read(), config_file, 'exec'), globals())
    settings_text = ["Parameters from RegN88Config:"]
    settings_text.append("Load                         = %s" % load_input)
    settings_text.append("Bone material id             = %s" % bone_material_id)
    settings_text.append("Bone Young's modulus         = %s" % bone_material_modulus)
    settings_text.append("Bone Poisson's ratio         = %s" % bone_material_poissons_ratio)
    settings_text.append("Bone Surface material id     = %s" % surface_material_id)
    settings_text.append("Bone Surface Young's modulus = %s" % surface_material_modulus)
    settings_text.append("Bone Surface Poisson's ratio = %s" % surface_material_poissons_ratio)
    settings_text.append("Top surface depth            = %s" % top_surface_maximum_depth)
    settings_text.append("Bottom surface depth         = %s\n" % bottom_surface_maximum_depth)
    message(*settings_text)

    # Read the transformation matrix:
    message("Reading IPL transformation matrix...")
    if(transform):
        t_mat = np.loadtxt(fname=transform, skiprows=2)
        rotation = t_mat[:3, :3]

    # Filter the image with a connectivity filter:
    message("Applying connectivity filter...")
    confilt = vtkbone.vtkboneImageConnectivityFilter()
    confilt.SetInputData(image)
    confilt.Update()
    image = confilt.GetOutput()

    # Generate a mesh:
    message("Generating mesh...")
    mesher = vtkbone.vtkboneImageToMesh()
    mesher.SetInputData(image)
    mesher.Update()
    mesh = mesher.GetOutput()

    # Generate material table:
    message("Generating material table...")
    E = bone_material_modulus
    v = bone_material_poissons_ratio
    material_name = 'Linear XT2'
    linear_material = vtkbone.vtkboneLinearIsotropicMaterial()
    linear_material.SetYoungsModulus(E)
    linear_material.SetPoissonsRatio(v)
    linear_material.SetName(material_name)

    material_table = vtkbone.vtkboneMaterialTable()
    material_table.AddMaterial(surface_material_id, linear_material)
    material_table.AddMaterial(bone_material_id, linear_material)

    # Compile the model:
    message("Compiling model...")
    modelConfig = vtkbone.vtkboneApplyTestBase()
    modelConfig.SetInputData(0, mesh)
    modelConfig.SetInputData(1, material_table)

    modelConfig.SetTopConstraintSpecificMaterial(surface_material_id)
    modelConfig.UnevenTopSurfaceOn()
    modelConfig.UseTopSurfaceMaximumDepthOn()
    modelConfig.SetTopSurfaceMaximumDepth(top_surface_maximum_depth)

    modelConfig.SetBottomConstraintSpecificMaterial(surface_material_id)
    modelConfig.UnevenBottomSurfaceOn()
    modelConfig.UseBottomSurfaceMaximumDepthOn()
    modelConfig.SetBottomSurfaceMaximumDepth(bottom_surface_maximum_depth)
    modelConfig.Update()

    model = modelConfig.GetOutput()
    message("Model bounds:", (" %.4f" * 6) % model.GetBounds())

    # Apply boundary conditions:
    message("Setting displacement boundary conditions...")
    e_init = np.array([0, 0, -load_input])

    # Apply fixed boundary conditions (default axial):
    if fixed_boundary == 'uniaxial':
        model.ApplyBoundaryCondition('face_z0', vtkbone.vtkboneConstraint.SENSE_Z, 0, 'z_fixed')
    elif fixed_boundary == 'axial':
        model.FixNodes('face_z0', 'bottom_fixed')
    else:
        message("[ERROR] Invalid fixed boundary conditions!")
        sys.exit(1)

    # Apply displacement boundary conditions:
    if "S1" in filename:
        message("Setting non-registered boundary conditions.")
        model.ApplyBoundaryCondition(
            'face_z1', vtkbone.vtkboneConstraint.SENSE_Z, e_init[2], 'z_moved')
    else:
        message("Setting registered boundary conditions.")
        if not (correction):
            message("[ERROR] Applying registered boundary conditions to the wrong image!")
            sys.exit(1)

        e_trafo = np.dot(np.linalg.inv(rotation), e_init)
        model.ApplyBoundaryCondition(
            'face_z1', vtkbone.vtkboneConstraint.SENSE_X, e_trafo[0], 'x_moved')
        model.ApplyBoundaryCondition(
            'face_z1', vtkbone.vtkboneConstraint.SENSE_Y, e_trafo[1], 'y_moved')
        model.ApplyBoundaryCondition(
            'face_z1', vtkbone.vtkboneConstraint.SENSE_Z, e_trafo[2], 'z_moved')

    info = model.GetInformation()
    pp_node_sets_key = vtkbone.vtkboneSolverParameters.POST_PROCESSING_NODE_SETS()
    pp_node_sets_key.Append(info, 'face_z1')
    pp_node_sets_key.Append(info, 'face_z0')

    model.AppendHistory("Created with blRegN88ModelGenerator version 1.1")

    # Write the n88model file:
    message("Writing n88model file...")
    writer = vtkbone.vtkboneN88ModelWriter()
    writer.SetInputData(model)
    writer.SetFileName(output_file)
    writer.Update()

    message("Done. Have a nice day!")


def main():

    description = '''Generates an n88model from registered images.'''

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog='blRegBCn88modelgenerator',
        description=description
    )
    parser.add_argument('input_file', help='Input image file (*REG_HOM_LS.AIM).')
    parser.add_argument('config_file', help='Configuration file (*.conf).')
    parser.add_argument('-c', '--correction', action='store_true',
                        help='Apply transformed boundary conditions from 3D registration.')
    parser.add_argument('-t', '--transform', help='Transformation matrix (*.txt).')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite existing output.')
    parser.add_argument('-b', '--fixed_boundary', default='axial',
                        help='Fixed boundary type (uniaxial/axial)')

    # Parse and display arguments:
    args = parser.parse_args()
    print((echo_arguments('blRegBCn88modelgenerator', vars(args))))

    # Run program HERE
    CreateN88Model(**vars(args))


# Call main function
if __name__ == '__main__':
    main()
