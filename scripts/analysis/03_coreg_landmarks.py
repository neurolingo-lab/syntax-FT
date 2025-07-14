from argparse import ArgumentParser
from pathlib import Path
from shutil import copy2

import mne
import mne_bids as mnb


def coreg_dialogue(subject, session, task, bids_root):
    """Run the MNE coregistration GUI."""
    # Set up the BIDS path and subject/session/task identifiers
    bids_path = mnb.BIDSPath(subject=subject, session=session, task=task, root=bids_root)
    rawpath = bids_path.copy().update(extension=".fif", suffix="meg", split="01", datatype="meg")

    try:
        raw = mnb.read_raw_bids(rawpath)
    except FileNotFoundError:
        raw = mnb.read_raw_bids(rawpath.update(split=None))

    fs_subjects_dir = bids_root / "derivatives/freesurfer/"
    t1_fname = fs_subjects_dir / f"sub-{subject}_ses-{session}" / "mri/T1.mgz"

    fs_sub = f"sub-{subject}_ses-{session}"
    if not (fidpath := fs_subjects_dir / fs_sub / f"bem/{fs_sub}-fiducials.fif").exists():
        if (fidpath.parent / f"sub-{subject}-fiducials.fif").exists():
            copy2(fidpath.parent / f"sub-{subject}-fiducials.fif", fidpath)
        else:
            raise FileNotFoundError(f"Could not find fiducials file for subject at {fidpath}")

    trans_fname = (
        bids_root
        / f"derivatives/mne-bids-pipeline/sub-{subject}/ses-{session}/"
        / f"meg/sub-{subject}_ses-{session}_task-{task}_trans.fif"
    )
    print(f"\n\nSave transform file to {trans_fname}\n\n")
    mne.gui.coregistration(
        inst=rawpath,
        subject=f"sub-{subject}_ses-{session}",
        subjects_dir=fs_subjects_dir,
        block=True,
    )  # Here you will perform the below steps before continuing

    if not trans_fname.exists():
        raise FileNotFoundError(f"Please ensure transform was saved to {trans_fname}")

    # After writing the trans and fiducials files make landmarks
    trans = mne.read_trans(trans_fname)

    landmarks = mnb.get_anat_landmarks(
        t1_fname,
        info=raw.info,
        trans=trans,
        fs_subject=f"sub-{subject}_ses-{session}",
        fs_subjects_dir=fs_subjects_dir,
    )

    # Write the final fiducials to the anatomical landmarks of the BIDS dataset
    # Note: We set "overwrite" to True because the original MRI we used for freesurfer is still in this BIDS directory

    t1w_bids_path = mnb.BIDSPath(
        subject=subject, session=session, root=bids_root, datatype="anat", suffix="T1w"
    )
    outpath = mnb.write_anat(
        image=t1_fname, bids_path=t1w_bids_path, landmarks=landmarks, verbose=True, overwrite=True
    )
    print(f"Wrote transform to {trans_fname} and updated fiducials to {outpath}")
    return


if __name__ == "__main__":
    parser = ArgumentParser(description="Run MNE coregistration GUI")
    parser.add_argument("--subject", type=str, required=True, help="Subject ID")
    parser.add_argument("--session", type=str, required=True, help="Session ID")
    parser.add_argument("--task", type=str, required=True, help="Task ID")
    parser.add_argument("--bids_root", type=Path, required=True, help="BIDS root directory")

    args = parser.parse_args()

    # Call the coregistration function with the provided arguments
    coreg_dialogue(args.subject, args.session, args.task, args.bids_root)
