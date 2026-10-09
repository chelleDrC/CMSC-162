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
cv2.medianBlur / scipy.ndimage / np.mean / np.median) so the algorithm can
be walked through step-by-step in the report, matching histogram.py's
approach in Guide 3. Because of that, filtering a large image can take a
couple of seconds -- that trade-off is intentional here, not a bug.
"""

import numpy as np

from ._kernel import clamp_to_byte, get_neighborhood


def _check_kernel_size(kernel_size):
    """The window needs a center pixel, so its size must be odd (3, 5, 7, ...)."""
    if kernel_size % 2 == 0 or kernel_size < 1:
        raise ValueError("kernel_size must be a positive odd number (e.g. 3, 5, 7)")


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
    _check_kernel_size(kernel_size)

    height = gray_array.shape[0]
    width = gray_array.shape[1]
    out = np.zeros((height, width), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            values = get_neighborhood(gray_array, row, col, kernel_size)

            # Average = add everything up, then divide by how many there are.
            total = 0
            for value in values:
                total = total + value
            average = total / len(values)

            out[row][col] = clamp_to_byte(average)

    return out


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
    _check_kernel_size(kernel_size)

    height = gray_array.shape[0]
    width = gray_array.shape[1]
    out = np.zeros((height, width), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            values = get_neighborhood(gray_array, row, col, kernel_size)

            # Median = the middle value once the list is sorted.
            # The window always holds an odd number of values (9, 25, ...),
            # so there is always exactly one middle value.
            values.sort()
            middle_index = len(values) // 2
            median = values[middle_index]

            out[row][col] = clamp_to_byte(median)

    return out
