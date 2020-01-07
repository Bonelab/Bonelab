from __future__ import division
import os
import os.path
import sys
import vtk
import csv
import numpy as np
import numpy.linalg
import math
from vtk.util import numpy_support as ns
from numpy.linalg import inv
import argparse

infile = sys.argv[2]
open(infile,'r')
#infile = r"/Users/jbhatla/Documents/UofC/PrEOA/Analysis/LOGS/PREOA_009_R_F_REG1.LOG"
basename = os.path.basename(infile)
name = basename.split("F")[0]
dirname = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Reg_Inputs/"
end = "MR_F_REG.txt"
filename = dirname + name + end

#Read Rotations
important = []
keep_phrases = ["DT Metric Measures"]

file = open(infile,"r").read()
lines =  file.splitlines()
for i in range(len(lines)):
    for phrase in keep_phrases:
        if phrase in lines[i]:
            important.append(lines[i+2])
            important.append(lines[i+3])
            important.append(lines[i+4])
            important.append(lines[i+5])
            important.append(lines[i+6])
            break

# Read Lateral Cartilage Measurements
Th_Parsed_LC = important[0].split()
SD_Parsed_LC = important[1].split()
Max_Parsed_LC = important[2].split()
Skew_Parsed_LC = important[3].split()
Kurtos_Parsed_LC = important[4].split()

Th_LC = Th_Parsed_LC[3]
SD_LC = SD_Parsed_LC[3]
Max_LC =Max_Parsed_LC[3]
Skew_LC = Skew_Parsed_LC[3]
Kurtos_LC = Kurtos_Parsed_LC[3]

# Read Lateral Bone Measurements
Th_Parsed_LB = important[5].split()
SD_Parsed_LB = important[6].split()
Max_Parsed_LB = important[7].split()
Skew_Parsed_LB = important[8].split()
Kurtos_Parsed_LB = important[9].split()

Th_LB = Th_Parsed_LB[3]
SD_LB = SD_Parsed_LB[3]
Max_LB =Max_Parsed_LB[3]
Skew_LB = Skew_Parsed_LB[3]
Kurtos_LB = Kurtos_Parsed_LB[3]


# Read Medial Cartilage Measurements
Th_Parsed_MC = important[10].split()
SD_Parsed_MC = important[11].split()
Max_Parsed_MC = important[12].split()
Skew_Parsed_MC = important[13].split()
Kurtos_Parsed_MC = important[14].split()

Th_MC = Th_Parsed_MC[3]
SD_MC = SD_Parsed_MC[3]
Max_MC =Max_Parsed_MC[3]
Skew_MC = Skew_Parsed_MC[3]
Kurtos_MC = Kurtos_Parsed_MC[3]

# Read Medial Bone Measurements
Th_Parsed_MB = important[15].split()
SD_Parsed_MB = important[16].split()
Max_Parsed_MB = important[17].split()
Skew_Parsed_MB = important[18].split()
Kurtos_Parsed_MB = important[19].split()

Th_MB = Th_Parsed_MB[3]
SD_MB = SD_Parsed_MB[3]
Max_MB =Max_Parsed_MB[3]
Skew_MB = Skew_Parsed_MB[3]
Kurtos_MB = Kurtos_Parsed_MB[3]


#Write parameters to .csv file
wfile = sys.argv[1]
#R = np.matrix([[Th_LC, SD_LC, Max_LC, Skew_LC, Kurtos_LC, Th_LB, SD_LB, Max_LB, Skew_LB, Kurtos_LB, Th_MC, SD_MC, Max_MC, Skew_MC, Kurtos_MC, Th_MB, SD_MB, Max_MB, Skew_MB, Kurtos_MB]])
R = np.matrix([[Th_LC, SD_LC, Max_LC, Th_LB, SD_LB, Max_LB, Th_MC, SD_MC, Max_MC, Th_MB, SD_MB, Max_MB]])
f = open(wfile,'a')
f.write ("%s %s %s %s %s %s %s %s %s %s %s %s %s \n" %(basename, Th_LC, SD_LC, Max_LC, Th_LB, SD_LB, Max_LB, Th_MC, SD_MC, Max_MC, Th_MB, SD_MB, Max_MB))
f.close()
