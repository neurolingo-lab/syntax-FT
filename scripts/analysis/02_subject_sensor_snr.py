import pickle

import mne
import mne_bids as mnb
from tqdm import tqdm

import intermodulation.analysis as ima
from intermodulation import analysis_spec, freqtag_spec

if __name__ == "__main__":
    parser = analysis_spec.make_parser()
    parser.description = """Pipeline script to compute sensor space signal-to-noise ratio (SNR) data
    for individual subjects in the frequency spectrum. This script will compute SNR for
    the oneword and twoword tasks, for all conditions combined and per condition."""

    parser.add_argument(
        "--cond-mean",
        action="store_true",
        help="Whether to average the evoked epochs prior to computing the PSD"
        "and SNR for a given condition. Will produce an additional description string in the "
        "saved files CONDMEAN.",
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
    snr_skip_neighbor_J = analysis_spec.noise_skip_neighbor_freqs
    snr_neighbor_K = analysis_spec.noise_n_neighbor_freqs

    psd_kwargs = analysis_spec.sensor_fft_pars.copy()
    psd_kwargs.update(
        n_fft=int(epochs.info["sfreq"] * (tmax - tmin)),
        tmin=tmin,
        tmax=tmax,
    )

    print("Computing SNR for oneword+twoword, per condition and all conditions...")
    if args.cond_mean:
        meanstr = "CONDMEAN"
    else:
        meanstr = ""
    owbase = f"sub-{args.subject}_ses-{args.session}_task-{args.task}_proc-{args.proc}_desc-{meanstr}oneword"
    twbase = f"sub-{args.subject}_ses-{args.session}_task-{args.task}_proc-{args.proc}_desc-{meanstr}twoword"
    allcond_spectra_ow = {"samp_epoch": epochs[0]}
    allcond_spectra_tw = {"samp_epoch": epochs[0]}
    percond_spectra_ow = {"samp_epoch": epochs[0]}
    percond_spectra_tw = {"samp_epoch": epochs[0]}
    for tag in tqdm(["F1", "F2"], desc="Processing tag sets"):
        twtag = "F1LEFT" if tag == "F1" else "F1RIGHT"
        if args.cond_mean:
            ow_ep = epochs[f"MINIBLOCK/ONEWORD/{tag}"].average()
            tw_ep = epochs[f"MINIBLOCK/TWOWORD/{twtag}"].average()
            meanstr = "CONDMEAN"
        else:
            ow_ep = epochs[f"MINIBLOCK/ONEWORD/{tag}"]
            tw_ep = epochs[f"MINIBLOCK/TWOWORD/{twtag}"]

        spectrum = ow_ep.compute_psd(exclude="bads", n_jobs=-1, verbose="error", **psd_kwargs)
        twspectrum = tw_ep.compute_psd(exclude="bads", n_jobs=-1, verbose="error", **psd_kwargs)
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
        for cond in tqdm(["WORD", "NONWORD"], desc=f"Processing OW {tag} conditions", leave=False):
            fulltag = f"ONEWORD/{cond}/{tag}"
            ow_ep = (
                epochs["MINIBLOCK/" + fulltag].average()
                if args.cond_mean
                else epochs["MINIBLOCK/" + fulltag]
            )
            spectrum = ow_ep.compute_psd(exclude="bads", n_jobs=-1, verbose="error", **psd_kwargs)
            psds, freqs = spectrum.get_data(return_freqs=True)
            snrs = ima.snr_spectrum(
                psds,
                noise_n_neighbor_freqs=snr_neighbor_K,
                noise_skip_neighbor_freqs=snr_skip_neighbor_J,
            )
            percond_spectra_ow[fulltag] = dict(psds=psds, freqs=freqs, snrs=snrs)
        for cond in tqdm(
            ["PHRASE", "NONPHRASE", "NONWORD"], desc="Processing TW conditions", leave=False
        ):
            fulltag = f"TWOWORD/{cond}/{twtag}"
            tw_ep = (
                epochs["MINIBLOCK/" + fulltag].average()
                if args.cond_mean
                else epochs["MINIBLOCK/" + fulltag]
            )
            spectrum = tw_ep.compute_psd(exclude="bads", n_jobs=-1, verbose="error", **psd_kwargs)
            psds, freqs = spectrum.get_data(return_freqs=True)
            snrs = ima.snr_spectrum(
                psds,
                noise_n_neighbor_freqs=snr_neighbor_K,
                noise_skip_neighbor_freqs=snr_skip_neighbor_J,
            )
            percond_spectra_tw[fulltag] = dict(psds=psds, freqs=freqs, snrs=snrs)
    print("Done.")
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
