# PixelView

CMSC 162 - Project 1

A desktop image-viewer/editor shell built with Python's built-in `tkinter`.

## Status

UI skeleton with a working canvas viewport:

- **File** menu is interactive (dropdown opens/closes); Edit/View/Help are placeholders.
- **Canvas navigation**:
  - Pan: hold `Space` and drag with the left mouse button.
  - Zoom: scroll the mouse wheel, zooming toward the cursor position.
- **Layers panel**: shows a single placeholder layer for now.
- Everything else (toolbar tools, Add Layer, info panel values) is a visual placeholder to be wired up in later phases.

## Requirements

- Python 3 with `tkinter` (included in standard CPython installs; on some Linux distros install `python3-tk` separately).

## Running

```
python main.py
```

## Project 2 Guide 1 -- Image Compression (PCX / RLE / Huffman)

- **Open a PCX file**: `File > Import Image` and pick a `.pcx` (sample: `assets/sample_leaf_256.pcx`).
  The file is decoded by hand in `tools/compression/pcx.py` (128-byte header, run-length
  decoding of the image data, 256-color palette read from the last 769 bytes) and the
  reconstructed image is shown on the canvas. `File > Close` closes it.
- **Compress > PCX Header & Palette**: header fields, palette swatches (hover for index/RGB),
  and RLE section sizes. Opens automatically after importing a PCX.
- **Compress > Huffman Coding**: `Compress` Huffman-codes the reconstructed image
  (`tools/compression/huffman.py`) and shows bytes before/after, compression ratio
  `C = n1/n2`, relative data redundancy `R = 1 - 1/C`, and every pixel value with its
  Huffman code. `Save as .hfc...` writes the compressed file.
- **Compress > Open .hfc File...**: decodes a saved `.hfc` back onto the canvas.
