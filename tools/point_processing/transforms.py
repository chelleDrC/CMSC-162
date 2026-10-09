"""
Point-processing transforms: grayscale, negative, threshold, gamma.

CMSC 162 Project 1 Guide 3, items (d)-(g):
    d. grayscale transformation, s = (R + G + B) / 3
    e. negative transformation, s = (L - 1) - r
    f. black/white via manual thresholding
    g. power-law (gamma) transformation

"Point processing" means every output pixel depends ONLY on the input pixel
at the same position. So every transform below follows the same recipe:

    1. make an empty (all black) output image of the same size
    2. visit every pixel with two for loops (rows, then columns)
    3. apply the formula to that one pixel
    4. store the answer in the output image

The pixel loops are written by hand (no numpy math such as np.where,
np.clip or np.power) so each step of the formula is easy to follow.
numpy is only used to create the empty output image, because the UI needs
a numpy array to turn the result back into a picture (Image.fromarray).

apply_pipeline() chains any sequence of them together and keeps every intermediate result,
so the histogram of each transformed stage (item h) can be computed by simply
calling histogram.compute_histogram() on any of the returned arrays.
"""

import numpy as np

L = 256  # intensity levels [0, 255]


def clamp_to_byte(value):
    """
    Keep a pixel value inside the valid range [0, 255] and make it a whole number.

    Formulas can produce values like -12 or 300.7, but a pixel can only
    store whole numbers from 0 to 255. Anything too small becomes 0,
    anything too large becomes 255, and decimals are dropped (e.g. 99.8 -> 99).
    """
    if value < 0:
        return 0
    if value > L - 1:
        return L - 1
    return int(value)


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
    if len(rgb_array.shape) != 3 or rgb_array.shape[2] < 3:
        raise ValueError("grayscale_transform expects an (H, W, 3+) array")

    height = rgb_array.shape[0]
    width = rgb_array.shape[1]

    # Empty output image: one value per pixel (no color channels).
    gray = np.zeros((height, width), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            pixel = rgb_array[row][col]

            # int() turns each value into a normal Python number first.
            # Without it, adding three 0-255 values could "wrap around"
            # (e.g. 200 + 100 would not give 300).
            red = int(pixel[0])
            green = int(pixel[1])
            blue = int(pixel[2])

            average = (red + green + blue) / 3
            gray[row][col] = clamp_to_byte(average)

    return gray


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
    height = gray_array.shape[0]
    width = gray_array.shape[1]
    negative = np.zeros((height, width), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            r = int(gray_array[row][col])

            # Flip the brightness: black (0) becomes white (255) and
            # white (255) becomes black (0).
            s = (max_level - 1) - r
            negative[row][col] = clamp_to_byte(s)

    return negative


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
    height = gray_array.shape[0]
    width = gray_array.shape[1]
    black_white = np.zeros((height, width), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            r = int(gray_array[row][col])

            # Bright enough -> white, otherwise -> black.
            if r >= threshold:
                black_white[row][col] = 255
            else:
                black_white[row][col] = 0

    return black_white


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
    height = gray_array.shape[0]
    width = gray_array.shape[1]
    corrected = np.zeros((height, width), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            r = int(gray_array[row][col])

            # Step 1: scale the pixel down to the range 0.0 - 1.0
            normalized = r / (L - 1)

            # Step 2: raise it to the power gamma (** means "to the power of")
            powered = c * (normalized ** gamma)

            # Step 3: scale it back up to the range 0 - 255
            s = powered * (L - 1)
            corrected[row][col] = clamp_to_byte(s)

    return corrected


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
