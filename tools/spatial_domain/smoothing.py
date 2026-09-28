"""
Smoothing (blurring) filters.

CMSC 162 Project 1 Guide 4, items (a) and (b):
    a. Averaging filter
    b. Median filter

Both filters work the same general way: slide a small square window (the
"kernel", e.g. 3x3) over every pixel of the image, look at the neighborhood
of pixel values under that window, and replace the center pixel with some
summary of that neighborhood. This is exactly what "spatial domain"
filtering means -- as opposed to point processing (Guide 3), where a pixel's
new value only ever depended on itself, here it depends on its neighbors
too.

The two filters differ only in *how* they summarize the neighborhood:
    - Averaging filter: the neighborhood's mean. Blurs the image by
      smoothing out sharp jumps in intensity -- good for reducing random
      ("Gaussian-like") noise, but also softens real edges.
    - Median filter: the neighborhood's median. Also blurs, but is much
      better at removing salt-and-pepper noise (stray black/white pixels)
      without smearing edges as much, since a single extreme outlier
      pixel can't drag the median the way it drags the mean.

Implemented as an explicit sliding-window loop (no cv2.blur /
cv2.medianBlur / scipy.ndimage) so the algorithm can be walked through
step-by-step in the report, matching histogram.py's approach in Guide 3.
Because of that, filtering a large image can take a couple of seconds --
that trade-off is intentional here, not a bug.
"""

import numpy as np

L = 256  # intensity levels [0, 255]


def _slide_window(gray_array, kernel_size, reduce_fn):
    """
    Shared sliding-window scaffolding for averaging_filter/median_filter.

    Pads the image by kernel_size // 2 pixels on every side (repeating the
    edge pixels, so the border doesn't darken toward zero) and then, for
    every output pixel, cuts out its kernel_size x kernel_size neighborhood
    and reduces it to a single number with reduce_fn (e.g. np.mean or
    np.median).
    """
    if kernel_size % 2 == 0 or kernel_size < 1:
        raise ValueError("kernel_size must be a positive odd number (e.g. 3, 5, 7)")

    arr = np.asarray(gray_array, dtype=np.float64)
    pad = kernel_size // 2
    padded = np.pad(arr, pad, mode="edge")

    h, w = arr.shape
    out = np.zeros((h, w), dtype=np.float64)
    for i in range(h):
        for j in range(w):
            neighborhood = padded[i:i + kernel_size, j:j + kernel_size]
            out[i, j] = reduce_fn(neighborhood)

    return np.clip(out, 0, L - 1).astype(np.uint8)


def averaging_filter(gray_array, kernel_size=3):
    """
    Mean filter: each output pixel = the average of its neighborhood.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.
    kernel_size : int
        Neighborhood width/height, must be odd (default 3, i.e. a 3x3
        window). Larger kernels blur more.

    Returns
    -------
    np.ndarray
        (H, W) uint8 array, same shape as input.
    """
    return _slide_window(gray_array, kernel_size, np.mean)


def median_filter(gray_array, kernel_size=3):
    """
    Median filter: each output pixel = the median of its neighborhood.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.
    kernel_size : int
        Neighborhood width/height, must be odd (default 3, i.e. a 3x3
        window).

    Returns
    -------
    np.ndarray
        (H, W) uint8 array, same shape as input.
    """
    return _slide_window(gray_array, kernel_size, np.median)
