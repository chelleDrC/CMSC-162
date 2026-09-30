"""
Shared manual convolution helper for spatial-domain filters.
"""

import numpy as np


def convolve2d(gray_array, kernel):
    arr = np.asarray(gray_array, dtype=np.float64)
    k = kernel.shape[0]
    pad = k // 2
    padded = np.pad(arr, pad, mode="edge")

    h, w = arr.shape
    out = np.zeros((h, w), dtype=np.float64)
    for i in range(h):
        for j in range(w):
            neighborhood = padded[i:i + k, j:j + k]
            out[i, j] = np.sum(neighborhood * kernel)

    return out
