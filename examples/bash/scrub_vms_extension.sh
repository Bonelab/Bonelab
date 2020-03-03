#!/bin/bash
#
# This is a simple script to remove the version extension from files that 
# have been downloaded from our VMS server.
#
# Assuming this script is in the current directory, it can be run as follows:
#
#    ./scrub_vms_extension.sh D0001274_OBLIQUE.TIF;1
#
#    But, this will cause errors because the bash shell interprets the ";" as a
#    command. So, the way to solve this problem is to run the command with "*" 
#    instead:
#
#    ./scrub_vms_extension.sh D0001274_OBLIQUE.TIF*
#
#    Or, for many files in a directory, try:
#
#    ./scrub_vms_extension.sh D0001274_*



if [ $# -lt 1 ] ; then
  echo "Usage: scrub_vms_extension.sh FILE.AIM;1"
  echo "       scrub_vms_extension.sh FILE.*"
  exit 1
fi

for f in $*
do
  #echo "Processing $f file..."
  ROOT_FILE_NAME=`echo "$f" | sed 's/;[0-9]*//'`
  mv $f ${ROOT_FILE_NAME}
done

exit 1
