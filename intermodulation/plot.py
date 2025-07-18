import warnings
from functools import partial

import matplotlib
import mne
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def snr_topo(
    snrs: np.ndarray,
    epochs: mne.Epochs,
    freqs: np.ndarray,
    fmin: float | None = None,
    fmax: float | None = None,
    ymin: float | None = None,
    ymax: float | None = None,
    vlines: list | None = None,
    fig_kwargs: dict | None = None,
    show_axes=False,
    annot_max=False,
):
    if ymin is None:
        ymin = snrs.min()
    if ymax is None:
        ymax = snrs.max()
    if fmin is None:
        fmin = freqs.min()
    if fmax is None:
        fmax = freqs.max()
    if fig_kwargs is None:
        fig_kwargs = {"figsize": (16, 16), "dpi": 600}

    def plotcallback(ax, ch_idx):
        ax.plot(freqs, snrs[ch_idx], color="w")
        if vlines is not None:
            for vline in vlines:
                ax.axvline(vline, color="w", linestyle="--", alpha=0.5)
        ax.set_ylim(ymin, ymax)
        ax.set_xlim(fmin, fmax)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("SNR")

    fig = plt.figure(**fig_kwargs)
    if show_axes:
        spinecolor = "w"
    else:
        spinecolor = "k"
    itertopo = mne.viz.iter_topography(
        epochs.info, on_pick=plotcallback, fig=fig, axis_spinecolor=spinecolor
    )

    for ax, idx in itertopo:
        mne.Epochs._keys_to_idx
        ax.plot(freqs, snrs[idx], color="w", lw=0.15)[0]
        ax.set_ylim(ymin, ymax)
        ax.set_xlim(fmin, fmax)
        if show_axes:
            ax.spines.top.set_visible(False)
            ax.spines.right.set_visible(False)
            ax.spines.bottom.set_linewidth(0.5)
            ax.spines.bottom.set_alpha(0.5)
            ax.spines.left.set_linewidth(0.5)
            ax.spines.left.set_alpha(0.5)
        if vlines is not None:
            for vline in vlines:
                ax.axvline(vline, color="w", linestyle="--", alpha=0.75, lw=0.15)
        if annot_max:
            maxidx = np.nanargmax(snrs[idx])
            maxsnrF = freqs[maxidx]
            maxsnr = snrs[idx][maxidx]
            ax.annotate(
                text=f"{maxsnr:.2f}, {maxsnrF:.2f}",
                xy=(0.0, 0.8),
                xycoords="axes fraction",
                color="w",
                fontsize=3,
                annotation_clip=False,
                visible=True,
            )
    if "inline" not in matplotlib.get_backend():
        fig.show()
    return fig


def itc_wholetrial_topo(
    itcs: pd.DataFrame,
    info: mne.Info,
    fmin: float | None = None,
    fmax: float | None = None,
    ymin: float | None = None,
    ymax: float | None = None,
    vlines: list | None = None,
    picks: list[str] | None = None,
    fig_kwargs: dict | None = None,
):
    if picks is None:
        picks = info.ch_names
    if ymin is None:
        ymin = 0.0
    if ymax is None:
        ymax = 1.0
    if fig_kwargs is None:
        fig_kwargs = {"figsize": (16, 16), "dpi": 600}

    def plotcallback(ax, ch_idx):
        ax.plot(itcs.columns.to_numpy(), itcs.iloc[ch_idx], color="w")
        if vlines is not None:
            for vline in vlines:
                ax.axvline(vline, color="r", linestyle="--")
        ax.set_ylim(ymin, ymax)
        ax.set_xlim(fmin, fmax)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("ITC")

    fig = plt.figure(**fig_kwargs)
    itertopo = mne.viz.iter_topography(info, on_pick=plotcallback, fig=fig)

    for ax, idx in itertopo:
        if itcs.index[idx] not in picks:
            continue
        ax.plot(itcs.columns.to_numpy(), itcs.iloc[idx], color="white", lw=0.5)
        ax.set_ylim(0, 1)
        ax.set_xlim(fmin, fmax)
        if vlines is not None:
            for vline in vlines:
                ax.axvline(vline, color="w", linestyle="--", lw=0.3, alpha=0.75)
    return fig


