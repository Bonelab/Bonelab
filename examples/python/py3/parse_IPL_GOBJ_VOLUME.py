import sys
import argparse

parser = argparse.ArgumentParser (
    description="""Reads in .LOG file resulting from IPL_GOBJ_VOLUME.""")

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

out.write('! This file was created with parse_IPL_GOBJ_VOLUME.py\n')

print ("Reading files...")

count = 0
for input_file in args.input_files:
    count = count + 1
    
    with open(input_file) as searchfile:
        entry = []
        print (input_file)
        
        for line in searchfile:
            if "GOBJ File" in line: break
        parameter = 'Filename' 
        value = (line.split(']')[1]).split('.')[0]
        unit = '[name]'
        entry.append( [parameter, value, unit] )
        
        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% ov     =" in line:
                parameter = 'TV'
                value = '%.4f' % (float(line.split()[3]))
                unit = '[mm^3]'
                entry.append( [parameter, value, unit] )
                break
    
        # Print the output
        entry = zip(*entry)
        if args.header & (count==1):
            out.write (args.delimiter.join(entry[0]) + "\n")
            out.write (args.delimiter.join(entry[2]) + "\n")
        out.write (args.delimiter.join(entry[1]) + "\n")
                
if args.output_file != None:
    out.close()

print ("Done.")
quit()

