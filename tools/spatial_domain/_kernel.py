"""
Shared manual helpers for the spatial-domain filters.

Spatial filters look at a pixel AND its neighbors (e.g. the 3x3 square
around it). These helpers are written with plain for loops so every step
can be traced by hand:

    clamp_to_byte()          keep a result inside the valid pixel range 0-255
    get_pixel_with_edge()    read a pixel, even if the position is outside the image
    get_neighborhood()       collect all pixel values under a k x k window
    convolve2d()             multiply a window by a kernel and add everything up
"""

L = 256  # intensity levels [0, 255]


def clamp_to_byte(value):
    """
    Keep a pixel value inside the valid range [0, 255] and make it a whole number.

    Anything below 0 becomes 0, anything above 255 becomes 255, and
    decimals are dropped (e.g. 99.8 -> 99).
    """
    if value < 0:
        return 0
    if value > L - 1:
        return L - 1
    return int(value)


def get_pixel_with_edge(gray_array, row, col):
    """
    Read the pixel at (row, col). If the position falls outside the image,
    use the closest pixel on the border instead.

    Why: when the window is centered on a border pixel, part of the window
    hangs outside the image. Repeating the edge pixel there (instead of
    using 0 / black) stops the borders of the result from turning dark.
    """
    height = gray_array.shape[0]
    width = gray_array.shape[1]

    # Move the row back inside the image if it went past the top or bottom.
    if row < 0:
        row = 0
    if row > height - 1:
        row = height - 1

    # Move the column back inside the image if it went past the left or right.
    if col < 0:
        col = 0
    if col > width - 1:
        col = width - 1

    return int(gray_array[row][col])


def get_neighborhood(gray_array, center_row, center_col, kernel_size):
    """
    Return every pixel value inside the kernel_size x kernel_size window
    centered on (center_row, center_col), as one flat Python list.

    Example for kernel_size = 3: the 9 values from the 3x3 square around
    the center pixel, read left to right, top to bottom.
    """
    half = kernel_size // 2  # how far the window reaches from the center (1 for a 3x3)

    values = []
    for offset_row in range(-half, half + 1):
        for offset_col in range(-half, half + 1):
            value = get_pixel_with_edge(gray_array,
                                        center_row + offset_row,
                                        center_col + offset_col)
            values.append(value)
    return values


def convolve2d(gray_array, kernel):
    """
    Manual 2D convolution (sliding-window weighted sum).

    For every pixel:
        1. place the kernel on top of the image, centered on that pixel
        2. multiply each kernel number by the pixel underneath it
        3. add all those products together -> that sum is the new pixel

    Parameters
    ----------
    gray_array : np.ndarray
        (H, W) single-channel array.
    kernel : list of lists
        Square kernel with an odd size, e.g. 3x3.

    Returns
    -------
    list of lists
        (H, W) raw sums as decimal numbers. They are NOT clamped to
        0-255 yet, because some filters (Laplacian, Sobel) need the
        negative values before deciding what to display.
    """
    height = gray_array.shape[0]
    width = gray_array.shape[1]
    kernel_size = len(kernel)
    half = kernel_size // 2

    result = []
    for row in range(height):
        result_row = []
        for col in range(width):

            total = 0.0
            for k_row in range(kernel_size):
                for k_col in range(kernel_size):
                    # Image position under this kernel cell.
                    image_row = row + k_row - half
                    image_col = col + k_col - half

                    pixel = get_pixel_with_edge(gray_array, image_row, image_col)
                    weight = kernel[k_row][k_col]
                    total = total + pixel * weight

            result_row.append(total)
        result.append(result_row)

    return result
