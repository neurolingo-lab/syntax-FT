from pathlib import Path

import mne
import numpy as np
import pandas as pd

from intermodulation.analysis_spec import make_parser, pick_points


def get_clim_pct(
    data: np.ndarray, fidx: int, lower_perc: float, middle_perc: float, upper_perc: float
) -> dict:
    fdata = data[:, fidx]
    lb = np.percentile(fdata, lower_perc)
    if lb <= 1:
        lb = 1.0
    mv = np.percentile(fdata, middle_perc)
    if mv <= 1.5 or mv <= lb:
        mv = 3
    ub = np.percentile(fdata, upper_perc)
    if ub <= 2.0 or ub <= mv:
        ub = 10
    return dict(kind="value", lims=np.array((lb, mv, ub)))


if __name__ == "__main__":
    parser = make_parser(group_level=True, plots=True)
    parser.description = (
        "Pipeline script to plot source space signal-to-noise data averaged across all subjects."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default="/srv/beegfs/scratch/users/g/gercek/syntax_im/results",
        help="Root directory for group mean data. Must have a folder `sub-all` generated by "
        "`06_group_means_source` with associated source time course files.",
    )
    parser.add_argument(
        "--fs-sub-dir",
        type=Path,
        default="/srv/beegfs/scratch/users/g/gercek/syntax_im/syntax_dataset/derivatives/freesurfer",
        help="Path to the freesurfer subjects directory in which recon-all outputs are stored for "
        "the `fsaverage` subject.",
    )
    parser.add_argument(
        "--freq-bin-offset",
        type=int,
        default=-1,
        help="The MEGIN Elektra at FCBG is known to sample slightly faster than advertised, which "
        "affects the true frequencies observed in the FFT and will lead to a slightly lower freq "
        "than in reality. This allows for us to correct in frequency bin steps. negative values "
        "are ok.",
    )
    parser.add_argument(
        "--clim",
        nargs=3,
        type=float,
        help="Percentiles to use as lower, middle, and upper anchors of the color map. Note that "
        "if any chosen percentile (low, mid, high) results in a value of < 1, then that value will"
        " instead be set to a default of (1.5, 2.5, 4) for L/M/H respectively.",
    )
    parser.add_argument(
        "--auto-clim",
        action="store_true",
        help="Whether to automatically determine the color map for brain plots from the data. "
        "Lower and upper bounds will be chosen at the 5th and 95th percentiles of the data for the"
        " chosen plotting frequencies.",
    )
    args = parser.parse_args()

    if args.auto_clim and len(args.clim) == 3:
        raise ValueError("Cannot set `auto-clim` and provide bounds for color map!")

    # STORAGE LOCATIONS
    stc_root = args.results_dir / "sub-all"
    savepath = args.plotpath / "sub-all"

    savepath.mkdir(parents=True, exist_ok=True)
    (savepath / "allcond").mkdir(parents=True, exist_ok=True)
    (savepath / "percond").mkdir(parents=True, exist_ok=True)

    tag_f = (6, 7.05882353)

    tasks = ("ONEWORD", "TWOWORD")
    ow_tags = ("F1", "F2")
    tw_tags = ("F1LEFT", "F1RIGHT")
    ow_conds = ("WORD", "NONWORD")
    tw_conds = ("PHRASE", "NONPHRASE", "NONWORD")

    if not args.auto_clim and len(args.clim) != 3:
        allcond_clim = dict(kind="value", lims=np.array((1.09, 2, 4)))
        percond_clim = dict(kind="value", lims=np.array((1.5, 2.5, 3)))
    elif len(args.clim) == 3:
        lb, mv, ub = args.clim
        allcond_clim = None
        percond_clim = None
    else:
        lb, mv, ub = (55, 85, 99.9)
        allcond_clim = None
        percond_clim = None

    brain_kwargs = dict(
        hemi="split",
        surface="pial",
        views=["lat", "med", "ven", "dor"],
        # cortex="bone",
        smoothing_steps="nearest",
        size=(1080, 680),
        subject="fsaverage",
        subjects_dir=args.fs_sub_dir,
        view_layout="horizontal",
    )

    picked_points = {"lh": [21571, 156056], "rh": [114112, 97289], "vol": []}

    title_taskpart = ("One-word with", "Two-word with")
    title_tagpart = {
        "ONEWORD": {"F1": "6 Hz stimulus", "F2": "7 Hz stimulus"},
        "TWOWORD": {
            "F1LEFT": "6 Hz stimulus on left side",
            "F1RIGHT": "7 Hz stimulus on left side",
        },
    }
    title_allcond = ": All conditions together"
    title_condpart = {
        "ONEWORD": {"WORD": "Word stimuli", "NONWORD": "Non-word stimuli"},
        "TWOWORD": {
            "PHRASE": "Valid phrases",
            "NONPHRASE": "Non-phrase pairs",
            "NONWORD": "Pair with non-word",
        },
    }

    f_offset = (1 / 28.333333) * args.freq_bin_offset
    f_idx_offset = args.freq_bin_offset

    freqs = pd.read_pickle(
        args.bids_root / "derivatives/mne-bids-pipeline/sub-02/ses-01/meg/"
        "sub-02_ses-01_task-syntaxIM_desc-morphFSAVGtwoword_allcondSNRsource.pkl"
    )["F1LEFT"]["freqs"]

    for task in tasks:
        oneword = True if task == "ONEWORD" else False
        tasktags = ow_tags if oneword else tw_tags

        allcond_taskpath = savepath / f"allcond/{task.lower()}"
        allcond_taskpath.mkdir(parents=True, exist_ok=True)

        percond_taskpath = savepath / f"percond/{task.lower()}/"
        percond_taskpath.mkdir(parents=True, exist_ok=True)
        for tag in tasktags:
            stc = mne.read_source_estimate(
                stc_root / f"allcond/{task.lower()}/grand_mean_snr_{tag}-lh.stc"
            )
            data = stc.data.copy()
            # First all-conditions-combined plots
            if oneword:
                plotfreqs = (tag_f[0],) if tag == "F1" else (tag_f[1],)
            else:
                plotfreqs = (tag_f[0], tag_f[1], tag_f[1] - tag_f[0], tag_f[1] + tag_f[0])
            for f in plotfreqs:
                curr_title = (
                    title_taskpart[int(not oneword)] + title_tagpart[task][tag] + title_allcond
                )
                stc.data = data
                fidx = np.abs(freqs - f).argmin() + f_idx_offset
                if allcond_clim is None:
                    currclim = get_clim_pct(data, fidx, lb, mv, ub)
                else:
                    currclim = allcond_clim

                brain = stc.plot(
                    initial_time=f + f_offset,
                    clim=currclim,
                    title=curr_title,
                    **brain_kwargs,
                )
                pick_points(brain, picked_points)
                brain.toggle_interface()
                brain.save_image(allcond_taskpath / f"brain_grand_mean_snr_{tag}_{int(f):d}Hz.png")
                brain.close()
                del brain

            # Then per-condition plots
            for cond in ow_conds if oneword else tw_conds:
                stc = mne.read_source_estimate(
                    stc_root / f"percond/{task.lower()}/grand_mean_snr_{cond}-{tag}-lh.stc"
                )
                data = stc.data.copy()
                for f in plotfreqs:
                    curr_title = (
                        title_taskpart[int(not oneword)]
                        + title_tagpart[task][tag]
                        + title_condpart[task][cond]
                    )
                    stc.data = data

                    fidx = np.abs(freqs - f).argmin() + f_idx_offset
                    if allcond_clim is None:
                        currclim = get_clim_pct(data, fidx, lb, mv, ub)
                    else:
                        currclim = percond_clim

                    brain = stc.plot(
                        initial_time=f + f_offset,
                        clim=currclim,
                        title=curr_title,
                        **brain_kwargs,
                    )
                    pick_points(brain, picked_points)
                    brain.toggle_interface()
                    brain.save_image(
                        percond_taskpath / f"brain_grand_mean_snr_{cond}-{tag}_{int(f):d}Hz.png"
                    )
                    brain.close()
                    del brain
