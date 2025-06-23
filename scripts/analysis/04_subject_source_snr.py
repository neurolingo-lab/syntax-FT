from pathlib import Path

import mne
import mne_bids as mnb

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
    inv = mne.minimum_norm.make_inverse_operator(
        raw.info,
        fwd,
        cov,
        loose="auto",
        rank="info",
    )
    mne.minimum_norm.write_inverse_operator(inv_bidspath.fpath, inv, overwrite=True)

    events, evdict = mne.events_from_annotations(raw)
    keepev = {k: v for k, v in evdict.items() if k.split("/")[0] == "MINIBLOCK"}
    epochs = mne.Epochs(raw, event_id=keepev, tmin=-0.2, tmax=21.0, picks="all", preload=True)

    del raw
    if epochs.info["sfreq"] >= 2000:
        epochs.decimate(4)
    if epochs.info["sfreq"] >= 1000:
        epochs.decimate(2)
