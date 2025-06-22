#!/bin/sh
#SBATCH --job-name=syntax-dataqual
#SBATCH --time=4:00:00
#SBATCH --partition=shared-cpu
#SBATCH --output=/home/gercek/worker-logs/syntax-dataqual-%j.out
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=128GB

7z x /home/gercek/gercek_li_venv.7z -o/tmp/
source /tmp/gercek_li_venv/bin/activate
mne_bids_pipeline --config $HOME/Projects/language-intermodulation/cluster_pipeline/mnebids_pipeline_config.py  --subject $PIPELINE_SUB --session 01 --steps preprocessing/data_quality --task $PIPELINE_TASK
