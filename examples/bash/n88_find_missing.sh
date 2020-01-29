#!/bin/bash
#
# Returns name of AIM file for which there is no successful n88 solution.
#
# Provide the names of the AIM files, and if any of the .log, .n88model,
# _analysis.txt or _pistoia.txt are missing, the name of the AIM is returned.
#
# Assuming this script is in the current directory, it can be run as follows:
#
#    ./n88_find_missing C0005865_HOM_LS.AIM
#

if [ $# -lt 1 ] ; then
  echo "Usage: n88_find_missing.sh C0005865_HOM_LS.AIM"
  echo "       n88_find_missing.sh *.AIM"
  exit 1
fi

for f in $*
do
  #echo "Processing $f file..."
  ROOT_FILE_NAME=`echo "$f" | sed 's/\(.*\)\..*/\1/'`
	AIM_FILE="${ROOT_FILE_NAME}.AIM"
	LOG_FILE="${ROOT_FILE_NAME}.log"
	MODEL_FILE="${ROOT_FILE_NAME}.n88model"
	ANALYSIS_FILE="${ROOT_FILE_NAME}_analysis.txt"
	PISTOIA_FILE="${ROOT_FILE_NAME}_pistoia.txt"
	#echo "$AIM_FILE"
	#echo "$LOG_FILE"
	#echo "$MODEL_FILE"
	#echo "$ANALYSIS_FILE"
	#echo "$PISTOIA_FILE"

	#if [[ ! -f "$LOG_FILE" || ! -f "$MODEL_FILE" || ! -f "$ANALYSIS_FILE" || ! -f "$PISTOIA_FILE" ]]; then
	#	echo "$f"
	#fi
	
	# This is the equivalent statement to the above (except MODEL_FILE is not included in the search list)
  [[ ! -f "$LOG_FILE" || ! -f "$ANALYSIS_FILE" || ! -f "$PISTOIA_FILE" ]] && echo "$f"

	# This will find the complementary files 
 	#[[ -f "$LOG_FILE" && -f "$MODEL_FILE" && -f "$ANALYSIS_FILE" && -f "$PISTOIA_FILE" ]] && echo "$f"

done

exit 1

