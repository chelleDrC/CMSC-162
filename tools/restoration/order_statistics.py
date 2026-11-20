"""
Order-statistic filter for noise removal (Project 2 Guide 2, item b.ii).

"Order statistic" means: sort (rank) the k x k neighborhood values, then
pick one based on its position in that sorted list. The median filter picks
the middle value:

    f(x, y) = median of g(s, t) over the neighborhood S_xy

A salt (255) or pepper (0) pixel always lands at an end of the sorted
list, so it is never chosen -- which is why the median filter removes
salt-and-pepper noise so well. It can be applied several times (multiple
passes) to remove what is left after the first pass.
"""

import numpy as np

from ._window import neighborhood_stack

L = 256  # intensity levels [0, 255]


def median_filter(gray, kernel_size=3):
    """
    Parameters
    ----------
    gray : np.ndarray
        (H, W) uint8 grayscale image.
    kernel_size : int
        Odd window size (3, 5, 7, ...).

    Returns
    -------
    np.ndarray
        (H, W) uint8 filtered image.
    """
    stack = neighborhood_stack(gray, kernel_size)
    result = np.median(stack, axis=0)
    return np.clip(np.round(result), 0, L - 1).astype(np.uint8)
