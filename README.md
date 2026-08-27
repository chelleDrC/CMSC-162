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
