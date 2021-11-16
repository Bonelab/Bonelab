#!/usr/bin/python

import sys

if len(sys.argv) != 3:
  sys.exit("Usage: create_batch.py job_to_execute email_flag(1/0)")

job_file = str(sys.argv[1])
batch_file = job_file + "_slurm"

# ==============================================================================
#                 _ _
#       /\  /\___| (_)_  __
#      / /_/ / _ \ | \ \/ /
#     / __  /  __/ | |>  <
#     \/ /_/ \___|_|_/_/\_\
#        .hpc.ucalgary.ca                    
# 
# Compute Cluster. Send comments/deficiencies to support@hpc.ucalgary.ca
# 
# Helix hardware (12 nodes named c1 through c12):
# 
#  8 compute nodes, 24 cores, 256GB memory
#  1 GPU node with 2 NVIDIA Tesla K40m GPUs, 16 cores, 256GB RAM
#  2 Large-memory nodes, 64 cores, 2TB RAM and 6TB of /tmp
#  1 Fast node, 16 3.2GHz cores and 5TB of SSD /tmp
# 
# Please refer to the Helix Quick Start Guide on how to access hardware.
# http://hpc.ucalgary.ca/quickstart/helix
#
# ===========================================================================
#                     __________________________
#                         __     ____       __  
#                         / |    /    )   /    )
#                     ---/__|---/___ /---/------
#                       /   |  /    |   /       
#                     _/____|_/_____|__(____/___
#                          arc.ucalgary.ca                          
# 
# Please note: WE DO NOT PERFORM BACKUPS
# 
# Filesystem Limits: 
# 500 GB limit for home directories
# 30  TB limit on /scratch
# 
# /scratch usage: If you want to use the larger quota in /scratch, please use
# 	 	/scratch/$SLURM_JOB_ID as the scratch directory for your job. 
# 
#               PLEASE NOTE:
# 
#                   /scratch/$SLURM_JOB_ID directories will be deleted
# 		  5 days after the job finishes.
# 
#                 
#                Problems or deficiencies? Send email to:
#                        support@hpc.ucalgary.ca
#                  
# ===========================================================================

f = open(batch_file,"w") 
  
f.write("#!/bin/sh\n")
f.write("\n")
f.write("# ---------------------------------------------------------------------\n")
f.write("# SLURM script for a job on a Compute Canada cluster: ARC. \n")
f.write("# ---------------------------------------------------------------------\n")
f.write("#SBATCH --nodes=1\n")
f.write("#SBATCH --ntasks=1            # number of MPI processes\n")
f.write("#SBATCH --cpus-per-task=6     # number of threads (WARNING: match threads for faim).\n")
#f.write("#SBATCH --partition=gpu       # use the old gpus\n")
#f.write("#SBATCH --gres=gpu:3          # use 3 gpus\n")
#f.write("#SBATCH --mem=8000M           # memory; default unit is megabytes\n")
f.write("#SBATCH --mem=12000M           # memory; default unit is megabytes\n")
f.write("#SBATCH --time=0-08:00        # time (DD-HH:MM)\n")
f.write("#SBATCH --job-name=EXAMPLE      # identifies the job name\n")
if (int(sys.argv[2]) > 0):
  f.write("#SBATCH --mail-user=example@ucalgary.ca\n")
  f.write("#SBATCH --mail-type=BEGIN\n")
  f.write("#SBATCH --mail-type=END\n")
  f.write("#SBATCH --mail-type=FAIL\n")
f.write("\n")
f.write("cd /home/skboyd/example\n")
f.write(sys.argv[1])
f.write("\n")
f.write("# ---------------------------------------------------------------------\n")
f.write("echo \"Current working directory: `pwd`\"\n")
f.write("echo \"Starting run at: `date`\"\n")
f.write("# ---------------------------------------------------------------------\n")
f.write("# Helpful commands:")
f.write("# squeue -u $USER\n")
f.write("# squeue -u skboyd -t RUNNING\n")
f.write("# squeue -u skboyd -t PENDING\n")
f.write("#\n")
f.write("# scontrol show job -dd <jobid>\n")
f.write("#\n")
f.write("# scancel <jobid>\n")
f.write("# scancel -u $USER\n")
f.write("# scancel -t PENDING -u $USER\n")
f.write("# ---------------------------------------------------------------------\n")
f.close()


