import sys
import argparse

parser = argparse.ArgumentParser (
    description="""Reads in .LOG file resulting from IPL_UPAT_CALGARY_EVAL_XT2_ROMO.""")

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

out.write('! This file was created with parse_IPL_UPAT_CALGARY_EVAL_XT2.py\n')

print ("Reading files...")

count = 0
for input_file in args.input_files:
    count = count + 1
    
    with open(input_file) as searchfile:
        entry = []
        print (input_file)

        for line in searchfile:
            if "ORIGAIM_FILENAME" in line: break
        parameter = 'Filename' 
        value = (line.split(']')[1]).split('.')[0]
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
    
        for line in searchfile:
            if "/vox_scanco_param" in line: break
        for line in searchfile:
            if "!% ov/tv  =" in line:
                parameter = 'BVTV'
                value = line.split()[3]
                value = '%.4f' % (100.0 * float(value))
                unit = '[%]'
                entry.append( [parameter, value, unit] )
                break
        
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
            if "!> MAT N (1/Th)     =" in line:
                parameter = 'TbN'
                value = '%.4f' % (float(line.split()[5]))
                unit = '[1/mm]'
                entry.append( [parameter, value, unit] )
                break

        for line in searchfile:
            if "/dt_object_param" in line: break
        for line in searchfile:
            if "!> Th        =" in line:
                parameter = 'TbTh'
                value = line.split()[3]
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break

        for line in searchfile:
            if "/dt_background_param" in line: break
        for line in searchfile:
            if "!> BG Th        =" in line:
                parameter = 'TbSp'
                value = line.split()[4]
                unit = (line.split(None,5)[5]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break
                 
        for line in searchfile:
            if "/moment2d_of_inertia" in line: break
        for line in searchfile:
            if "MEAN     " in line:
                parameter = 'BA.TtAr'
                value = line.split()[10]
                unit = '[mm^2]'
                entry.append( [parameter, value, unit] )
                parameter = 'TtAr'
                value = line.split()[11]
                unit = '[mm^2]'
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/moment2d_of_inertia" in line: break
        for line in searchfile:
            if "MEAN     " in line:
                parameter = 'BA.CtAr'
                value = line.split()[10]
                unit = '[mm^2]'
                entry.append( [parameter, value, unit] )
                parameter = 'CtAr'
                value = line.split()[11]
                unit = '[mm^2]'
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/moment2d_of_inertia" in line: break
        for line in searchfile:
            if "MEAN     " in line:
                parameter = 'BA.TbAr'
                value = line.split()[10]
                unit = '[mm^2]'
                entry.append( [parameter, value, unit] )
                parameter = 'TbAr'
                value = line.split()[11]
                unit = '[mm^2]'
                entry.append( [parameter, value, unit] )
                break

# -------------------------- ROMO -------------------------------

        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% mean_unit =" in line:
                parameter = 'TMD'
                value = line.split()[3]
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% mean_unit =" in line:
                parameter = 'CtTMD'
                value = line.split()[3]
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break
    
        for line in searchfile:
            if "/voxgobj_scanco_param" in line: break
        for line in searchfile:
            if "!% mean_unit =" in line:
                parameter = 'TbTMD'
                value = line.split()[3]
                unit = (line.split(None,4)[4]).splitlines(False)[0]
                entry.append( [parameter, value, unit] )
                break

        for line in searchfile:
            if "/mil_param" in line: break
        for line in searchfile:
            if "!> F.Ratio   =" in line:
                parameter = 'DA'
                value = '%.4f' % (float(line.split()[3]))
                unit = '[1]'
                entry.append( [parameter, value, unit] )
                break

        for line in searchfile:
            if "/connectivity" in line: break
        for line in searchfile:
            if "!> Connectivity Density:" in line:
                parameter = 'ConnD'
                value = '%.4f' % (float(line.split()[3]))
                unit = '[1/mm^3]'
                entry.append( [parameter, value, unit] )
                break

        for line in searchfile:
            if "/tri_da_metric_db" in line: break
        for line in searchfile:
            if "!> SMI       =" in line:
                parameter = 'SMI'
                value = '%.4f' % (float(line.split()[3]))
                unit = '[1]'
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

