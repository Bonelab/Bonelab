#!/bin/bash
# ---------------------------------------------------------------------
# Helpful commands:# squeue -u $USER
# squeue -u skboyd -t RUNNING
# squeue -u skboyd -t PENDING
#
# scontrol show job -dd <jobid>
#
# scancel <jobid>
# scancel -u $USER
# scancel -t PENDING -u $USER
# ---------------------------------------------------------------------
# 
# Batch 1: November 2021
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0006_RL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0006_RL_M00_HOM_LS_job 1 && sbatch ./models/EXAMPLE_0006_RL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0006_RR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0006_RR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0006_RR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0006_TL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0006_TL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0006_TL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0006_TR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0006_TR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0006_TR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0007_RL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0007_RL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0007_RL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0007_RR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0007_RR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0007_RR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0007_TL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0007_TL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0007_TL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0007_TR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0007_TR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0007_TR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0008_RL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0008_RL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0008_RL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0008_RR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0008_RR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0008_RR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0008_TL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0008_TL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0008_TL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0008_TR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0008_TR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0008_TR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0009_RL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0009_RL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0009_RL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0009_RR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0009_RR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0009_RR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0009_TL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0009_TL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0009_TL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0009_TR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0009_TR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0009_TR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0010_RL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0010_RL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0010_RL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0010_RR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0010_RR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0010_RR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0010_TL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0010_TL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0010_TL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0010_TR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0010_TR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0010_TR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0011_RL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0011_RL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0011_RL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0011_RR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0011_RR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0011_RR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0011_TL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0011_TL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0011_TL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0011_TR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0011_TR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0011_TR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0012_RL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0012_RL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0012_RL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0012_RR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0012_RR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0012_RR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0012_TL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0012_TL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0012_TL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0012_TR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0012_TR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0012_TR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0027_RL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0027_RL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0027_RL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0027_RR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0027_RR_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0027_RR_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0027_TL_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0027_TL_M00_HOM_LS_job 0 && sbatch ./models/EXAMPLE_0027_TL_M00_HOM_LS_job_slurm
./create_job.sh mesh_solve_analyze.sh ./models/EXAMPLE_0027_TR_M00_HOM_LS.AIM material_cort_trab_xt2.txt && python ./create_batch.py ./models/EXAMPLE_0027_TR_M00_HOM_LS_job 1 && sbatch ./models/EXAMPLE_0027_TR_M00_HOM_LS_job_slurm
exit
