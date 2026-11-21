"""
Shared helpers for the restoration code.

Images are lists of rows: gray[y][x] is an int in [0, 255].

    clamp_to_byte  -- round a number and keep it inside [0, 255]
    pad_edges      -- copy of the image with the edge pixels repeated outward
    filter_image   -- slide a k x k window over the image and replace each
                      pixel with a value computed from the window

"""

L = 256  # intensity levels [0, 255]


def clamp_to_byte(value):
    """Round to the nearest integer and clip to [0, 255]."""
    value = round(value)
    if value < 0:
        return 0
    if value > L - 1:
        return L - 1
    return value


def pad_edges(gray, pad):
    """
    Return a copy of the image with `pad` extra rows and columns on every
    side. The new border repeats the nearest edge pixel, so windows centered
    on border pixels still have a full k x k set of neighbors.
    """
    h = len(gray)
    padded = []
    for y in range(-pad, h + pad):
        row = gray[min(max(y, 0), h - 1)]  # rows above/below reuse the first/last row
        padded.append([row[0]] * pad + row + [row[-1]] * pad)
    return padded


def filter_image(gray, kernel_size, window_value):
    """
    Parameters
    ----------
    gray : list of rows (H rows of W ints)
    kernel_size : odd window width/height (3, 5, 7, ...)
    window_value : function(list of k*k ints) -> int, the new pixel value

    Returns
    -------
    A new list of rows, the same size as the input.
    """
    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("kernel_size must be a positive odd number (e.g. 3, 5, 7)")

    h, w = len(gray), len(gray[0])
    padded = pad_edges(gray, kernel_size // 2)

    result = []
    for y in range(h):
        rows = padded[y:y + kernel_size]  # the k rows this output row needs
        out_row = []
        for x in range(w):
            window = []
            for row in rows:
                window.extend(row[x:x + kernel_size])
            out_row.append(window_value(window))
        result.append(out_row)
    return result
