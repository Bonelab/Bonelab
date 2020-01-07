# Imports
import time
import sys
import os
import argparse
import re
import collections


def log(msg, *additionalLines):
    """Print message with time stamp.
    The first argument is printed with the a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    """
    if 'start_time' not in log.__dict__:
        log.start_time = time.time()
    if 'logFile' not in log.__dict__:
        log.logFile = sys.stdout

    if msg:
        log.logFile.write("%8.2f %s" % (time.time() - log.start_time, msg) + os.linesep)
    for line in additionalLines:
        log.logFile.write(" " * 14 + line + os.linesep)


def writeEntry(entry):
    """Print message with time stamp.
    The first argument is printed with the a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    """
    if 'csvFile' not in writeEntry.__dict__:
        writeEntry.csvFile = sys.stdout
    if 'header' not in writeEntry.__dict__:
        writeEntry.header = None
    if 'delimiter' not in writeEntry.__dict__:
        writeEntry.delimiter = ','

    # Check for None and convert to an empty string
    correctedEntry = []
    for column in entry:
        if column is None:
            correctedEntry.append("")
        else:
            correctedEntry.append(column)

    # Write it to the CSV file
    writeEntry.csvFile.write(writeEntry.delimiter.join(correctedEntry))
    writeEntry.csvFile.write(os.linesep)

# Arguments and Constants
version = 0.1
parser = argparse.ArgumentParser(
    description="Parse the outputs from direct mechanics",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
    "--delimiter", "-d",
    nargs='?',
    default=",",
    help="Delimiter character"
)
parser.add_argument(
    "--log", "-l",
    nargs='?',
    default="stdout",
    help="The log file"
)
parser.add_argument(
    "--output", "-o",
    nargs='?',
    default="stdout",
    help="The output CSV file"
)
parser.add_argument(
    "input_files",
    nargs='+',  # Note that ArgumentParser will glob the input expression into a list
    help="File to process (Performs Unix pattern matching)"
)
args = parser.parse_args()

# Setup maps
digitRegex=r'([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)'
nameToRegexDict = collections.OrderedDict()
nameToRegexDict['BV/TV'] = [r'^\s+Volume fraction\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['Exx'] = [r'^\s+Exx\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['Eyy'] = [r'^\s+Eyy\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['Ezz'] = [r'^\s+Ezz\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['Gyz'] = [r'^\s+Gyz\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['Gzx'] = [r'^\s+Gzx\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['Gxy'] = [r'^\s+Gxy\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['nu_yx'] = [r'^\s+nu_yx\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['nu_zx'] = [r'^\s+nu_zx\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['nu_xy'] = [r'^\s+nu_xy\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['nu_zy'] = [r'^\s+nu_zy\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['nu_xz'] = [r'^\s+nu_xz\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['nu_yz'] = [r'^\s+nu_yz\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 0]
nameToRegexDict['R_Exx'] = [r'^\s+Exx\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_Eyy'] = [r'^\s+Eyy\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_Ezz'] = [r'^\s+Ezz\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_Gyz'] = [r'^\s+Gyz\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_Gzx'] = [r'^\s+Gzx\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_Gxy'] = [r'^\s+Gxy\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_nu_yx'] = [r'^\s+nu_yx\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_nu_zx'] = [r'^\s+nu_zx\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_nu_xy'] = [r'^\s+nu_xy\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_nu_zy'] = [r'^\s+nu_zy\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_nu_xz'] = [r'^\s+nu_xz\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R_nu_yz'] = [r'^\s+nu_yz\s+=\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)$', 1]
nameToRegexDict['R11'] = [r'^\[\[\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]$', 0]
nameToRegexDict['R12'] = [r'^\[\[\s*(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]$', 0]
nameToRegexDict['R13'] = [r'^\[\[\s*(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]$', 0]
nameToRegexDict['R21'] = [r'^\s+\[\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]$', 0]
nameToRegexDict['R22'] = [r'^\s+\[\s*(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]$', 0]
nameToRegexDict['R23'] = [r'^\s+\[\s*(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]$', 0]
nameToRegexDict['R31'] = [r'^\s+\[\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]\]$', 0]
nameToRegexDict['R32'] = [r'^\s+\[\s*(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]\]$', 0]
nameToRegexDict['R33'] = [r'^\s+\[\s*(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*\]\]$', 0]

# Add all variables to an ordered dict for indexing. This just generates it
nameToIndexDict = {'LogFile': 0}
index = 1
for variable in nameToRegexDict:
    nameToIndexDict[variable] = index
    index += 1

# Generate header
header = [None for x in range(len(nameToIndexDict.keys()))]
for name in nameToIndexDict.keys():
    header[nameToIndexDict[name]] = name

# Setup the logger
if args.log.lower() == "stdout":
    log.logFile = sys.stdout
else:
    try:
        log.logFile = open(args.log, "wt")
    except IOError as e:
        sys.exit("Unable to open {0} for outputing. Exiting...".format(args.log))

# Open the CSV writter
writeEntry.delimiter = args.delimiter
if args.output.lower() == "stdout":
    writeEntry.csvFile = sys.stdout
    writeEntry(header)
else:
    if not os.path.isfile(args.output):
        try:
            writeEntry.csvFile = open(args.output, "at")
            writeEntry(header)
        except IOError as e:
            sys.exit("Unable to open CSV file {0}. Exiting...".format(args.output))
    else:
        try:
            writeEntry.csvFile = open(args.output, "at")
        except IOError as e:
            sys.exit("Unable to open CSV file {0}. Exiting...".format(args.output))

# Log our inputs
log("Started {0}".format(parser.prog))
log("", "Version {0}".format(version))
log("", "LogFile {0}".format(args.log))
log("", "CSVFile {0}".format(args.output))
log("", "Parsing {0} inputs".format(len(args.input_files)))

# Parse input files.
for inputFile in args.input_files:
    # Check if it's actually a file (not just a directory)
    if not os.path.isfile(inputFile):
        log("{0} is not a file. Skipping.".format(inputFile))
        continue

    # Log the file, preallocate CSV entry, put filename in entry
    baseName = os.path.basename(inputFile)
    log(baseName)
    entry = [None for x in range(len(header))]
    entry[0] = baseName

    # Load the whole file into memory as a list of strings
    # It'll be small files so it'll be fine.
    with open(inputFile, 'r') as fileHandle:
        text = fileHandle.read()

    nFoundEntries = 0
    for nameKey in nameToRegexDict:
        expression = nameToRegexDict[nameKey][0]
        index = nameToRegexDict[nameKey][1]
        varMatch = re.findall(expression, text, re.M)
        if varMatch:
            nFoundEntries += 1
            entry[nameToIndexDict[nameKey]] = varMatch[index]

    # Write CSV entry and log
    log("", "Found {0} matched entries".format(nFoundEntries))
    writeEntry(entry)

# Clean up
log("Cleaning up...")
if not (args.log.lower() == "stdout"):
    log.logFile.close()
if not (args.output.lower() == "stdout"):
    writeEntry.csvFile.close()
