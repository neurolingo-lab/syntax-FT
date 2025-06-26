from argparse import ArgumentParser
from pathlib import Path

from mne.viz.ui_events import VertexSelect, publish


def pick_points(brain, picks: dict) -> None:
    for hemi in picks:
        for pick in picks[hemi]:
            publish(brain, VertexSelect(hemi, pick))
    return


def make_parser(group_level: bool = False, plots: bool = False) -> ArgumentParser:
    """
    Generate a template pipeline argument parser for scripts. Will _always_ include:
      - `bids_root` flag
      - `task` flag

    Based on the `group_level` argument can also include:
      - `proc` flag
      - `subject` flag
      - `session` flag
      - `run` flag

    And likewise the `plots` argument will cause the `plotpath` flag to be included.


    Parameters
    ----------
    group_level : bool, optional
        Whether to exclude subject-level flags for when a group-level analysis script is
        run, by default False
    plots : bool, optional
        Whether to include a flag for the destination of a plotting output, by default False

    Returns
    -------
    ArgumentParser
        Argument parser object with chosen template flags, which has not been used to parse command
        line arguments yet and can still be modified.
    """
    parser = ArgumentParser()
    if not group_level:
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
            "--run",
            type=str,
            default=None,
            help="Run of the recording in question, if any. If not provided `run=None` will be used.",
        )
    parser.add_argument(
        "--task",
        type=str,
        default="syntaxIM",
        help="Task name, should match the BIDS task name.",
    )
    parser.add_argument(
        "--bids_root",
        type=Path,
        default="/srv/beegfs/scratch/users/g/gercek/syntax_im/syntax_dataset",
        help="Root directory for BIDS dataset",
    )
    if plots:
        parser.add_argument(
            "--plotpath",
            type=Path,
            default="/srv/beegfs/scratch/users/g/gercek/syntax_im/results/",
            help="Directory in which to save SNR plots, if any",
        )
    return parser


# Global parameters for different FFTs
fft_pars = dict(
    fmin=0.1,
    fmax=140.0,
)

sensor_fft_pars = dict(method="welch", n_overlap=0, n_per_seg=None, window="boxcar", **fft_pars)

source_fft_pars = dict(
    lambda2=1 / 9.0, method="MNE", nave=1, bandwidth="hann", low_bias=True, **fft_pars
)
