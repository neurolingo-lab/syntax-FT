import matplotlib.pyplot as plt
import mne_bids as mnb
import pandas as pd

import intermodulation.plot as imp
from intermodulation import analysis_spec

if __name__ == "__main__":
    parser = analysis_spec.make_parser(plots=True)

    args = parser.parse_args()

    # Handle processing tag and path to derivatives for subject
    processing = None if args.proc == "raw" else args.proc
    procdir = "raw" if args.proc == "raw" else f"proc-{args.proc}"

    derivatives_root = args.bids_root / "derivatives/mne-bids-pipeline"
    procpath = derivatives_root / f"sub-{args.subject}/ses-{args.session}/meg/"
    if not procpath.exists():
        raise FileNotFoundError(
            f"Could not find derivatives directory for subject {args.subject}, "
            f"session {args.session}!"
        )

    # Create appropriate plotting directories if they don't exist
    args.plotpath.mkdir(parents=True, exist_ok=True)
    plotpath = args.plotpath / f"sub-{args.subject}" / procdir
    plotpath.mkdir(parents=True, exist_ok=True)
    print(f"Saving plots to {plotpath}")

    # Generate BIDS path for SNR and PSDs
    base_bidspath = mnb.BIDSPath(
        subject=args.subject,
        session=args.session,
        task=args.task,
        processing=processing,
        suffix=None,
        extension=".pkl",
        root=derivatives_root,
        check=False,  # Need to disable checking for derivatives
    )
    ow_base_path = base_bidspath.copy().update(desc="oneword")
    tw_base_path = base_bidspath.copy().update(desc="twoword")

    print("Plotting SNR and SNR topos for oneword+twoword, all conditions combined...")
    plot_freqs = (1, 15)
    topofig_kw = dict(figsize=(8, 8), dpi=200)

    allcond_spectra_ow = pd.read_pickle(ow_base_path.update(suffix="allcondSNR").fpath)
    allcond_spectra_tw = pd.read_pickle(tw_base_path.update(suffix="allcondSNR").fpath)
    epochs = allcond_spectra_ow["samp_epoch"].copy()

    for name, spectra in {"oneword": allcond_spectra_ow, "twoword": allcond_spectra_tw}.items():
        fig, axes = plt.subplots(2, 2, figsize=(15, 11), sharex=True, sharey="row")
        for i, (tag, data) in enumerate(spectra.items()):
            ax = axes[:, i]
            if name == "twoword":
                # Vertical lines at tag frequencies and f2-f1, f1+f2 IMs
                tagfreq = [
                    7.05882353 - 6.0,
                    6.0,
                    7.05882353,
                    2 * 6,
                    6 + 7.05882353,
                    2 * 7.05882353,
                ]
                titlestr = f"{tag} Two-Word SNR"
            else:
                tagfreq = {"F1": 6.0, "F2": 7.05882353}[tag]
                titlestr = f"{tag} One-Word SNR"
            imp.plot_snr(
                data["psds"],
                data["snrs"],
                data["freqs"],
                fmin=plot_freqs[0],
                fmax=plot_freqs[1],
                fig=fig,
                axes=ax,
                titleannot=titlestr,
                tagfreq=tagfreq,
                plotpsd=True,
            )
            # Topomap plots
            topofig = imp.snr_topo(
                data["snrs"].mean(axis=0),
                epochs.pick("data", exclude="bads"),
                data["freqs"],
                fmin=plot_freqs[0],
                fmax=plot_freqs[1],
                ymin=0.0,
                ymax=8.0,
                vlines=[tagfreq] if name == "oneword" else tagfreq,
                fig_kwargs=topofig_kw,
            )
            topofig.suptitle(titlestr + ": All conditions", color="w")
            topofig.savefig(
                plotpath
                / f"sub-{args.subject}_ses-{args.session}_task-{args.task}_{name}_allconds_{tag}_snrtopo.pdf"
            )
            plt.close(topofig)
        axes[1, 0].set_ylim([-0.5, 4.0])
        fig.savefig(
            plotpath
            / f"sub-{args.subject}_ses-{args.session}_task-{args.task}_{name}_allconds_snr.pdf"
        )
        plt.close(fig)
    print("Done.")
    del allcond_spectra_ow, allcond_spectra_tw

    percond_spectra_ow = pd.read_pickle(ow_base_path.update(suffix="percondSNR").fpath)
    percond_spectra_tw = pd.read_pickle(tw_base_path.update(suffix="percondSNR").fpath)

    print("Plotting SNR and SNR topos for oneword+twoword, per condition...")
    for name, spectra in {"oneword": percond_spectra_ow, "twoword": percond_spectra_tw}.items():
        ncond = len(spectra.keys())
        fig, axes = plt.subplots(2, ncond, figsize=(ncond * 5, 11), sharex=True, sharey="row")
        for i, (tag, data) in enumerate(spectra.items()):
            cond = tag.split("/")[1]
            freq = tag.split("/")[-1]
            if name == "twoword":
                # Vertical lines at tag frequencies and f2-f1, f1+f2 IMs
                tagfreq = [
                    7.05882353 - 6.0,
                    6.0,
                    7.05882353,
                    2 * 6,
                    6 + 7.05882353,
                    2 * 7.05882353,
                ]
                titlestr = f"{cond} SNR"
            else:
                tagfreq = {"F1": 6.0, "F2": 7.05882353}[freq]
                titlestr = f"{cond} SNR"
            ax = axes[:, i]
            imp.plot_snr(
                data["psds"],
                data["snrs"],
                data["freqs"],
                fmin=plot_freqs[0],
                fmax=plot_freqs[1],
                fig=fig,
                axes=ax,
                titleannot=titlestr,
                tagfreq=tagfreq,
                plotpsd=True,
            )
            topofig = imp.snr_topo(
                data["snrs"].mean(axis=0),
                epochs.pick("data", exclude="bads"),
                data["freqs"],
                fmin=plot_freqs[0],
                fmax=plot_freqs[1],
                ymin=0.0,
                ymax=8.0,
                vlines=[tagfreq] if name == "oneword" else tagfreq,
                fig_kwargs=topofig_kw,
            )
            topofig.suptitle(f"{name}: {freq} {cond} trials SNR", color="w")
            topofig.savefig(
                plotpath
                / f"sub-{args.subject}_ses-{args.session}_task-{args.task}_{name}_{cond}_{freq}_snrtopo.pdf"
            )
            plt.close(topofig)
        axes[1, 0].set_ylim([-0.5, 4.0])
        fig.suptitle(f"{name} SNR per condition", fontsize=16)
        fig.tight_layout()
        fig.savefig(
            plotpath
            / f"sub-{args.subject}_ses-{args.session}_task-{args.task}_{name}_percond_snr.pdf"
        )
    print("Done.")
