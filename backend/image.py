"""
Lab 1: enable opening of file and display RGB value of a pixel
"""

from tkinter import filedialog
from PIL import Image
import os


IMAGE_FILETYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.tiff *.tif"),
    ("JPEG", "*.jpg *.jpeg"),
    ("PNG", "*.png"),
    ("TIFF", "*.tiff *.tif"),
    ("All files", "*.*"),
]


def open_image_dialog():
    path = filedialog.askopenfilename(
        title="Import Image",
        filetypes=IMAGE_FILETYPES,
    )
    return path or None


def load_image(path):
    try:
        img = Image.open(path)
        img.load()
        return img.convert("RGB")
    except Exception:
        return None

# Show ource file's original color mode since load_image() always converts to RGB
def peek_image_mode(path):
    try:
        with Image.open(path) as img:
            return img.mode
    except Exception:
        return None


def canvas_to_image_coords(canvas_x, canvas_y, canvas_w, canvas_h, img_w, img_h, zoom, offset_x, offset_y):
    cx = canvas_w / 2 + offset_x
    cy = canvas_h / 2 + offset_y
    pw = img_w * zoom
    ph = img_h * zoom
    x0 = cx - pw / 2
    y0 = cy - ph / 2

    image_x = int((canvas_x - x0) / zoom)
    image_y = int((canvas_y - y0) / zoom)
    return image_x, image_y


def get_pixel_rgb(image, x, y):
    if image is None:
        return None
    if x < 0 or y < 0 or x >= image.width or y >= image.height:
        return None
    return image.getpixel((x, y))


def _format_file_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024


def get_image_metadata(path, image, original_mode=None):
    w, h = image.size
    dpi = image.info.get("dpi")
    resolution = f"{round(dpi[0])} x {round(dpi[1])} DPI" if dpi else "\u2014"
    ext = os.path.splitext(path)[1].lstrip(".").upper() or "\u2014"
    try:
        size_str = _format_file_size(os.path.getsize(path))
    except OSError:
        size_str = "\u2014"

    return {
        "dimensions": f"{w} x {h} px",
        "resolution": resolution,
        "color_mode": original_mode or image.mode,
        "file_type": ext,
        "file_size": size_str,
    }
