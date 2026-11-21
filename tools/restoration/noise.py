"""
Noise models for image degradation (item a).

Degradation model (noise only, no blur):

    g(x, y) = f(x, y) + n(x, y)

f is the clean image, n is random noise, g is what we observe. Each function
below takes f (a list of rows of 0-255 ints) and returns g, clipped back to
the valid range [0, 255].

    add_salt_and_pepper_noise -- impulse noise: random pixels forced to 255 / 0
    add_gaussian_noise        -- n drawn from a normal (bell-curve) distribution
    add_rayleigh_noise        -- n drawn from a Rayleigh (skewed) distribution
"""

import math
import random

from ._window import L, clamp_to_byte


def add_salt_and_pepper_noise(gray, salt_prob=0.05, pepper_prob=0.05, rng=None):
    """
    Salt-and-pepper (impulse) noise.

    Every pixel independently becomes:
        white (255, "salt")   with probability salt_prob
        black (0,   "pepper") with probability pepper_prob
        unchanged             otherwise

    How: draw one uniform random number u in [0, 1) per pixel.
        u < pepper_prob                         -> pepper
        pepper_prob <= u < pepper_prob + salt_prob -> salt
    """
    if salt_prob < 0 or pepper_prob < 0 or salt_prob + pepper_prob > 1:
        raise ValueError("Probabilities must be >= 0 and add up to at most 1.")
    rng = rng or random.Random()

    noisy = []
    for row in gray:
        new_row = []
        for pixel in row:
            u = rng.random()
            if u < pepper_prob:
                new_row.append(0)
            elif u < pepper_prob + salt_prob:
                new_row.append(L - 1)
            else:
                new_row.append(pixel)
        noisy.append(new_row)
    return noisy


def add_gaussian_noise(gray, mean=0.0, sigma=20.0, rng=None):
    """
    Gaussian noise:

        p(z) = 1 / (sqrt(2*pi) * sigma) * exp(-(z - mean)^2 / (2 * sigma^2))
    """
    rng = rng or random.Random()
    return [[clamp_to_byte(pixel + rng.gauss(mean, sigma)) for pixel in row]
            for row in gray]


def add_rayleigh_noise(gray, a=0.0, b=800.0, rng=None):
    """
    Rayleigh noise with parameters a (offset) and b (spread), as in
    Gonzalez & Woods:

        p(z) = (2 / b) * (z - a) * exp(-(z - a)^2 / b)   for z >= a, else 0
        mean     = a + sqrt(pi * b / 4)
        variance = b * (4 - pi) / 4

    Sampling (inverse-transform method): the cumulative distribution is
        F(z) = 1 - exp(-(z - a)^2 / b)
    Setting F(z) = u for a uniform random u in [0, 1) and solving for z gives
        z = a + sqrt(-b * ln(1 - u))
    so uniform random numbers can be turned straight into Rayleigh ones.

    Note: Rayleigh noise is always >= a, so it also brightens the image on
    average (by its mean) -- the histogram shifts right and is skewed.
    """
    if b <= 0:
        raise ValueError("b must be positive.")
    rng = rng or random.Random()

    noisy = []
    for row in gray:
        new_row = []
        for pixel in row:
            u = rng.random()
            new_row.append(clamp_to_byte(pixel + a + math.sqrt(-b * math.log(1.0 - u))))
        noisy.append(new_row)
    return noisy
