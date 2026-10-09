"""

CMSC 162 Project 1 Guide 4, item (f): Sobel magnitude operator.

The Laplacian (sharpening.py) measures overall intensity change
with one kernel, while Sobel measures it directionally: Gx picks up
horizontal change, Gy picks up vertical change, and combining them gives
the overall edge strength regardless of direction.

"""

import numpy as np

from ._kernel import clamp_to_byte, convolve2d

SOBEL_KX = [
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
]

SOBEL_KY = [
    [-1, -2, -1],
    [ 0,  0,  0],
    [ 1,  2,  1],
]


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
    gx = convolve2d(gray_array, SOBEL_KX)  # horizontal change at every pixel
    gy = convolve2d(gray_array, SOBEL_KY)  # vertical change at every pixel

    height = gray_array.shape[0]
    width = gray_array.shape[1]
    out = np.zeros((height, width), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            change_x = gx[row][col]
            change_y = gy[row][col]

            # Pythagorean theorem: sqrt(Gx^2 + Gy^2).
            # Raising to the power 0.5 is the same as taking the square root.
            magnitude = (change_x ** 2 + change_y ** 2) ** 0.5

            out[row][col] = clamp_to_byte(magnitude)

    return out