def itc_singlefreq_topo(
    itc: mne.time_frequency.AverageTFR,
    data: np.ndarray,
    times: np.ndarray,
    freqs: np.ndarray,
    freq: float,
    picks: list[str] | None = None,
    tmin: float | None = None,
    tmax: float | None = None,
    ymin: float | None = None,
    ymax: float | None = None,
    vlines: list | None = None,
):
    if picks is None:
        picks = mne.pick_types(itc.info, meg=True)
    if tmin is None:
        tmin = times.min()
    if tmax is None:
        tmax = times.max()

    fidx = np.abs(freqs - freq).argmin()
    fdata = data[:, fidx, :]

    if ymin is None:
        ymin = fdata.min()
    if ymax is None:
        ymax = fdata.max()

    pick_fun = partial(
        mne.viz.topo._plot_timeseries_unified,
        data=[fdata],
        times=[times],
        color="w",
        vline=vlines,
        ylim=(ymin, ymax),
    )

    click_fun = partial(
        mne.viz.topo._plot_timeseries,
        data=[fdata],
        times=[times],
        color="w",
        vline=vlines,
        ylim=(ymin, ymax),
    )

    fig = mne.viz.topo._plot_topo(
        itc.info,
        times=(tmin, tmax),
        show_func=pick_fun,
        click_func=click_fun,
        layout=mne.channels.find_layout(itc.info),
        unified=True,
        x_label="Time (s)",
        y_label="ITC",
    )

    fig.suptitle(f"ITC at {freq:.2f} Hz")
    return fig


def plot_snr(
    psds,
    snrs,
    freqs,
    fmin,
    fmax,
    titleannot="",
    fig=None,
    axes=None,
    tagfreq=None,
    plotpsd=False,
    annot_snr_peaks=False,
):
    if len(titleannot) > 0:
        titleannot = ": " + titleannot
    if fig is None:
        nrows = 2 if plotpsd else 1
        fig, axes = plt.subplots(nrows, 1, sharex=plotpsd)
    if plotpsd and axes is not None:
        if len(axes) != 2:
            raise ValueError("If axes are passed, they must be a list of two axes objects.")
    if not plotpsd:
        if axes is not None and not isinstance(axes, plt.Axes):
            raise ValueError("If not plotting PSD, axes must be a single axes object.")
        axes = [axes]

    freq_range = range(
        np.flatnonzero(np.floor(freqs) >= fmin)[0], np.flatnonzero(np.ceil(freqs) <= fmax)[-1]
    )
    axidx = 0

    if snrs.ndim == 2:
        meanaxis = (0,)
    elif snrs.ndim == 3:
        meanaxis = (0, 1)
    else:
        raise ValueError("psds must be 2D or 3D array.")

    if plotpsd:
        psds_plot = 10 * np.log10(psds)
        psds_mean = psds_plot.mean(axis=meanaxis)[freq_range]
        psds_std = psds_plot.std(axis=meanaxis)[freq_range]
        axes[axidx].plot(freqs[freq_range], psds_mean, color="b")
        axes[axidx].fill_between(
            freqs[freq_range], psds_mean - psds_std, psds_mean + psds_std, color="b", alpha=0.2
        )
        axes[axidx].set(title="PSD " + titleannot, ylabel="Power Spectral Density [dB]")
        axidx += 1

    # SNR spectrum
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        snr_mean = np.nanmean(snrs, axis=meanaxis)[freq_range]
        # print(snr_mean.shape)
        snr_std = np.nanstd(snrs, axis=meanaxis)[freq_range]

    axes[axidx].plot(freqs[freq_range], snr_mean, color="r")
    axes[axidx].fill_between(
        freqs[freq_range], snr_mean - snr_std, snr_mean + snr_std, color="r", alpha=0.2
    )
    axes[axidx].set(
        title="SNR " + titleannot,
        xlabel="Frequency [Hz]",
        ylabel="SNR",
    )

    # Annotate peaks above given SNR if annot_snr_peaks is not false.
    if annot_snr_peaks is not False:
        if not isinstance(annot_snr_peaks, bool) and (
            isinstance(annot_snr_peaks, float) or isinstance(annot_snr_peaks, int)
        ):
            minpeak = annot_snr_peaks
        else:
            minpeak = 1.5
        for idx, freq in enumerate(freqs[freq_range]):
            if ((peak := snr_mean[idx]) > minpeak) and np.isfinite(peak):
                # print(peak, minpeak)
                axes[axidx].annotate(f"{freq:0.2f} Hz", (freq, peak))

    if tagfreq is not None:
        if isinstance(tagfreq, (list, np.ndarray)):
            tagfreqs = tagfreq
        else:
            tagfreqs = [tagfreq]
        for freq in tagfreqs:
            if plotpsd:
                axes[0].axvline(freq, color="purple", linestyle="--", alpha=0.5)
            axes[axidx].axvline(freq, color="purple", linestyle="--", alpha=0.5)

    axes[axidx].set_xlim([fmin, fmax])

    fig.show()
    return fig, axes
