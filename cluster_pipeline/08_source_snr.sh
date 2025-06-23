#!/bin/sh
#SBATCH --job-name=syntax-srcSNR
#SBATCH --time=1:00:00
#SBATCH --partition=shared-cpu
#SBATCH --output=/home/gercek/worker-logs/syntax-srcSNR-%j.out
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64GB

7z x /home/gercek/gercek_li_venv.7z -o/tmp/
source /tmp/gercek_li_venv/bin/activate
python /home/gercek/Projects/language-intermodulation/scripts/analysis/04_subject_source_snr.py \
    --proc clean --subject $PIPELINE_SUB --session 01 --task $PIPELINE_TASK --morph-fsaverage --snr-skip 2 --snr-neighbors 12

python /home/gercek/Projects/language-intermodulation/scripts/analysis/04_subject_source_snr.py \
    --proc clean --subject $PIPELINE_SUB --session 01 --task $PIPELINE_TASK --snr-skip 2 --snr-neighbors 12
