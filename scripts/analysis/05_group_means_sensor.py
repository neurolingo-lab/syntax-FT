import pickle
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

import numpy as np
from tqdm import tqdm

import intermodulation.analysis as ima

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Pipeline script to compute source space signal-to-noise data "
        "for individual subjects in the frequency spectrum."
    )
    parser.add_argument(
        "--task",
        type=str,
        default="syntaxIM",
        help="Task name, should match the task name in the BIDS dataset.",
    )
    parser.add_argument(
        "--bids_root",
        type=Path,
        default="/srv/beegfs/scratch/users/g/gercek/syntax_im/syntax_dataset",
        help="Root directory for BIDS dataset",
    )
    parser.add_argument(
        "--plotpath",
        type=Path,
        default="/srv/beegfs/scratch/users/g/gercek/syntax_im/results/",
        help="Directory in which to save SNR plots, if any",
    )
    args = parser.parse_args()

    # STORAGE LOCATIONS
    bids_root = args.bids_root
    savepath = args.plotpath / "sub-all"

    savepath.mkdir(parents=True, exist_ok=True)
    allcond_path = savepath / "allcond"
    allcond_path.mkdir(parents=True, exist_ok=True)
    percond_path = savepath / "percond"
    percond_path.mkdir(parents=True, exist_ok=True)

    derivatives_root = bids_root / "derivatives/mne-bids-pipeline"
    fs_root = bids_root / "derivatives/freesurfer"
    fs_sub = "fsaverage"

    # Load in PSD, SNR data from individual subject files
    subfiles_allcond = {}
    subfiles_percond = {}

    template_dict = {"ONEWORD": defaultdict(list), "TWOWORD": defaultdict(list)}

    psds_allcond = deepcopy(template_dict)
    snrs_allcond = deepcopy(template_dict)

    psds_percond = deepcopy(template_dict)
    snrs_percond = deepcopy(template_dict)

    owconds = ("WORD", "NONWORD")
    twconds = ("PHRASE", "NONPHRASE", "NONWORD")
    owfreqs = ("F1", "F2")
    twfreqs = ("F1LEFT", "F1RIGHT")
    for task in tqdm(("ONEWORD", "TWOWORD"), desc="Processing tasks"):
        tasktags = owfreqs if task == "ONEWORD" else twfreqs
        taskconds = owconds if task == "ONEWORD" else twconds

        allcond_path_task = allcond_path / task.lower()
        allcond_path_task.mkdir(parents=True, exist_ok=True)
        percond_path_task = percond_path / task.lower()
        percond_path_task.mkdir(parents=True, exist_ok=True)

        subfiles_allcond[task] = list(
            derivatives_root.rglob(
                f"sub-*_ses-*_task-{args.task}_desc-morphFSAVG{task.lower()}_allcondSNRsource.pkl"
            )
        )
        subfiles_percond[task] = list(
            derivatives_root.rglob(
                f"sub-*_ses-*_task-{args.task}_desc-morphFSAVG{task.lower()}_percondSNRsource.pkl"
            )
        )
        for tasktag in tqdm(tasktags, desc=f"Processing task {task} freq tags", leave=False):
            all_label = f"{task}/{tasktag}"
            for i, file in tqdm(
                enumerate(subfiles_allcond[task]),
                desc=f"Processing {all_label} files",
                leave=False,
            ):
                with open(file, "rb") as f:
                    filedata = pickle.load(f)
                psds_allcond[task][tasktag].append(filedata[tasktag]["psd"])
                snrs_allcond[task][tasktag].append(filedata[tasktag]["snrs"])
                if i == 0:
                    template_stc = filedata[tasktag]["stc"]
            grand_mean_psd = np.average(psds_allcond[task][tasktag], axis=0)
            psds_allcond[task][tasktag] = []
            # grand_mean_snr = np.average(snrs_allcond[task][tasktag], axis=0)
            grand_mean_snr = ima.snr_spectrum(
                grand_mean_psd,
                noise_n_neighbor_freqs=9,
                noise_skip_neighbor_freqs=2,
            )
            snrs_allcond[task][tasktag] = []

            np.save(
                allcond_path_task / f"grand_mean_psd_{tasktag}.npy",
                grand_mean_psd,
            )
            np.save(
                allcond_path_task / f"grand_mean_snr_{tasktag}.npy",
                grand_mean_snr,
            )

            mean_psd_stc = template_stc.copy()
            mean_psd_stc.data = np.nan_to_num(grand_mean_psd)
            mean_psd_stc.save(
                allcond_path_task / f"grand_mean_psd_{tasktag}",
                ftype="stc",
                overwrite=True,
                verbose="error",
            )

            mean_snr_stc = template_stc.copy()
            mean_snr_stc.data = np.nan_to_num(grand_mean_snr)
            mean_snr_stc.save(
                allcond_path_task / f"grand_mean_snr_{tasktag}",
                ftype="stc",
                overwrite=True,
                verbose="error",
            )

            for file in tqdm(
                subfiles_percond[task], desc=f"Processing {all_label} conds", leave=False
            ):
                with open(file, "rb") as f:
                    filedata = pickle.load(f)

                for i, cond in enumerate(taskconds):
                    cond_label = f"{cond}/{tasktag}"
                    psds_percond[task][cond_label].append(filedata[cond_label]["psd"])
                    snrs_percond[task][cond_label].append(filedata[cond_label]["snrs"])
                    if i == 0:
                        template_stc = filedata[cond_label]["stc"]

                    grand_mean_psd = np.average(psds_percond[task][cond_label], axis=0)
                    psds_percond[task][cond_label] = []
                    grand_mean_snr = np.average(snrs_percond[task][cond_label], axis=0)
                    snrs_percond[task][cond_label] = []

                    cond_label = cond_label.replace("/", "-")
                    np.save(
                        percond_path_task / f"grand_mean_psd_{cond_label}.npy",
                        grand_mean_psd,
                    )
                    np.save(
                        percond_path_task / f"grand_mean_snr_{cond_label}.npy",
                        grand_mean_snr,
                    )

                    mean_psd_stc = template_stc.copy()
                    mean_psd_stc.data = np.nan_to_num(grand_mean_psd)
                    mean_psd_stc.save(
                        percond_path_task / f"grand_mean_psd_{cond_label}",
                        ftype="stc",
                        overwrite=True,
                        verbose="error",
                    )

                    mean_snr_stc = template_stc.copy()
                    mean_snr_stc.data = np.nan_to_num(grand_mean_snr)
                    mean_snr_stc.save(
                        percond_path_task / f"grand_mean_snr_{cond_label}",
                        ftype="stc",
                        overwrite=True,
                        verbose="error",
                    )
