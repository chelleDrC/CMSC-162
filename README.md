> [!WARNING]
> **DO NOT MERGE THIS BRANCH INTO `main`.**
> This branch contains **only** the Project 2 Guide 2 files. The PixelView app
> (Project 1 and Project 2 Guide 1 code) was deleted here on purpose, so merging
> would delete the team's code from `main`. Use this branch for the Guide 2
> submission only.

# Noise & Restoration

CMSC 162 - Project 2 Guide 2: Image Degradation and Restoration

A small desktop app (Python + `tkinter`) that adds noise to an image and then
restores it with spatial filters.

## Requirements

- Python 3 with `tkinter` (included in standard CPython installs)
- `pip install -r requirements.txt` (Pillow, numpy)

## Running

```
python restoration_app.py
```

## How to use

1. **Open Image** -- the image is converted to grayscale and shown in the *Original* card
   (sample: `assets/leaf spot disease.jpeg`).
2. **Degrade** (item a) -- choose *Salt & Pepper* (set the salt and pepper probabilities),
   *Gaussian* (mean, sigma) or *Rayleigh* (a, b), then **Add Noise**. The *Degraded* card
   shows the noisy image and its histogram (item b.i). Drag on the degraded image to see
   the histogram of just that patch; click it to go back to the whole image.
3. **Restore** (item b.ii) -- choose *Geometric* mean, *Contraharmonic* mean (set **Q**:
   Q > 0 removes pepper, Q < 0 removes salt) or *Median* (order-statistic), pick a kernel
   size, then **Apply Filter**. **Apply Again** filters the result again (2nd, 3rd pass...).

## Code layout

- `restoration_app.py` -- entry point
- `tools/restoration/noise.py` -- the three noise models
- `tools/restoration/mean_filters.py` -- geometric and contraharmonic mean filters
- `tools/restoration/order_statistics.py` -- median filter
- `tools/restoration/_window.py` -- shared helper that collects every pixel's k x k neighborhood
- `restoration_ui/` -- the window (`window.py`), its widgets (`widgets.py`) and colors (`theme.py`)
