# lcapy-gui

This package provides an experimental GUI for Lcapy, lcapy-tk.
Schematics can be created and saved in a number of formats and
symbolic component voltages and currents can be inspected.

## Installation
Ensure `wheel` and `setuptools` are installed.

If running on windows, please ensure you have the latest [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) installed.

Run `pip install .`

## How to run
From the console it can be run as `lcapy-tk`.

From a python interpreter it can be run using:

    from lcapygui import LcapyTk
    e = LcapyTk()
    e.display()
