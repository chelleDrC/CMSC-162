"""
Shared helper: collect every pixel's neighborhood for a k x k filter.

Instead of looping over every pixel and cutting out its k x k window one at
a time, we build a stack of k*k shifted copies of the image:

    stack[n, y, x] = the n-th neighbor of pixel (y, x)

e.g. for a 3x3 window, stack[0] holds every pixel's top-left neighbor,
stack[4] holds the pixel itself, and stack[8] its bottom-right neighbor.

A filter then just reduces along axis 0 -- e.g. np.median(stack, axis=0)
is a median filter. This is the same sliding-window idea, but numpy does
the per-pixel loop for us, which makes the filters fast enough to run
several passes interactively.
"""

import numpy as np


def neighborhood_stack(gray, kernel_size):
    """
    Parameters
    ----------
    gray : np.ndarray
        (H, W) grayscale image.
    kernel_size : int
        Window width/height -- must be odd (3, 5, 7, ...).

    Returns
    -------
    np.ndarray
        (kernel_size * kernel_size, H, W) float64 array of neighbor values.
        Borders are handled by repeating the edge pixels.
    """
    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("kernel_size must be a positive odd number (e.g. 3, 5, 7)")

    image = np.asarray(gray, dtype=np.float64)
    h, w = image.shape
    pad = kernel_size // 2
    padded = np.pad(image, pad, mode="edge")

    layers = []
    for dy in range(kernel_size):
        for dx in range(kernel_size):
            layers.append(padded[dy:dy + h, dx:dx + w])
    return np.stack(layers)
