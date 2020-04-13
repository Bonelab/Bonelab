##Updated 2016-JUL-07 by Sarah Manske
##Use with extreme caution - compare results with XT2 database
##Refer to parse_IPL_UPAT_CALGARY_EVAL_XT1.py

import sys
import argparse

parser = argparse.ArgumentParser (
    description="""Reads in .LOG file resulting from IPL_UPAT_CALGARY_EVAL_XT2_LLAC.""")

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

out.write('! This file was created with parse_IPL_UPAT_CALGARY_EVAL_XT2_LLAC.py\n')

print ("Reading files...")

count = 0
for input_file in args.input_files:
    count = count + 1
    
    with open(input_file, encoding='cp1250') as searchfile:
        entry = []
        print (input_file)
        
        for line in searchfile:
            if "IPL_ISQ" in line: break
        name = (line.split(']')[1]).split('.')[0]
        
        parameter = 'Subject' 
        value = 'VITD_' + name.split('_')[1]
        unit = '[name]'
        entry.append( [parameter, value, unit] )
        
        parameter = 'Visit' 
        value = name.split('_')[2]
        unit = '[month]'
        entry.append( [parameter, value, unit] )
        
        parameter = 'OrgFile' 
        value = name
        unit = '[name]'
        entry.append( [parameter, value, unit] )
        
        for line in searchfile:
            if "Processing Log" in line: break
        for line in searchfile:
            if "Original Creation-Date" in line:
                parameter = 'Date'
                value = line.split()[2]
                unit = '[dd-mmm-yyyy]'
                entry.append( [parameter, value, unit] )
                break
        for line in searchfile:
            if "Site" in line:
                parameter = 'Site'
                value = line.split()[1]
                unit = '[#]'
                entry.append( [parameter, value, unit] )
                break

        err = False 
        
        for line in searchfile:
            if "Empty GOBJ-File" in line: err = True # If the GOBJ is empty, then an error is triggered
            if "/examine" in line: break
        for line in searchfile:
            if "!> OV        =" in line:
                parameter = 'CaV'
                value = line.split()[3]
                calcification_volume = float(value)
                if err: value = "x"
                unit = '[mm^3]'
                entry.append( [parameter, value, unit] )
                break
        for line in searchfile:
            if "!> TV        =" in line:
                parameter = 'TtV'
                value = line.split()[3]
                if err: value = "x"
                unit = '[mm^3]'
                entry.append( [parameter, value, unit] )
                break

        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% mean_unit =" in line:
                parameter = 'CaBMD'
                value = line.split()[3]
                bmd = value
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                if err: value = "x"
                entry.append( [parameter, value, unit] )
                break

        parameter = 'CaBMC'
        value = '%.4f' % (calcification_volume/1000.0 * float(bmd))
        if err: value = "x"
        unit = '[mg HA]'
        entry.append( [parameter, value, unit] )
    
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

