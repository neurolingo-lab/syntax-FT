import pickle
from copy import deepcopy

import mne
import mne_bids as mnb

import intermodulation.analysis as ima
import intermodulation.freqtag_spec as spec
from intermodulation import analysis_spec


def source_psd_epochs_avg(epochs, psd_kwargs: dict, subject: str, session: str):
    evoked = epochs.average()
    kwargs = deepcopy(psd_kwargs)
    stc = mne.minimum_norm.apply_inverse(
        evoked,
        inverse_operator=kwargs.pop("inverse_operator"),
        lambda2=kwargs.pop("lambda2"),
        method=kwargs.pop("method"),
    )
    psdavg, freqs = mne.time_frequency.psd_array_welch(stc.data, **kwargs)
    fs_sub = f"sub-{subject}_ses-{session}" if subject != "fsaverage" else subject
    plotstc = mne.SourceEstimate(
        data=psdavg,
        vertices=stc.vertices,
        tmin=freqs.min(),
        tstep=freqs[1] - freqs[0],
        subject=fs_sub,
    )
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
    parser = analysis_spec.make_parser()
    parser.description = (
        "Pipeline script to compute source space signal-to-noise data "
        "for individual subjects in the frequency spectrum."
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

    args = parser.parse_args()

    # STORAGE LOCATIONS
    bids_root = args.bids_root

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
        task=args.task,
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

    src_path = fs_root / f"{fs_sub}/bem/"
    bem_path = fs_root / f"{fs_sub}/bem/"
    if args.src_spacing is not None:
        src_path = list(src_path.glob(f"sub*-{args.src_spacing}-src.fif"))
        if not src_path:
            raise FileNotFoundError(f"No source file with spacing {args.src_spacing} found!")
        if len(src_path) > 1:
            raise ValueError(
                f"More than one source file with spacing {args.src_spacing} found!\n"
                f"Found : {src_path}"
            )
        src_path = src_path[0]
    elif not list(src_path.glob("sub*-src.fif")):
        raise FileNotFoundError("No source file found!")
    elif len(list(src_path.glob("sub*-src.fif"))) > 1:
        raise ValueError(
            f"Multiple source files found!\n Found: {src_path}\n Please choose a"
            " spacing to use via `--src-spacing`."
        )
    else:
        src_path = list(src_path.glob("sub*-src.fif"))[0]

    if not bem_path.glob("sub*-bem-sol.fif"):
        raise FileNotFoundError("No BEM solution file found!")
    elif len(list(bem_path.glob("sub*-bem-sol.fif"))) > 1:
        raise NotImplementedError(
            f"Multiple BEM solution files found!\n Found: {bem_path}\n I will eventually work out"
            " how to match bem numbers to `--src-spacing`."
        )
    else:
        bem_path = list(bem_path.glob("sub*-bem-sol.fif"))[0]

    src = mne.read_source_spaces(src_path)
    bem = mne.read_bem_solution(bem_path)

    trans = mne.read_trans(trans_bidspath.fpath)
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
        fsavg_src = mne.read_source_spaces(fs_root / "fsaverage/bem/fsaverage-ico-5-src.fif")
        morph = mne.compute_source_morph(
            fwd["src"],
            subject_from=fs_sub,
            subject_to="fsaverage",
            subjects_dir=fs_root,
            src_to=fsavg_src,
        )
        morphstr = "morphFSAVG"
    else:
        morphstr = ""

    minidur = spec.WORD_DUR * spec.MINIBLOCK_LEN

    events, evdict = mne.events_from_annotations(raw)
    keepev = {k: v for k, v in evdict.items() if k.split("/")[0] == "MINIBLOCK"}
    epochs = mne.Epochs(raw, event_id=keepev, tmin=-0.2, tmax=minidur, picks="all", preload=True)

    del raw
    if epochs.info["sfreq"] >= 2000:
        epochs.decimate(4)
    elif epochs.info["sfreq"] >= 1000:
        epochs.decimate(2)
    sfreq = epochs.info["sfreq"]

    # Compute source space PSD and then SNR
    # Global parameters for different FFTs
    tmin = 0.0
    tmax = minidur

    snr_skip_neighbor_J = analysis_spec.noise_skip_neighbor_freqs
    snr_neighbor_K = analysis_spec.noise_n_neighbor_freqs
    psd_kwargs = analysis_spec.source_fft_pars.copy()
    psd_kwargs.update(
        dict(
            inverse_operator=inv,
            sfreq=sfreq,
            n_fft=int(epochs.info["sfreq"] * (tmax - tmin)),
            n_jobs=-1,
        )
    )

    print("Computing SNR for oneword+twoword, per condition and all conditions...")
    savesub = "fsaverage" if args.morph_fsaverage else args.subject
    owbase = f"sub-{args.subject}_ses-{args.session}_task-{args.task}_desc-{morphstr}oneword"
    twbase = f"sub-{args.subject}_ses-{args.session}_task-{args.task}_desc-{morphstr}twoword"
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
                epochs[f"MINIBLOCK/{all_label}"], psd_kwargs, savesub, args.session
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
                psdavg, freqs, plotstc = source_psd_epochs_avg(
                    epochs[cond_label], psd_kwargs, savesub, args.session
                )
                print(psdavg.shape, freqs.shape, plotstc.data.shape, plotstc.times.shape)
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
