"""
Channel splitting utilities.

CMSC 162 Project 1 Guide 3, item (b): divide an image into its Red, Green
and Blue channels for display and downstream histogram analysis.
"""

import numpy as np
from PIL import Image


def to_array(image):
    """PIL Image -> numpy uint8 array (H, W, 3)."""
    return np.asarray(image.convert("RGB"), dtype=np.uint8)


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
    arr = to_array(image) if isinstance(image, Image.Image) else np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] < 3:
        raise ValueError("split_channels expects an (H, W, 3+) RGB array/image")
    return {"R": arr[:, :, 0], "G": arr[:, :, 1], "B": arr[:, :, 2]}


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
    index = {"R": 0, "G": 1, "B": 2}[which]
    out = np.zeros((*channel.shape, 3), dtype=np.uint8)
    out[:, :, index] = channel
    return Image.fromarray(out, mode="RGB")
