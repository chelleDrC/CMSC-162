"""
Image degradation and restoration (CMSC 162 Project 2 Guide 2).

    noise.py             -- item a: add salt-and-pepper, Gaussian, or Rayleigh noise
    mean_filters.py      -- item b.ii: geometric mean and contraharmonic mean filters
    order_statistics.py  -- item b.ii: median filter (order-statistic)
    _window.py           -- shared helpers: clamping and the sliding k x k window

Plain Python only (no NumPy). Every function takes and returns a grayscale
image as a list of rows of 0-255 ints.
"""
