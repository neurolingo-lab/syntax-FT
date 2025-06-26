import pickle

import mne
import mne_bids as mnb

import intermodulation.analysis as ima
from intermodulation import analysis_spec, freqtag_spec

if __name__ == "__main__":
    parser = analysis_spec.make_parser()

    parser.add_argument(
        "--save-deriv",
        action="store_true",
        help="Whether the data should be stored in the BIDS derivatives directory once saved. "
        "Outputs will be saved to the 'mne-bids-pipeline' directory under the appropriate subject "
        "and session label, named as e.g. "
        "`sub-XX_ses-XX_task-syntaxIM_proc-PROC_desc-[oneword/twoword]_allcondSNR.pkl",
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

    processing = None if args.proc == "raw" else args.proc
    procdir = "raw" if args.proc == "raw" else f"proc-{args.proc}"

    # STORAGE LOCATIONS
    derivatives_root = args.bids_root / "derivatives/mne-bids-pipeline"
    procpath = derivatives_root / f"sub-{args.subject}/ses-{args.session}/meg/"
    if not procpath.exists():
        raise FileNotFoundError(
            f"Could not find derivatives directory for subject {args.subject}, "
            f"session {args.session}!"
        )

    args.plotpath.mkdir(parents=True, exist_ok=True)
    plotpath = args.plotpath / f"sub-{args.subject}" / procdir
    plotpath.mkdir(parents=True, exist_ok=True)

    raw_bidspath = mnb.BIDSPath(
        subject=args.subject,
        session=args.session,
        task=args.task,
        processing=processing,
        split="01" if processing in ("sss", "filt", None) else None,
        datatype="meg",
        suffix="raw" if processing is not None else None,
        extension=".fif",
        root=derivatives_root if processing is not None else args.bids_root,
        check=False,  # Need to disable checking for derivatives
    )

    minidur = freqtag_spec.WORD_DUR * freqtag_spec.MINIBLOCK_LEN

    try:
        raw = mne.io.read_raw_fif(raw_bidspath.fpath, verbose=False)
    except FileNotFoundError:
        try:
            raw = mne.io.read_raw_fif(raw_bidspath.copy().update(split=None).fpath, verbose=False)
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find the file {raw_bidspath.fpath}! Please check.")

    events, evdict = mne.events_from_annotations(raw)
    keepev = {k: v for k, v in evdict.items() if k.split("/")[0] == "MINIBLOCK"}
    print("Raw sampled at ", raw.info["sfreq"])
    # if raw.info["sfreq"] == 2000:
    #     decim = 4
    #     print("Decimating to 500Hz from 2000Hz")
    # else:
    #     decim = 1

    epochs = mne.Epochs(raw, event_id=keepev, tmin=-0.2, tmax=minidur, picks="all", verbose=False)
    epochs.load_data()
    del raw

    # Global parameters for different FFTs, using the common set from analysis spec
    tmin = 0.0
    tmax = minidur
    snr_skip_neighbor_J = args.snr_skip
    snr_neighbor_K = args.snr_neighbors

    psd_kwargs = analysis_spec.sensor_fft_pars.copy()
    psd_kwargs.update(
        n_fft=int(epochs.info["sfreq"] * (tmax - tmin)),
        tmin=tmin,
        tmax=tmax,
    )

    print("Computing SNR for oneword+twoword, per condition and all conditions...")
    owbase = (
        f"sub-{args.subject}_ses-{args.session}_task-{args.task}_proc-{args.proc}_desc-oneword"
    )
    twbase = (
        f"sub-{args.subject}_ses-{args.session}_task-{args.task}_proc-{args.proc}_desc-twoword"
    )
    allcond_spectra_ow = {"samp_epoch": epochs[0]}
    allcond_spectra_tw = {"samp_epoch": epochs[0]}
    percond_spectra_ow = {"samp_epoch": epochs[0]}
    percond_spectra_tw = {"samp_epoch": epochs[0]}
    for tag in ["F1", "F2"]:
        twtag = "F1LEFT" if tag == "F1" else "F1RIGHT"
        spectrum = epochs[f"MINIBLOCK/ONEWORD/{tag}"].compute_psd(
            exclude="bads", n_jobs=-1, verbose=False, **psd_kwargs
        )
        twspectrum = epochs[f"MINIBLOCK/TWOWORD/{twtag}"].compute_psd(
            exclude="bads", n_jobs=-1, verbose=False, **psd_kwargs
        )
        psds, freqs = spectrum.get_data(return_freqs=True)
        twpsds, twfreqs = twspectrum.get_data(return_freqs=True)
        snrs = ima.snr_spectrum(
            psds,
            noise_n_neighbor_freqs=snr_neighbor_K,
            noise_skip_neighbor_freqs=snr_skip_neighbor_J,
        )
        twsnrs = ima.snr_spectrum(
            twpsds,
            noise_n_neighbor_freqs=snr_neighbor_K,
            noise_skip_neighbor_freqs=snr_skip_neighbor_J,
        )
        allcond_spectra_ow[tag] = dict(psds=psds, freqs=freqs, snrs=snrs)
        allcond_spectra_tw[twtag] = dict(psds=twpsds, freqs=twfreqs, snrs=twsnrs)
        for cond in ["WORD", "NONWORD"]:
            fulltag = f"ONEWORD/{cond}/{tag}"
            spectrum = epochs["MINIBLOCK/" + fulltag].compute_psd(
                exclude="bads", n_jobs=-1, **psd_kwargs
            )
            psds, freqs = spectrum.get_data(return_freqs=True)
            snrs = ima.snr_spectrum(
                psds,
                noise_n_neighbor_freqs=snr_neighbor_K,
                noise_skip_neighbor_freqs=snr_skip_neighbor_J,
            )
            percond_spectra_ow[fulltag] = dict(psds=psds, freqs=freqs, snrs=snrs)
        for cond in ["PHRASE", "NONPHRASE", "NONWORD"]:
            fulltag = f"TWOWORD/{cond}/{twtag}"
            spectrum = epochs["MINIBLOCK/" + fulltag].compute_psd(
                exclude="bads", n_jobs=-1, **psd_kwargs
            )
            psds, freqs = spectrum.get_data(return_freqs=True)
            snrs = ima.snr_spectrum(
                psds,
                noise_n_neighbor_freqs=snr_neighbor_K,
                noise_skip_neighbor_freqs=snr_skip_neighbor_J,
            )
            percond_spectra_tw[fulltag] = dict(psds=psds, freqs=freqs, snrs=snrs)
    print("Done.")
    if args.save_deriv:
        print(f"Saving data to {procpath} ...")
        with open(
            procpath / f"{owbase}_allcondSNR.pkl",
            "wb",
        ) as f:
            pickle.dump(allcond_spectra_ow, f)
        with open(
            procpath / f"{twbase}_allcondSNR.pkl",
            "wb",
        ) as f:
            pickle.dump(allcond_spectra_tw, f)
        with open(
            procpath / f"{owbase}_percondSNR.pkl",
            "wb",
        ) as f:
            pickle.dump(percond_spectra_ow, f)
        with open(
            procpath / f"{twbase}_percondSNR.pkl",
            "wb",
        ) as f:
            pickle.dump(percond_spectra_tw, f)

        print("Done.\n")
