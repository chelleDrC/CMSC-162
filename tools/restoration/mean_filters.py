"""
Mean filters for noise removal (Project 2 Guide 2, item b.ii).

Both filters replace each pixel with a kind of "average" of its k x k
neighborhood S_xy (mn = k*k pixels), computed from the noisy image g:

    Geometric mean:     f(x, y) = [ product of g(s, t) over S_xy ] ^ (1 / mn)

    Contraharmonic:     f(x, y) = sum of g(s, t)^(Q+1)  /  sum of g(s, t)^Q
                                  (both sums over S_xy)

Contraharmonic order Q:
    Q > 0  -> favours bright values: removes PEPPER (black) noise
    Q < 0  -> favours dark values:   removes SALT (white) noise
    Q = 0  -> arithmetic mean;  Q = -1 -> harmonic mean
Choosing the wrong sign makes the noise worse, not better.
"""

import numpy as np

from ._window import neighborhood_stack

L = 256  # intensity levels [0, 255]


def _to_uint8(values):
    return np.clip(np.round(values), 0, L - 1).astype(np.uint8)


def geometric_mean_filter(gray, kernel_size=3):
    """
    Geometric mean filter. Smooths about as well as the arithmetic mean but
    keeps a bit more detail.

    The product of 9 (or more) values up to 255 gets huge, so we use logs:
        product^(1/mn) = exp( mean of log(g) )

    log(0) is undefined, so black pixels are treated as 1 -- one black
    pixel still drags the result very dark, which is why this filter does
    poorly on pepper noise.
    """
    stack = neighborhood_stack(gray, kernel_size)
    stack = np.maximum(stack, 1.0)
    return _to_uint8(np.exp(np.mean(np.log(stack), axis=0)))


def contraharmonic_mean_filter(gray, kernel_size=3, q=1.5):
    """
    Contraharmonic mean filter of order Q (see module docstring for how to
    pick Q).

    Black pixels are treated as 1 so that 0 raised to a negative power
    (a division by zero) never happens.
    """
    stack = neighborhood_stack(gray, kernel_size)
    stack = np.maximum(stack, 1.0)
    numerator = np.sum(stack ** (q + 1), axis=0)
    denominator = np.sum(stack ** q, axis=0)
    return _to_uint8(numerator / denominator)
