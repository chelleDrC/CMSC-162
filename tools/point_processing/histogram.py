"""
Manual (from-scratch) discrete histogram computation.

CMSC 162 Project 1 Guide 3, items (c) and (h): h(r_k) = n_k for r_k in
[0, 255]. Counts are accumulated with an explicit per-pixel loop -- no
cv2.calcHist / np.histogram -- so the algorithm can be walked through
step-by-step in the report.

A histogram is just a list of 256 counters, one for each possible
brightness value. We visit every pixel and add 1 to the counter that
matches its brightness.

Integration: Person B imports compute_histogram() directly on their
point-transformed 2D images (grayscale, negative, thresholded, gamma).
The UI (app/app.py) renders the result on a tkinter Canvas via
bucketize(), so the histogram lives inside PixelView itself rather than
in a separate plotting window.
"""

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
    list
        A list of 256 counts for a 2D input, or a list of C such lists
        for a 3D input -- one per channel, in the same order as the
        input's last axis.
    """
    number_of_dimensions = len(channel_or_image.shape)

    if number_of_dimensions == 2:
        return _histogram_2d(channel_or_image)

    if number_of_dimensions == 3:
        # One histogram per color channel.
        height = channel_or_image.shape[0]
        width = channel_or_image.shape[1]
        number_of_channels = channel_or_image.shape[2]

        histograms = []
        for channel_index in range(number_of_channels):
            hist = [0] * L
            for row in range(height):
                for col in range(width):
                    intensity = int(channel_or_image[row][col][channel_index])
                    hist[intensity] = hist[intensity] + 1
            histograms.append(hist)
        return histograms

    raise ValueError(f"compute_histogram expects a 2D or 3D array, got shape {channel_or_image.shape}")


def _histogram_2d(channel):
    """Explicit accumulation loop over a single (H, W) channel: O(M*N) time, O(L) space."""
    # 256 counters, all starting at 0: hist[0] counts black pixels,
    # hist[255] counts white pixels, and so on.
    hist = [0] * L

    height = channel.shape[0]
    width = channel.shape[1]

    for row in range(height):
        for col in range(width):
            intensity = int(channel[row][col])
            hist[intensity] = hist[intensity] + 1  # one more pixel with this brightness

    return hist


def bucketize(hist, num_buckets):
    """
    Downsample a 256-bin histogram into num_buckets buckets (summed),
    for rendering on a narrow tkinter Canvas that has fewer than 256
    pixels of width available.

    Example: with 128 buckets, bucket 0 = hist[0] + hist[1],
    bucket 1 = hist[2] + hist[3], and so on.
    """
    if num_buckets < 1:
        num_buckets = 1

    buckets = []
    for i in range(num_buckets):
        # Which range of the 256 bins falls into bucket i.
        start = (i * L) // num_buckets
        end = ((i + 1) * L) // num_buckets

        # Add up every bin in that range.
        total = 0
        for intensity in range(start, end):
            total = total + int(hist[intensity])
        buckets.append(total)

    return buckets
