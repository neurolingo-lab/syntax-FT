#!/bin/sh
#SBATCH --job-name=syntax-applyICAclean
#SBATCH --time=3:00:00
#SBATCH --partition=shared-cpu
#SBATCH --output=/home/gercek/worker-logs/syntax-applyICAclean-%j.out
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=128GB

7z x /home/gercek/gercek_li_venv.7z -o/tmp/
source /tmp/gercek_li_venv/bin/activate
mne_bids_pipeline --config $HOME/scratch/syntax_im/mnebids_pipeline_config.py  --subject $PIPELINE_SUB --session 01 --steps preprocessing/make_epochs,preprocessing/apply_ica,preprocessing/ptp_reject --task $PIPELINE_TASK
