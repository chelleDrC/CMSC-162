"""
Channel splitting utilities.

CMSC 162 Project 1 Guide 3, item (b): divide an image into its Red, Green
and Blue channels for display and downstream histogram analysis.

Every color pixel is stored as three numbers: [Red, Green, Blue].
Splitting the channels means copying each of those three numbers into its
own separate image. The copying is done pixel by pixel with plain for loops
so the process is easy to follow.
"""

import numpy as np
from PIL import Image


def to_array(image):
    """PIL Image -> numpy uint8 array (H, W, 3)."""

    return np.asarray(image.convert("RGB"), dtype=np.uint8) #uint8 means each value is 0-255


def split_channels(image):
    """
    Split an RGB image into its Red, Green and Blue channels.

    Parameters
    ----------
    image : PIL.Image.Image or np.ndarray
        Source image. PIL images are converted to RGB first.

    Returns
    -------
    dict[str, np.ndarray]
        {"R": (H, W) uint8, "G": (H, W) uint8, "B": (H, W) uint8}
    """
    if isinstance(image, Image.Image):
        arr = to_array(image)
    else:
        arr = np.asarray(image)

    if len(arr.shape) != 3 or arr.shape[2] < 3:
        raise ValueError("split_channels expects an (H, W, 3+) RGB array/image")

    height = arr.shape[0]
    width = arr.shape[1]

    # Three empty single-channel images, one for each color.
    red_channel = np.zeros((height, width), dtype=np.uint8)
    green_channel = np.zeros((height, width), dtype=np.uint8)
    blue_channel = np.zeros((height, width), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            pixel = arr[row][col]          # e.g. [200, 120, 35]
            red_channel[row][col] = pixel[0]
            green_channel[row][col] = pixel[1]
            blue_channel[row][col] = pixel[2]

    return {"R": red_channel, "G": green_channel, "B": blue_channel}


def channel_as_grayscale(channel):
    """Single channel (H, W) -> PIL 'L' image, shown as an intensity map."""
    return Image.fromarray(channel.astype(np.uint8), mode="L")


def channel_as_color(channel, which):
    """
    Single channel (H, W) -> PIL 'RGB' image with the other two channels
    zeroed, so e.g. the Red channel renders red-tinted instead of gray.

    Parameters
    ----------
    which : str
        One of "R", "G", "B" -- which channel slot to populate.
    """
    # Position of the chosen color inside a pixel: [R, G, B] -> 0, 1, 2
    if which == "R":
        index = 0
    elif which == "G":
        index = 1
    else:
        index = 2

    height = channel.shape[0]
    width = channel.shape[1]

    # Start with an all-black color image (every pixel is [0, 0, 0]).
    out = np.zeros((height, width, 3), dtype=np.uint8)

    # Fill in only the chosen color; the other two stay 0.
    for row in range(height):
        for col in range(width):
            out[row][col][index] = channel[row][col]

    return Image.fromarray(out, mode="RGB")
