#!/bin/sh
#SBATCH --job-name=syntax-grpmean
#SBATCH --time=1:00:00
#SBATCH --partition=shared-cpu
#SBATCH --output=/home/gercek/worker-logs/syntax-grpmean-%j.out
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64GB

7z x /home/gercek/gercek_li_venv.7z -o/tmp/
source /tmp/gercek_li_venv/bin/activate
python /home/gercek/Projects/language-intermodulation/scripts/analysis/05_group_means_sensor.py \
    --task $PIPELINE_TASK

python /home/gercek/Projects/language-intermodulation/scripts/analysis/06_group_means_source.py \
    --task $PIPELINE_TASK

xvfb-run -d python /home/gercek/Projects/language-intermodulation/scripts/analysis/07_plot_group_means_sensor.py \
    --task $PIPELINE_TASK

xvfb-run -d python /home/gercek/Projects/language-intermodulation/scripts/analysis/08_plot_group_means_source.py \
    --task $PIPELINE_TASK