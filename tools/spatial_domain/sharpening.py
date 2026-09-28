"""
Sharpening / highpass filters.

CMSC 162 Project 1 Guide 4, item (c): highpass filtering with the
Laplacian operator (kernel shown below).

    d. Unsharp masking     -- teammate's part, not implemented here yet.
    e. Highboost filtering -- teammate's part, not implemented here yet.

Where smoothing (smoothing.py) averages neighboring pixels together and
blurs the image, a highpass filter does the opposite: it responds strongly
wherever intensity changes *quickly* (edges, fine detail, noise) and
responds near zero wherever the image is flat. The Laplacian operator is
the standard way to measure that: it approximates the second derivative of
the image, using this 3x3 kernel (the "4-neighbor" Laplacian):

        0   1   0
        1  -4   1
        0   1   0

Some textbooks use the "8-neighbor" variant instead, which also reacts to
diagonal edges:

        1   1   1
        1  -8   1
        1   1   1

Both kernels sum to zero, so a perfectly flat neighborhood (all pixels
equal) produces a response of exactly 0 -- only *changes* in intensity
produce a nonzero response. That response can come out negative (e.g. going
from bright to dark), so it's converted with abs() before clipping to
[0, 255] for display; what you're looking at is edge *strength*, not sign.
"""

import numpy as np

L = 256  # intensity levels [0, 255]

LAPLACIAN_KERNEL_4 = np.array([
    [0,  1, 0],
    [1, -4, 1],
    [0,  1, 0],
], dtype=np.float64)

LAPLACIAN_KERNEL_8 = np.array([
    [1,  1, 1],
    [1, -8, 1],
    [1,  1, 1],
], dtype=np.float64)


def laplacian_highpass(gray_array, kernel_variant="4"):
    """
    Highpass filtering with the Laplacian operator.

    For every pixel, multiplies its 3x3 neighborhood elementwise by the
    chosen kernel and sums the result (this elementwise-multiply-then-sum
    is exactly what "convolution with a kernel" means). Borders are padded
    by repeating the edge pixels so the 3x3 window is always defined.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.
    kernel_variant : str
        "4" for the 4-neighbor kernel (default), "8" for the 8-neighbor
        kernel that also picks up diagonal edges.

    Returns
    -------
    np.ndarray
        (H, W) uint8 array -- the edge-response magnitude, same shape as
        input.
    """
    kernel = {"4": LAPLACIAN_KERNEL_4, "8": LAPLACIAN_KERNEL_8}.get(kernel_variant)
    if kernel is None:
        raise ValueError('kernel_variant must be "4" or "8"')

    arr = np.asarray(gray_array, dtype=np.float64)
    pad = kernel.shape[0] // 2  # 1, for a 3x3 kernel
    padded = np.pad(arr, pad, mode="edge")

    h, w = arr.shape
    out = np.zeros((h, w), dtype=np.float64)
    for i in range(h):
        for j in range(w):
            neighborhood = padded[i:i + kernel.shape[0], j:j + kernel.shape[1]]
            out[i, j] = np.sum(neighborhood * kernel)

    # The raw response can be negative; what matters for display is how
    # far it is from zero (i.e. how strong the edge is), not its sign.
    return np.clip(np.abs(out), 0, L - 1).astype(np.uint8)
