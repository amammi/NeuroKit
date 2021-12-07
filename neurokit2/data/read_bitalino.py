# -*- coding: utf-8 -*-
import json

import numpy as np
import pandas as pd

from ..signal import signal_resample


def read_bitalino(filename, sampling_rate="max", resample_method="interpolation"):
    """Read and format a  OpenSignals file (e.g., from BITalino) into a pandas' dataframe.

    The function outputs both the dataframe and the sampling rate (retrieved from the
    OpenSignals file).

    Parameters
    ----------
    filename :  str
        Filename (with or without the extension) of an OpenSignals file (e.g., 'data.txt').
    sampling_rate : int
        Sampling rate (in Hz, i.e., samples/second). Defaults to the original sampling rate at which signals were
        sampled if set to "max". If the sampling rate is set to a given value, will resample
        the signals to the desired value. Note that the value of the sampling rate is outputted
        along with the data.
    resample_method : str
        Method of resampling (see `signal_resample()`).

    Returns
    ----------
    df : DataFrame
        The BITalino file as a pandas dataframe.
    sampling rate: int
        The sampling rate at which the data is sampled.

    See Also
    --------
    read_acqknowledge, signal_resample

    Examples
    --------
    >>> import neurokit2 as nk
    >>>
    >>> #data, sampling_rate = nk.read_bitalino("data.txt")
    """
    # read metadata
    with open(filename, "r") as f:

        if "OpenSignals" not in f.readline():  # read first line
            raise ValueError(
                "NeuroKit error: read_bitalino(): Text file is not in OpenSignals format."
            )

        metadata = json.loads(f.readline()[1:])  # read second line

    if len(list(metadata.keys())) == 1:
        # If only one device
        metadata = metadata[
            list(metadata.keys())[0]
        ]  # convert json header to dict (only select first device / MAC address)
        channels = np.arange(len(metadata["channels"])) + 5  # analog channels start from column 5

        data = pd.read_csv(filename, sep="\t", usecols=channels, header=None, comment="#")

        # Add column names
        data.columns = metadata["sensor"]

        # Adjust sampling rate
        if sampling_rate == "max":
            sampling_rate = metadata["sampling rate"]
        else:
            # resample
            data, sampling_rate = _read_bitalino_resample(data, metadata["sampling rate"], sampling_rate, resample_method=resample_method)

    else:
        # Read from multiple devices
        devices = list(metadata.keys())
        data = pd.DataFrame([])
        for index, name in enumerate(devices):

            channels = np.arange(len(metadata[name]["channels"])) + 5  + (5 * index) + (2 * index)
            # analog channels start from column 5 for each device

            df = pd.read_csv(filename, sep="\t", usecols=channels, header=None, comment="#")
            df.columns = [i + '_' + metadata[name]['device name'] for i in metadata[name]['sensor']]

            data = pd.concat([data, df], axis=1)

        # Adjust sampling rate
        if sampling_rate == "max":
            sampling_rate = metadata[name]["sampling rate"]
        else:
            # resample
            data, sampling_rate = _read_bitalino_resample(data, metadata[name]["sampling rate"], sampling_rate, resample_method=resample_method)

    return data, sampling_rate


def _read_bitalino_resample(data, original_sampling_rate, resampling_rate, resample_method="interpolation"):

    signals = pd.DataFrame()
    for i in data:
        signal = signal_resample(
            data[i],
            sampling_rate=original_sampling_rate,
            desired_sampling_rate=resampling_rate,
            method=resample_method,
        )
        signal = pd.Series(signal)
        signals = pd.concat([signals, signal], axis=1)
    data = signals.copy()

    return data, sampling_rate
