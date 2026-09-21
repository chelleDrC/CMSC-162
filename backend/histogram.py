"""
Manual (from-scratch) discrete histogram computation.

CMSC 162 Project 1 Guide 3, items (c) and (h): h(r_k) = n_k for r_k in
[0, 255]. Counts are accumulated with an explicit per-pixel loop -- no
cv2.calcHist / np.histogram -- so the algorithm can be walked through
step-by-step in the report.

Integration: Person B imports compute_histogram() directly on their
point-transformed 2D images (grayscale, negative, thresholded, gamma).
The UI (ui/app.py) renders the result on a tkinter Canvas via
bucketize(), so the histogram lives inside PixelView itself rather than
in a separate plotting window.
"""

import numpy as np

L = 256  # intensity levels [0, 255]


def compute_histogram(channel_or_image):
    """
    Discrete histogram h(r_k) = n_k, r_k in [0, 255].

    Parameters
    ----------
    channel_or_image : np.ndarray
        (H, W) single-channel array, or (H, W, C) multi-channel array.

    Returns
    -------
    np.ndarray
        Shape (256,) for a 2D input, or (C, 256) for a 3D input -- one
        row per channel, in the same order as the input's last axis.
    """
    arr = np.asarray(channel_or_image)

    if arr.ndim == 2:
        return _histogram_2d(arr)

    if arr.ndim == 3:
        return np.stack([_histogram_2d(arr[:, :, c]) for c in range(arr.shape[2])])

    raise ValueError(f"compute_histogram expects a 2D or 3D array, got shape {arr.shape}")


def _histogram_2d(channel):
    """Explicit accumulation loop over a single (H, W) channel: O(M*N) time, O(L) space."""
    hist = np.zeros(L, dtype=np.int64)
    for intensity in channel.astype(np.int64).ravel():  # one increment per pixel
        hist[intensity] += 1
    return hist


def bucketize(hist, num_buckets):
    """
    Downsample a 256-bin histogram into num_buckets buckets (summed),
    for rendering on a narrow tkinter Canvas that has fewer than 256
    pixels of width available.
    """
    hist = np.asarray(hist)
    num_buckets = max(1, num_buckets)
    edges = np.linspace(0, L, num_buckets + 1).astype(int)
    return [int(hist[edges[i]:edges[i + 1]].sum()) for i in range(num_buckets)]
