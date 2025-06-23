import pickle
from pathlib import Path

import mne
import mne_bids as mnb

import intermodulation.analysis as ima
import intermodulation.freqtag_spec as spec


def source_psd_epochs_avg(epochs, psd_kwargs):
    psdgen = mne.minimum_norm.compute_source_psd_epochs(
        epochs.copy().pick("data", exclude="bads"), return_generator=True, **psd_kwargs
    )

    psdavg = 0
    for i, stc in enumerate(psdgen):
        if i == 0:
            plotstc = stc.copy()
        psdavg += stc.data
    psdavg /= i + 1
    freqs = plotstc.times
    return psdavg, freqs, plotstc


def morph_psd_and_snr(plotstc: mne.SourceEstimate, psdavg, snrs):
    orig_stc = plotstc.copy()
    orig_stc.data = snrs
    plotstc = morph.apply(orig_stc)  # Apply the morph to the SNRs first
    snrs = plotstc.data

    orig_stc.data = psdavg  # Then apply to the PSD average itself
    tmp_stc = morph.apply(orig_stc)
    psdavg = tmp_stc.data
    return psdavg, snrs, plotstc


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Pipeline script to compute source space signal-to-noise data "
        "for individual subjects in the frequency spectrum."
    )
    parser.add_argument(
        "--proc",
        type=str,
        default="raw",
        help="Processing type: raw, sss, filt, or clean",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default="02",
        help="Subject ID",
    )
    parser.add_argument(
        "--session",
        type=str,
        default="01",
        help="Session ID",
    )
    parser.add_argument(
        "--bids_root",
        type=Path,
        default="/srv/beegfs/scratch/users/g/gercek/syntax_im/syntax_dataset",
        help="Root directory for BIDS dataset",
    )
    parser.add_argument(
        "--inverse-method",
        type=str,
        default="MNE",
        help="The inverse method used to compute the source PSD. Shoudl match whichever method was"
        " used to compute the inverse solution.",
    )
    parser.add_argument(
        "--morph-fsaverage",
        action="store_true",
        help="Whether or not the subject source space should be morphed to match the fsaverage "
        "template provided by freesurfer, to provide a common target for all subjects.",
    )
    parser.add_argument(
        "--src-spacing",
        type=str,
        default=None,
        help="The source space spacing to use for morphing to fsaverage, if multiple are "
        "available. If not provided, will use the file present in the freesurfer `bem` directory "
        "for the subject/session, provided only one source space file is present.",
    )
    parser.add_argument(
        "--plotpath",
        type=Path,
        default="/srv/beegfs/scratch/users/g/gercek/syntax_im/results/",
        help="Directory in which to save SNR plots, if any",
    )
    parser.add_argument(
        "--snr-skip",
        type=int,
        default=2,
        help="Number of frequency bins to skip on either side of a frequency bin for SNR "
        "computation. By default 2 bin on each side.",
    )
    parser.add_argument(
        "--snr-neighbors",
        type=int,
        default=12,
        help="Number of neighboring frequency bins to consider when computing the signal-to-noise "
        "ratio for a given frequency bin. This does not include the skipped bins immediately "
        "adjacent.",
    )
    args = parser.parse_args()

    # STORAGE LOCATIONS
    bids_root = args.bids_root
    savepath = args.plotpath / f"sub-{args.subject}"

    savepath.mkdir(parents=True, exist_ok=True)

    derivatives_root = bids_root / "derivatives/mne-bids-pipeline"
    fs_root = bids_root / "derivatives/freesurfer"
    fs_sub = f"sub-{args.subject}_ses-{args.session}"

    procpath = derivatives_root / f"sub-{args.subject}/ses-{args.session}/meg/"
    if not procpath.exists():
        raise FileNotFoundError(
            f"Could not find derivatives directory for subject {args.subject}, "
            f"session {args.session}!"
        )

    processing = "clean"

    raw_bidspath = mnb.BIDSPath(
        subject=args.subject,
        session=args.session,
        task="syntaxIM",
        processing=processing,
        split="01" if processing in ("sss", "filt", None) else None,
        datatype="meg",
        suffix="raw" if processing is not None else None,
        extension=".fif",
        root=derivatives_root if processing is not None else bids_root,
        check=False,  # Need to disable checking for derivatives
    )

    trans_bidspath = raw_bidspath.copy().update(split=None, processing=None, suffix="trans")
    fs_path = derivatives_root.parent / "freesurfer" / f"sub-{args.subject}"
    src_path = fs_path / f"bem/sub-{args.subject}-oct6-src.fif"
    bem_path = fs_path / f"bem/sub-{args.subject}-5120-bem-sol.fif"

    trans = mne.read_trans(trans_bidspath.fpath)
    src = mne.read_source_spaces(src_path)
    bem = mne.read_bem_solution(bem_path)

    fwd_bidspath = trans_bidspath.copy().update(suffix="fwd")

    raw = mne.io.read_raw_fif(raw_bidspath.fpath)  # ima.miniblock_events(raw)
    try:
        fwd = mne.read_forward_solution(fwd_bidspath.fpath)
    except FileNotFoundError:
        print(f"Forward solution not found for subject {args.subject}, session {args.session}!")
        print("Will attempt to recompute forward solution.")

        fwd = mne.make_forward_solution(
            raw.info,
            trans=trans,
            src=src,
            bem=bem,
            mindist=5,
        )
        mne.write_forward_solution(fwd_bidspath.fpath, fwd, overwrite=True)

    cov_bidspath = raw_bidspath.copy().update(
        split=None,
        suffix="cov",
        task="noise",
    )
    inv_bidspath = trans_bidspath.copy().update(suffix="inv")
    cov = mne.read_cov(cov_bidspath)
    try:
        inv = mne.minimum_norm.read_inverse_operator(inv_bidspath.fpath)
    except FileNotFoundError:
        print(f"Inverse solution no found for subject {args.subject}, session {args.session}!")
        print("Will attempt to recompute inverse solution")
        inv = mne.minimum_norm.make_inverse_operator(
            raw.info,
            fwd,
            cov,
            loose="auto",
            rank="info",
        )
        mne.minimum_norm.write_inverse_operator(inv_bidspath.fpath, inv, overwrite=True)

    if args.morph_fsaverage:
        src_bidspath = fs_root / f"{fs_sub}/bem/"
        if args.src_spacing is not None:
            src_bidspath = src_bidspath.mtach(f"*-{args.src_spacing}-src.fif")
            if not src_bidspath:
                raise FileNotFoundError(f"No source file with spacing {args.src_spacing} found!")
            if len(src_bidspath) > 1:
                raise ValueError(
                    f"More than one source file with spacing {args.src_spacing} found!\n"
                    f"Found : {src_bidspath}"
                )
        elif not src_bidspath.match("*-src.fif"):
            raise FileNotFoundError("No source file found!")
        elif len(src_bidspath.match("*-src.fif")) > 1:
            raise ValueError(
                f"Multiple source files found!\n Found: {src_bidspath}\n Please choose a"
                " spacing to use via `--src-spacing`."
            )

        src = mne.read_source_spaces(src_bidspath[0])
        morph = mne.compute_source_morph(
            src,
            subject_from=fs_sub,
            subject_to="fsaverage",
            subjects_dir=fs_root,
        )
        morphstr = "morphFSAVG"
    else:
        morphstr = ""

    events, evdict = mne.events_from_annotations(raw)
    keepev = {k: v for k, v in evdict.items() if k.split("/")[0] == "MINIBLOCK"}
    epochs = mne.Epochs(raw, event_id=keepev, tmin=-0.2, tmax=21.0, picks="all", preload=True)

    del raw
    if epochs.info["sfreq"] >= 2000:
        epochs.decimate(4)
    if epochs.info["sfreq"] >= 1000:
        epochs.decimate(2)

    # Compute source space PSD and then SNR
    # Global parameters for different FFTs
    minidur = spec.WORD_DUR * spec.MINIBLOCK_LEN

    fmin = 0.1
    fmax = 140.0
    tmin = 0.1
    tmax = 21.0
    tmax = minidur
    snr_skip_neighbor_J = args.snr_skip
    snr_neighbor_K = args.snr_neighbors
    psd_kwargs = dict(
        inverse_operator=inv,
        lambda2=1 / 9.0,
        method="MNE",
        n_fft=int(epochs.info["sfreq"] * (tmax - tmin)),
        overlap=0.0,
        tmin=tmin,
        tmax=tmax,
        fmin=fmin,
        fmax=fmax,
        nave=1,
        bandwidth="hann",
        low_bias=True,
        n_jobs=-1,
    )

    print("Computing SNR for oneword+twoword, per condition and all conditions...")
    owbase = f"sub-{args.subject}_ses-{args.session}_task-syntaxIM_desc-{morphstr}oneword"
    twbase = f"sub-{args.subject}_ses-{args.session}_task-syntaxIM_desc-{morphstr}twoword"
    allcond_spectra_ow = {}
    allcond_spectra_tw = {}
    percond_spectra_ow = {}
    percond_spectra_tw = {}
    for tag in ["F1", "F2"]:
        twtag = "F1LEFT" if tag == "F1" else "F1RIGHT"
        for task, allcond, percond in [
            ("ONEWORD", allcond_spectra_ow, percond_spectra_ow),
            ("TWOWORD", allcond_spectra_tw, percond_spectra_tw),
        ]:
            oneword = task == "ONEWORD"
            tasktag = tag if oneword else twtag
            all_label = f"{task}/{tasktag}"
            psdavg, freqs, plotstc = source_psd_epochs_avg(
                epochs[f"MINIBLOCK/{all_label}"], psd_kwargs
            )
            snrs = ima.snr_spectrum(
                psdavg,
                noise_n_neighbor_freqs=snr_neighbor_K,
                noise_skip_neighbor_freqs=snr_skip_neighbor_J,
            )
            if args.morph_fsaverage:  # If requested, morph both the PSD and SNR into fsavg space
                psdavg, snrs, plotstc = morph_psd_and_snr(plotstc, psdavg, snrs)

            allcond[tasktag] = dict(psd=psdavg, freqs=freqs, snrs=snrs, stc=plotstc)

            taskconds = ["WORD", "NONWORD"] if oneword else ["PHRASE", "NONPHRASE", "NONWORD"]
            for cond in taskconds:
                cond_label = f"MINIBLOCK/{task}/{cond}/{tasktag}"
                psdavg, freqs, plotstc = source_psd_epochs_avg(epochs[cond_label], psd_kwargs)
                snrs = ima.snr_spectrum(
                    psdavg,
                    noise_n_neighbor_freqs=snr_neighbor_K,
                    noise_skip_neighbor_freqs=snr_skip_neighbor_J,
                )
                if args.morph_fsaverage:
                    psdavg, snrs, plotstc = morph_psd_and_snr(plotstc, psdavg, snrs)

                percond[f"{cond}/{tasktag}"] = dict(
                    psd=psdavg, freqs=freqs, snrs=snrs, stc=plotstc
                )
    print("Done.")
    print(f"Saving data to {procpath} ...")
    with open(
        procpath / f"{owbase}_allcondSNRsource.pkl",
        "wb",
    ) as f:
        pickle.dump(allcond_spectra_ow, f)
    with open(
        procpath / f"{twbase}_allcondSNRsource.pkl",
        "wb",
    ) as f:
        pickle.dump(allcond_spectra_tw, f)
    with open(
        procpath / f"{owbase}_percondSNRsource.pkl",
        "wb",
    ) as f:
        pickle.dump(percond_spectra_ow, f)
    with open(
        procpath / f"{twbase}_percondSNRsource.pkl",
        "wb",
    ) as f:
        pickle.dump(percond_spectra_tw, f)

    print("Done.\n")
