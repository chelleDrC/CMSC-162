"""
Sharpening / highpass filters.

CMSC 162 Project 1 Guide 4:
    c. Highpass filtering with the Laplacian operator (kernel shown below)
    d. Unsharp masking
    e. Highboost filtering (amplification parameter k)

Where smoothing (smoothing.py) averages neighboring pixels together and
blurs the image, these filters all emphasize the opposite: intensity
change. The Laplacian responds to change directly (second derivative).
Unsharp masking and highboost filtering take a different route to the
same goal -- they use a blur to find out what detail exists, then add
that detail back on top of the original to make it more pronounced.

All three share the manual sliding-window convolution in _kernel.py
"""

import numpy as np

from ._kernel import convolve2d
from .smoothing import averaging_filter

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

    Both kernels sum to zero, so a perfectly flat neighborhood (all
    pixels equal) produces a response of exactly 0. That response can come out
    negative (e.g. going from bright to dark), so it's converted with
    abs() before clipping to [0, 255] for display; what you're looking
    at is edge *strength*, not sign.

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

    response = convolve2d(gray_array, kernel)
    return np.clip(np.abs(response), 0, L - 1).astype(np.uint8)


def _unsharp_core(gray_array, k, kernel_size=3):
    """
    Shared math for unsharp_mask() and highboost_filter() -- they are the
    same operation, differing only in how large k is allowed to be:

        1. blur the image (the "unsharp" version -- ironic name, but it's
           the standard term: a blurred copy is used to find detail)
        2. mask = original - blurred
           Blurring removes fine detail/edges, so subtracting the blur
           from the original leaves behind *only* that detail -- this
           difference is literally called the "unsharp mask".
        3. sharpened = original + k * mask
           Adding the mask back on top of the original re-emphasizes
           exactly the detail that blurring had smoothed away. Flat
           regions barely change (their mask is close to zero, since
           blurring a flat region doesn't alter it much); edges and
           texture are boosted.

    k = 1.0 is standard unsharp masking. k > 1.0 amplifies the mask
    further -- that's highboost filtering.
    """
    arr = np.asarray(gray_array, dtype=np.float64)
    blurred = averaging_filter(gray_array, kernel_size=kernel_size).astype(np.float64)
    mask = arr - blurred
    sharpened = arr + k * mask
    return np.clip(sharpened, 0, L - 1).astype(np.uint8)


def unsharp_mask(gray_array, kernel_size=3):
    """
    Unsharp masking: sharpen by adding back the detail
    a blur removes, with a fixed amplification of k = 1.0.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.
    kernel_size : int
        Size of the internal averaging-filter blur (must be odd,
        default 3).

    Returns
    -------
    np.ndarray
        (H, W) uint8 array, same shape as input.
    """
    return _unsharp_core(gray_array, k=1.0, kernel_size=kernel_size)


def highboost_filter(gray_array, k=1.5, kernel_size=3):
    """
    Highboost filtering: unsharp masking with an
    adjustable amplification factor k instead of a fixed k = 1.0.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.
    k : float
        Amplification parameter. k = 1.0 reduces to standard unsharp
        masking; k > 1.0 boosts the extracted detail further for a
        stronger sharpening effect. Intended to be user-adjustable
        (e.g. via a UI slider), same as threshold/gamma in Guide 3.
    kernel_size : int
        Size of the internal averaging-filter blur (must be odd,
        default 3).

    Returns
    -------
    np.ndarray
        (H, W) uint8 array, same shape as input.
    """
    return _unsharp_core(gray_array, k=k, kernel_size=kernel_size)
