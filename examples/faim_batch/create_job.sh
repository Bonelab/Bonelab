#!/bin/bash
#
# This script performs the following steps:
# 1. Uses a template of 'mesh_solve_analyze' and replaces the variables with hardcoded names.
#    Inputs are the name of the image file (.aim) and the name of the test type (axial or uniaxial).
# 2. Submits the job for processing.
#
#    ./create_job template_mesh_solve_analyze image_file material_file
#
# where template_mesh_solve_analyze is the original python script to run the FE job,
# image_file is the segmented image file to be processed, and
# material_file is configuration file for material properties.
#

if [ $# -ne 3 ] ; then
  echo "Usage: create_job mesh_solve_analyze.sh image_file material_file"
  exit 1
fi

TEMPLATE_FILE="$1"
INPUT_IMAGE_FILE="$2"
MATERIAL_FILE="$3"

# Strip off the extension of the input file
ROOT_FILE_NAME=`echo "${INPUT_IMAGE_FILE}" | sed 's/\(.*\)\..*/\1/'`
MODEL_FILE="${ROOT_FILE_NAME}.n88model"
PISTOIA_FILE="${ROOT_FILE_NAME}_pistoia.txt"
LOG_FILE="${ROOT_FILE_NAME}.log"

JOB_FILE="${ROOT_FILE_NAME}_job"
TMP_FILE="${ROOT_FILE_NAME}_tmp"

date

cp ${TEMPLATE_FILE} ${TMP_FILE}

echo "Create job ${JOB_FILE}"

# Replace variables with hardcoded names
sed "s@INPUT_IMAGE_FILE@$INPUT_IMAGE_FILE@g" ${TMP_FILE} > ${JOB_FILE} && mv ${JOB_FILE} ${TMP_FILE}
sed "s@MATERIAL_FILE@$MATERIAL_FILE@g" ${TMP_FILE} > ${JOB_FILE} && mv ${JOB_FILE} ${TMP_FILE}
sed "s@MODEL_FILE@$MODEL_FILE@g" ${TMP_FILE} > ${JOB_FILE} && mv ${JOB_FILE} ${TMP_FILE}
sed "s@PISTOIA_FILE@$PISTOIA_FILE@g" ${TMP_FILE} > ${JOB_FILE} && mv ${JOB_FILE} ${TMP_FILE}
sed "s@LOG_FILE@$LOG_FILE@g" ${TMP_FILE} > ${JOB_FILE}

rm ${TMP_FILE}
chmod 755 ${JOB_FILE}

exit
