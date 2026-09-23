"""
Point-processing transforms: grayscale, negative, threshold, gamma.

CMSC 162 Project 1 Guide 3, items (d)-(g):
    d. grayscale transformation, s = (R + G + B) / 3
    e. negative transformation, s = (L - 1) - r
    f. black/white via manual thresholding
    g. power-law (gamma) transformation

Each transform is a standalone function operating on numpy arrays
apply_pipeline() chains any sequence of them together and keeps every intermediate result, 
so the histogram of each transformed stage (item h) can be computed by simply
calling histogram.compute_histogram() on any of the returned arrays.
"""

import numpy as np

L = 256  # intensity levels [0, 255]


def grayscale_transform(rgb_array):
    """
    s = (R + G + B) / 3.

    Parameters
    ----------
    rgb_array : np.ndarray
        (H, W, 3) uint8 array.

    Returns
    -------
    np.ndarray
        (H, W) uint8 grayscale array.
    """
    arr = np.asarray(rgb_array, dtype=np.float64)
    if arr.ndim != 3 or arr.shape[2] < 3:
        raise ValueError("grayscale_transform expects an (H, W, 3+) array")
    gray = (arr[:, :, 0] + arr[:, :, 1] + arr[:, :, 2]) / 3.0
    return np.clip(gray, 0, L - 1).astype(np.uint8)


def negative_transform(gray_array, max_level=L):
    """
    s = (L - 1) - r.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.
    max_level : int
        Number of intensity levels L (default 256, i.e. range [0, 255]).

    Returns
    -------
    np.ndarray
        (H, W) uint8 array, same shape as input.
    """
    arr = np.asarray(gray_array, dtype=np.int64)
    negative = (max_level - 1) - arr
    return np.clip(negative, 0, max_level - 1).astype(np.uint8)


def threshold_transform(gray_array, threshold):
    """
    Manual black/white thresholding: s = 255 if r >= threshold else 0.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.
    threshold : int
        Cutoff intensity in [0, 255]. Intended to be user-adjustable
        (e.g. via a UI slider) rather than a fixed constant.

    Returns
    -------
    np.ndarray
        (H, W) uint8 array containing only 0 or 255.
    """
    arr = np.asarray(gray_array)
    return np.where(arr >= threshold, 255, 0).astype(np.uint8)


def gamma_transform(gray_array, gamma, c=1.0):
    """
    Power-law transformation: s = c * (r / 255)^gamma * 255.

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) uint8 single-channel array.
    gamma : float
        Exponent. gamma < 1 brightens midtones, gamma > 1 darkens them.
        Intended to be user-adjustable (e.g. via a UI slider).
    c : float
        Scaling constant (default 1.0).

    Returns
    -------
    np.ndarray
        (H, W) uint8 array, same shape as input.
    """
    arr = np.asarray(gray_array, dtype=np.float64) / (L - 1)
    corrected = c * np.power(arr, gamma) * (L - 1)
    return np.clip(corrected, 0, L - 1).astype(np.uint8)


def apply_pipeline(image, steps):
    """
    Apply a sequence of transforms in order, keeping every intermediate result

    Parameters
    ----------
    image : np.ndarray
        Starting array, e.g. an (H, W, 3) RGB array for a pipeline that
        begins with grayscale_transform, or an (H, W) array if starting
        from an already-grayscale image.
    steps : list[tuple[callable, dict]]
        Ordered (transform_fn, kwargs) pairs. Each transform_fn is
        called as transform_fn(current_array, **kwargs).

    Returns
    -------
    list[np.ndarray]
        [image, result_after_step_1, result_after_step_2, ...] -- one
        more entry than len(steps), since the original input is
        included as stage 0.
    """
    stages = [np.asarray(image)]
    current = stages[0]
    for transform_fn, kwargs in steps:
        current = transform_fn(current, **(kwargs or {}))
        stages.append(current)
    return stages
