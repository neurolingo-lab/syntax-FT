from pathlib import Path

import mne
import mne_bids as mnb
import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm

import intermodulation.plot as imp
from intermodulation.analysis_spec import make_parser, psd_plot_freqs

if __name__ == "__main__":
    parser = make_parser(group_level=True, plots=True)
    parser.description = (
        "Pipeline script to plot sensor space signal-to-noise data averaged across all subjects."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default="/srv/beegfs/scratch/users/g/gercek/syntax_im/results",
        help="Root directory for group mean data. Must have a folder `sub-all` generated by "
        "`06_group_means_source` with associated source time course files.",
    )
    parser.add_argument(
        "--meg-true-samprate",
        type=float,
        default=1000.49,
        help="The MEGIN Elektra at FCBG is known to sample slightly faster than advertised, which "
        "affects the true frequencies observed in the FFT and will lead to a slightly lower freq "
        "than in reality. This allows for us to correct. Specify w.r.t. a true 1000 Hz rate.",
    )
    args = parser.parse_args()

    # STORAGE LOCATIONS
    sensor_info_sub = "05"
    rawsamp = mne.io.read_raw_fif(
        mnb.BIDSPath(
            subject=sensor_info_sub,
            session="01",
            task="syntaxIM",
            processing="clean",
            datatype="meg",
            suffix="raw",
            extension=".fif",
            root=args.bids_root / "derivatives/mne-bids-pipeline",
            check=False,  # Need to disable checking for derivatives
        )
    ).crop(0, 1.0, verbose="error")
    freqs = np.load(
        mnb.BIDSPath(
            subject=sensor_info_sub,
            session="01",
            task="syntaxIM",
            processing="clean",
            datatype="meg",
            suffix="allcondSNR",
            extension=".pkl",
            description="oneword",
            root=args.bids_root / "derivatives/mne-bids-pipeline",
            check=False,  # Need to disable checking for derivatives
        ),
        allow_pickle=True,
    )["F1"]["freqs"]

    allcond_data = args.results_dir / "sub-all/allcond"
    percond_data = args.results_dir / "sub-all/percond"

    plotpath = args.plotpath / "sub-all"

    plotpath.mkdir(parents=True, exist_ok=True)
    (plotpath / "allcond").mkdir(parents=True, exist_ok=True)
    (plotpath / "percond").mkdir(parents=True, exist_ok=True)

    samprate_correction = (2 * 1000) / (args.meg_true_samprate * 2)

    tag_f = (6, 7.05882353)

    tasks = ("ONEWORD", "TWOWORD")
    ow_tags = ("F1", "F2")
    tw_tags = ("F1LEFT", "F1RIGHT")
    ow_conds = ("WORD", "NONWORD")
    tw_conds = ("PHRASE", "NONPHRASE", "NONWORD")

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
    topofig_kw = dict(figsize=(8, 8), dpi=200)

    for task in tqdm(tasks, desc="Task"):
        oneword = True if task == "ONEWORD" else False
        taskname = "oneword" if oneword else "twoword"

        tasktags = ow_tags if oneword else tw_tags
        taskconds = ow_conds if oneword else tw_conds

        allcond_taskdata = allcond_data / task.lower()
        allcond_taskpath = plotpath / f"allcond/{task.lower()}"
        allcond_taskpath.mkdir(parents=True, exist_ok=True)

        percond_taskdata = percond_data / task.lower()
        percond_taskpath = plotpath / f"percond/{task.lower()}/"
        percond_taskpath.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(2, 2, figsize=(15, 11), sharex=True, sharey="row")
        for i, tag in tqdm(enumerate(tasktags), desc="Tag subplot", leave=False):
            mean_psd = np.load(
                allcond_taskdata / f"sensor_grand_mean_psd_{tag}.npy",
                allow_pickle=True,
            )
            mean_snr = np.load(
                allcond_taskdata / f"sensor_grand_mean_snr_{tag}.npy",
                allow_pickle=True,
            )
            ax = axes[:, i]
            if not oneword:
                # Vertical lines at tag frequencies and f2-f1, f1+f2 IMs
                tagfreq = [
                    7.05882353 - 6.0,
                    6.0,
                    7.05882353,
                    2 * 6,
                    6 + 7.05882353,
                    2 * 7.05882353,
                ]
            else:
                tagfreq = {"F1": 6.0, "F2": 7.05882353}[tag]
            titlestr = title_taskpart[int(not oneword)] + title_tagpart[task][tag] + title_allcond
            imp.plot_snr(
                mean_psd,
                mean_snr,
                freqs,
                fmin=psd_plot_freqs[0],
                fmax=psd_plot_freqs[1],
                fig=fig,
                axes=ax,
                titleannot=titlestr,
                tagfreq=tagfreq,
                plotpsd=True,
                annot_snr_peaks=True,
            )

            # Topomap plots
            topofig = imp.snr_topo(
                mean_snr,
                rawsamp.pick("data", exclude="bads"),
                freqs,
                fmin=psd_plot_freqs[0],
                fmax=psd_plot_freqs[1],
                ymin=0.0,
                ymax=8.0,
                vlines=[tagfreq] if oneword else tagfreq,
                fig_kwargs=topofig_kw,
                annot_max=True,
            )
            topofig.suptitle(titlestr + ": All conditions", color="w")
            topofig.savefig(allcond_taskpath / f"{taskname}_allcond_{tag}_snrtopo.pdf")
            plt.close(topofig)
        axes[1, 0].set_ylim([-0.5, 4.0])
        fig.savefig(plotpath / f"{taskname}_allcond_snr.pdf")
        plt.close(fig)

        ncond = len(taskconds) * 2
        fig, axes = plt.subplots(2, ncond, figsize=(ncond * 5, 11), sharex=True, sharey="row")
        for i, tag in tqdm(enumerate(tasktags), desc="Tag subplot", leave=False):
            for j, cond in tqdm(enumerate(taskconds), desc="Cond subplot", leave=False):
                colidx = i * len(taskconds) + j
                fulltag = f"{cond}-{tag}"
                psd = np.load(
                    percond_taskdata / f"sensor_grand_mean_psd_{fulltag}.npy",
                    allow_pickle=True,
                )
                snr = np.load(
                    percond_taskdata / f"sensor_grand_mean_snr_{fulltag}.npy",
                    allow_pickle=True,
                )
                if j == 0:
                    name = "oneword" if oneword else "twoword"
                else:
                    name = "twoword" if oneword else "oneword"
                if not oneword:
                    # Vertical lines at tag frequencies and f2-f1, f1+f2 IMs
                    tagfreq = [
                        7.05882353 - 6.0,
                        6.0,
                        7.05882353,
                        2 * 6,
                        6 + 7.05882353,
                        2 * 7.05882353,
                    ]
                else:
                    tagfreq = {"F1": 6.0, "F2": 7.05882353}[tag]
                titlestr = (
                    title_taskpart[int(not oneword)]
                    + title_condpart[task][cond]
                    + " with "
                    + title_tagpart[task][tag]
                )
                ax = axes[:, colidx]
                imp.plot_snr(
                    psd,
                    snr,
                    freqs,
                    fmin=psd_plot_freqs[0],
                    fmax=psd_plot_freqs[1],
                    fig=fig,
                    axes=ax,
                    titleannot=titlestr,
                    tagfreq=tagfreq,
                    plotpsd=True,
                    annot_snr_peaks=True,
                )
                topofig = imp.snr_topo(
                    snr,
                    rawsamp.pick("data", exclude="bads"),
                    freqs,
                    fmin=psd_plot_freqs[0],
                    fmax=psd_plot_freqs[1],
                    ymin=0.0,
                    ymax=8.0,
                    vlines=[tagfreq] if oneword else tagfreq,
                    fig_kwargs=topofig_kw,
                    annot_max=True,
                )
                topofig.suptitle(f"{taskname}: {tag} {cond} trials SNR", color="w")
                topofig.savefig(plotpath / f"{taskname}_{cond}_{tag}_snrtopo.pdf")
                plt.close(topofig)
        axes[1, 0].set_ylim([-0.5, 4.0])
        fig.suptitle(f"{taskname} SNR per condition", fontsize=16)
        fig.tight_layout()
        fig.savefig(plotpath / f"{taskname}_percond_snr.pdf")
