import sys
import argparse

parser = argparse.ArgumentParser (
    description="""Reads in .LOG file resulting from IPL_REGISTER_XT2 to calculate percent overlap.
    Calculations are based on the baseline measurement, and use the total number of voxels in the 
    volume before and after registration to calculate the percent overlap.""")

parser.add_argument ("--header", "-H",
    action="store_true",
    help="""Print a header line first.""")

parser.add_argument ("--delimiter", "-d",
    default = "\t",
    help="""Delimiter character to separate columns.  Default is a tab ('\\t').""")

parser.add_argument ("--output_file", "-o",
    help="Output file. If not specified, output will go to STDOUT.")

parser.add_argument ("input_files", nargs='*',
   help="Files to process. Any number may be specified.")

args = parser.parse_args()

if args.output_file == None:
    out = sys.stdout
else:
    out = open (args.output_file, "wt")

out.write('! This file was created with parse_IPL_REGISTER_XT2.py\n')

print ("Reading files...")

count = 0
for input_file in args.input_files:
    count = count + 1
    
    with open(input_file, encoding='cp1250') as searchfile:
        entry = []
        print (input_file)

        for line in searchfile:
            if "GOBJ_CORR_FILE" in line: break

        parameter = 'Filename' 
        value = (line.split(']')[1]).split('_M')[0]
        unit = '[name]'
        entry.append( [parameter, value, unit] )
        
        for line in searchfile:
            if "Processing Log" in line: break
        for line in searchfile:
            if "Original Creation-Date" in line:
                parameter = 'MeasDate'
                value = line.split()[2]
                unit = '[dd-mmm-yyyy]'
                entry.append( [parameter, value, unit] )
                break
        for line in searchfile:
            if "Index Patient" in line:
                parameter = 'Patient'
                value = line.split()[2]
                unit = '[#]'
                entry.append( [parameter, value, unit] )
                break
        for line in searchfile:
            if "Index Measurement" in line:
                parameter = 'Meas'
                value = line.split()[2]
                unit = '[#]'
                entry.append( [parameter, value, unit] )
                break
        for line in searchfile:
            if "Site" in line:
                parameter = 'Site'
                value = line.split()[1]
                unit = '[#]'
                entry.append( [parameter, value, unit] )
                break

        for line in searchfile:
            if "/vox_scanco_param" in line: break
        for line in searchfile:
            if "!% obj_nr =" in line:
                parameter = 'VolOrig'
                value = line.split()[3]
                unit = '[#]'
                entry.append( [parameter, value, unit] )
                vol_orig = float(value)
                break

        for line in searchfile:
            if "/vox_scanco_param" in line: break
        for line in searchfile:
            if "!% obj_nr =" in line:
                parameter = 'VolReg'
                value = line.split()[3]
                unit = '[#]'
                entry.append( [parameter, value, unit] )
                
                vol_reg = float(value)
                parameter = 'Overlap'
                value = '%.4f' % (100.0 * vol_reg / vol_orig)
                unit = '[%]'
                entry.append( [parameter, value, unit] )
                break

        # Print the output
        entry = list(zip(*entry))
        if args.header & (count==1):
            out.write (args.delimiter.join(entry[0]) + "\n")
            out.write (args.delimiter.join(entry[2]) + "\n")
        out.write (args.delimiter.join(entry[1]) + "\n")
                
if args.output_file != None:
    out.close()

print ("Done.")
quit()

