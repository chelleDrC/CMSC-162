"""
Noise models for image degradation (Project 2 Guide 2, item a).

Degradation model (noise only, no blur):

    g(x, y) = f(x, y) + n(x, y)

f is the clean image, n is random noise, g is what we observe. Each function
below takes f and returns g, clipped back to the valid range [0, 255].

    add_salt_and_pepper_noise -- impulse noise: random pixels forced to 255 / 0
    add_gaussian_noise        -- n drawn from a normal (bell-curve) distribution
    add_rayleigh_noise        -- n drawn from a Rayleigh (skewed) distribution
"""

import numpy as np

L = 256  # intensity levels [0, 255]


def _to_uint8(values):
    """Clip to [0, 255] and convert back to an 8-bit image."""
    return np.clip(np.round(values), 0, L - 1).astype(np.uint8)


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
    rng = rng or np.random.default_rng()

    noisy = np.array(gray, dtype=np.uint8)  # copy, so the input is untouched
    u = rng.random(noisy.shape)

    pepper = u < pepper_prob
    salt = (u >= pepper_prob) & (u < pepper_prob + salt_prob)
    noisy[pepper] = 0
    noisy[salt] = L - 1
    return noisy


def add_gaussian_noise(gray, mean=0.0, sigma=20.0, rng=None):
    """
    Gaussian noise: n ~ Normal(mean, sigma^2).

        p(z) = 1 / (sqrt(2*pi) * sigma) * exp(-(z - mean)^2 / (2 * sigma^2))

    Most noise values fall within mean +/- 2*sigma, so a larger sigma means
    stronger, grainier noise.
    """
    rng = rng or np.random.default_rng()
    noise = rng.normal(loc=mean, scale=sigma, size=np.shape(gray))
    return _to_uint8(np.asarray(gray, dtype=np.float64) + noise)


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
    rng = rng or np.random.default_rng()
    u = rng.random(np.shape(gray))
    noise = a + np.sqrt(-b * np.log(1.0 - u))
    return _to_uint8(np.asarray(gray, dtype=np.float64) + noise)

