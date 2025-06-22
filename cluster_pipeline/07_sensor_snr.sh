#!/bin/sh
#SBATCH --job-name=syntax-sourcemodel
#SBATCH --time=1:00:00
#SBATCH --partition=shared-cpu
#SBATCH --output=/home/gercek/worker-logs/syntax-sensorSNR-%j.out
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64GB

7z x /home/gercek/gercek_li_venv.7z -o/tmp/
source /tmp/gercek_li_venv/bin/activate
python /home/gercek/Projects/language-intermodulation/scripts/analysis/02_subject_sensor_snr.py \
    --proc clean --subject $PIPELINE_SUB --session 01 --save_deriv --snr-skip 2 --snr-neighbors 12
