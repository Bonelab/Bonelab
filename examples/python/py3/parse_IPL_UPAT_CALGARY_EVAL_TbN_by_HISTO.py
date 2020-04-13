import sys
import argparse

parser = argparse.ArgumentParser (
    description="""Reads in .LOG file resulting from IPL_UPAT_CALGARY_EVAL.""")

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

out.write('! This file was created with parseIPL.py\n')

print ("Reading files...")

count = 0
for input_file in args.input_files:
    count = count + 1
    
    with open(input_file, encoding='cp1250') as searchfile:
        entry = []
        print (input_file)
        
        for line in searchfile:
            if "ORIGAIM_FILENAME" in line: break
        parameter = 'Filename' 
        value = (line.split(']')[1]).split('.')[0]
        unit = '[name]'
        entry.append( [parameter, value, unit] )
        
        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% mean_unit =" in line:
                parameter = 'BMD'
                value = line.split()[3]
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% mean_unit =" in line:
                parameter = 'CtBMD'
                value = line.split()[3]
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% mean_unit =" in line:
                parameter = 'TbBMD'
                value = line.split()[3]
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break
    
        bvtv = float(value) / 1200.0 # save bvtv for later
        
        value = '%.4f' % (100.0 * float(value) / 1200.0)
        parameter = 'BVTV'
        unit = '[%]'
        entry.append( [parameter, value, unit] )
    
        for line in searchfile:
            if "/dt_cortex_obj_param" in line: break
        for line in searchfile:
            if "!> C.Th        =" in line:
                parameter = 'CtTh'
                value = line.split()[3]
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% ov/tv  =" in line:
                parameter = 'CtPo'
                value = '%.4f' % (100.0 *(1.0 - float(line.split()[3])))
                unit = '[%]'
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "! Trabecular number (TbN):" in line: break
        for line in searchfile:
            if "Mean_unit   =	" in line:
                parameter = 'TbN'
                value = '%.4f' % (1.0/float(line.split()[2]))
                unit = (line.split(None,3)[3]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break
        
        tbn = (1.0/float(line.split()[2]))
    
        value = '%.4f' % (bvtv / tbn)
        parameter = 'TbTh'
        unit = '[mm]'
        entry.append( [parameter, value, unit] )
    
        value = '%.4f' % ((1.0 - bvtv) / tbn)
        parameter = 'TbSp'
        unit = '[mm]'
        entry.append( [parameter, value, unit] )
         
        for line in searchfile:
            if "/moment2d_of_inertia" in line: break
        for line in searchfile:
            if "MEAN     " in line:
                parameter = 'TtAr'
                value = line.split()[10]
                unit = '[mm^2]'
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/moment2d_of_inertia" in line: break
        for line in searchfile:
            if "MEAN     " in line:
                parameter = 'CtAr'
                value = line.split()[10]
                unit = '[mm^2]'
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/moment2d_of_inertia" in line: break
        for line in searchfile:
            if "MEAN     " in line:
                parameter = 'TbAr'
                value = line.split()[10]
                unit = '[mm^2]'
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

