"""
Image degradation and restoration (CMSC 162 Project 2 Guide 2).

    noise.py             -- item a: add salt-and-pepper, Gaussian, or Rayleigh noise
    mean_filters.py      -- item b.ii: geometric mean and contraharmonic mean filters
    order_statistics.py  -- item b.ii: median filter (order-statistic)
    _window.py           -- shared helper that gathers each pixel's k x k neighborhood

Every function takes and returns an (H, W) uint8 grayscale numpy array.
"""
