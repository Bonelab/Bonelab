#!/bin/bash
#
# Returns the following information from an AIM
#   Volume
#   Patient Name
#   Index Patient
#   Index Measurement
#   Site
#
# Ensure that AIX is available by setting paths with setenv.sh:
# $ source /Applications/bonelab-1.7/setenv.sh
#
# Equivalent to running:
# $ aix -l C0006540_HOM_LS.AIM | grep -e "Volume" -e "Patient Name" -e "Index Patient" -e "Index Measurement" -e "Site"
#

if [ $# -lt 1 ] ; then
  echo "Usage: aix_info.sh C0005865_HOM_LS.AIM"
  echo "       aix_info.sh *.AIM"
  exit 1
fi

for f in $*
do
  #echo "Processing $f file..."
  ROOT_FILE_NAME=`echo "$f"`

  #aix -l ${ROOT_FILE_NAME} | grep -e "Volume"
  VOLUME_LEFT=`aix -l ${ROOT_FILE_NAME} | grep -e "Volume" | sed 's/^Volume[\ ]*//g'`
	VOLUME=`echo $VOLUME_LEFT | sed 's/$ *//g'`
 	#echo "[$VOLUME]"

  #aix -l ${ROOT_FILE_NAME} | grep -e "Patient Name"
  PATIENT_NAME_LEFT=`aix -l ${ROOT_FILE_NAME} | grep -e "Patient Name" | sed 's/^Patient\ Name[\ ]*//g'`
	PATIENT_NAME=`echo $PATIENT_NAME_LEFT | sed 's/$ *//g'`
	#echo "[$PATIENT_NAME]"

  #aix -l ${ROOT_FILE_NAME} | grep -e "Index Patient"
  INDEX_PATIENT=`aix -l ${ROOT_FILE_NAME} | grep -e "Index Patient" | sed 's/^Index\ Patient[\ ]*//g'`
  #echo "[$INDEX_PATIENT]"

  #aix -l ${ROOT_FILE_NAME} | grep -e "Index Measurement"
  INDEX_MEASUREMENT=`aix -l ${ROOT_FILE_NAME} | grep -e "Index Measurement" | sed 's/^Index\ Measurement[\ ]*//g'`
  #echo "[$INDEX_MEASUREMENT]"

  #aix -l ${ROOT_FILE_NAME} | grep -e "Site"
  SITE=`aix -l ${ROOT_FILE_NAME} | grep -e "Site" | sed 's/^Site[\ ]*//g'`
  #echo "[$SITE]"

  #PATIENT_NAME_LEFT=`echo "Patient Name                  John Doe, 332                 " | sed 's/^Patient\ Name[\ ]*//g'`
	#echo "[$PATIENT_NAME_LEFT]"
	#PATIENT_NAME=`echo $PATIENT_NAME_LEFT | sed 's/$ *//g'`
	#echo "[$PATIENT_NAME]"

  # Convert site code
  [[ $SITE == "20" ]] && SITE="RL"
  [[ $SITE == "21" ]] && SITE="RR"
  [[ $SITE == "38" ]] && SITE="TL"
  [[ $SITE == "39" ]] && SITE="TR"

	echo "\"$VOLUME\" \"$PATIENT_NAME\" \"$INDEX_PATIENT\" \"$INDEX_MEASUREMENT\" \"$SITE\""

done

exit 1
