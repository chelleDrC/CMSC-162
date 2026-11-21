"""
Order-statistic filter for noise removal (item b.ii).

"Order statistic" means: sort (rank) the k x k neighborhood values, then
pick one based on its position in that sorted list. The median filter picks
the middle value:

    f(x, y) = median of g(s, t) over the neighborhood S_xy

A salt (255) or pepper (0) pixel always lands at an end of the sorted
list, so it is never chosen -- which is why the median filter removes
salt-and-pepper noise so well. It can be applied several times (multiple
passes) to remove what is left after the first pass.
"""

from ._window import filter_image


def median_filter(gray, kernel_size=3):
    """
    Parameters
    ----------
    gray : list of rows
        H rows of W ints (0-255).
    kernel_size : int
        Odd window size (3, 5, 7, ...).

    Returns
    -------
    list of rows
        The filtered image, same size as the input.
    """
    def window_value(window):
        # k*k is odd, so the exact middle of the sorted list is the median.
        return sorted(window)[len(window) // 2]

    return filter_image(gray, kernel_size, window_value)
