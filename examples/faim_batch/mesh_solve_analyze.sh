#!/bin/bash
#
# This script is a template of the standard mesh_solve_analyze so that 
# it can be hardcoded for a specific job. This is used in conjunction 
# with 'submit_example.sh' and is used on arc.ucalgary.ca
#
# This is a simple script that takes a segmented image file name as input,
# generates a finite element model using n88modelgenerator, then solves
# it with the FAIM solver.
#
# Assuming this script is in the current directory, it can be run as follows:
#
#    ./mesh_solve_analyze image_file material_file
#
# where image_file is the segmented image file to be processed, and
# config_file is an n88modelgenerator configuration file.
#
# You may want to edit this script in order to customize it.

source activate faim-8.1
source /home/skboyd/Numerics88/Faim\ 8.1/setenv

echo
echo "    ==== Generating MODEL_FILE ===="
echo
n88modelgenerator \
    INPUT_IMAGE_FILE \
    --material_definitions MATERIAL_FILE \
    --test axial \
    --test_axis z \
    --normal_strain -0.01 \
    --maximum_iterations 30000 \
    --convergence_tolerance 1E-6 \
    MODEL_FILE

if [ $? -ne 0 ] ; then
  echo "Mesh generation returned error."
  exit 1
fi

echo
echo "    ==== Solving and post-processing FE model ===="
echo "    WARNING: Match threads to request for batch job"
echo
#faim  --engine=nv --device=0,1,2 MODEL_FILE
faim  --engine=mt --threads=6 MODEL_FILE
#faim  --engine=mt --threads=8 MODEL_FILE
#faim  --engine=mt --threads=12 MODEL_FILE
#faim  --engine=mt --threads=24 MODEL_FILE

if [ $? -ne 0 ] ; then
  echo "faim returned error."
  exit 1
fi

echo
echo "    ==== Compressing data file ===="
echo
n88copymodel --compress MODEL_FILE MODEL_FILE
if [ $? -ne 0 ] ; then
  echo "copymodel returned error."
  exit 1
fi

echo
echo "    ==== Performing Pistoia criterion analysis ===="
echo
n88pistoia MODEL_FILE \
  --critical_volume 2.0 \
  --critical_strain 0.007 \
  --output_file PISTOIA_FILE
if [ $? -ne 0 ] ; then
  echo "n88pistoia returned error."
  exit 1
fi

echo
echo "    ==== Generate a log file ===="
echo
n88modelinfo --log MODEL_FILE > LOG_FILE
if [ $? -ne 0 ] ; then
  echo "n88modelinfo returned error."
  exit 1
fi

echo
echo "    ==== Moving a large n88model file ===="
echo

#scp MODEL_FILE bonelab@winston.ucalgary.ca:/lu102/bonelab/Backup/example/
rm MODEL_FILE
#if [ $? -ne 0 ] ; then
#  echo "n88modelinfo returned error when using SCP."
#  exit 1
#fi

echo
