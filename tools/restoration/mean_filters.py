"""
Mean filters for noise removal (item b.ii).

Both filters replace each pixel with a kind of "average" of its k x k
neighborhood S_xy (mn = k*k pixels), computed from the noisy image g:

    Geometric mean:     f(x, y) = [ product of g(s, t) over S_xy ] ^ (1 / mn)

    Contraharmonic:     f(x, y) = sum of g(s, t)^(Q+1)  /  sum of g(s, t)^Q
                                  (both sums over S_xy)

Contraharmonic order Q:
    Q > 0  -> favors bright values: removes PEPPER (black) noise
    Q < 0  -> favors dark values:   removes SALT (white) noise
    Q = 0  -> arithmetic mean;  Q = -1 -> harmonic mean
"""

import math

from ._window import L, clamp_to_byte, filter_image


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
    log_of = [math.log(max(v, 1)) for v in range(L)]  # lookup table: log of each pixel value

    def window_value(window):
        return clamp_to_byte(math.exp(sum([log_of[v] for v in window]) / len(window)))

    return filter_image(gray, kernel_size, window_value)


def contraharmonic_mean_filter(gray, kernel_size=3, q=1.5):
    """
    Contraharmonic mean filter of order Q

    Black pixels are treated as 1 so that 0 raised to a negative power
    (a division by zero) never happens.
    """
    # Lookup tables: v^(Q+1) and v^Q for every possible pixel value v.
    upper = [max(v, 1) ** (q + 1) for v in range(L)]
    lower = [max(v, 1) ** q for v in range(L)]

    def window_value(window):
        numerator = sum([upper[v] for v in window])
        denominator = sum([lower[v] for v in window])
        return clamp_to_byte(numerator / denominator)

    return filter_image(gray, kernel_size, window_value)
