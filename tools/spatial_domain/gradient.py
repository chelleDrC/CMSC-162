"""

CMSC 162 Project 1 Guide 4, item (f): Sobel magnitude operator.

The Laplacian (sharpening.py) measures overall intensity change
with one kernel, while Sobel measures it directionally: Gx picks up
horizontal change, Gy picks up vertical change, and combining them gives
the overall edge strength regardless of direction.

"""

import numpy as np

from ._kernel import convolve2d

L = 256  # intensity levels [0, 255]

SOBEL_KX = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
], dtype=np.float64)

SOBEL_KY = np.array([
    [-1, -2, -1],
    [ 0,  0,  0],
    [ 1,  2,  1],
], dtype=np.float64)


def sobel_magnitude(gray_array):
    """
    Gradient magnitude using the Sobel operator.

    Convolves the image with Gx (horizontal-change kernel) and Gy
    (vertical-change kernel) separately, then combines the two
    directional responses into a single edge-strength value per pixel
    via sqrt(Gx^2 + Gy^2) - the magnitude of the 2D gradient vector
    (Gx, Gy) at that pixel. A flat neighborhood produces Gx = Gy = 0
    (both kernels sum to zero), so only actual intensity change 
    (edges, fine detail, noise) produces a nonzero response.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.

    Returns
    -------
    np.ndarray
        (H, W) uint8 array -- the edge-strength magnitude, same shape as
        input.
    """
    gx = convolve2d(gray_array, SOBEL_KX)
    gy = convolve2d(gray_array, SOBEL_KY)
    magnitude = np.sqrt(gx ** 2 + gy ** 2)
    return np.clip(magnitude, 0, L - 1).astype(np.uint8)
