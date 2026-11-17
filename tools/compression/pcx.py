"""
Project 2 Guide 1 (items a-c): read a PCX file by hand.

A PCX file has three parts:

    +-----------------------------+
    | Header        (128 bytes)   |  fixed-position fields, little-endian
    +-----------------------------+
    | Image data    (RLE bytes)   |  scanlines compressed with run-length encoding
    +-----------------------------+
    | 0x0C marker + palette       |  only for 256-color (8-bit, 1-plane) files:
    | (1 + 768 bytes)             |  256 colors x 3 bytes (R, G, B)
    +-----------------------------+

Everything here is decoded manually from the raw bytes (no Image.open on
the .pcx) so the header layout, the RLE rule and the palette lookup can be
walked through step by step in the report. Pillow is only used at the very
end to turn the decoded pixel list into something the canvas can show.

Supported layouts:
    - 8 bits/pixel, 1 plane  -> 256-color indexed (palette at end of file),
                                or grayscale if the file has no palette
    - 8 bits/pixel, 3 planes -> 24-bit RGB (one R, G, B plane per scanline)
    - 1 bit/pixel, 1-4 planes -> monochrome / 16-color EGA (16-color
                                palette stored inside the header)
"""

import os

from PIL import Image


HEADER_SIZE = 128
PALETTE_SIZE = 768        # 256 colors * 3 bytes
PALETTE_MARKER = 0x0C     # the byte right before the 256-color palette
RLE_FLAG = 0xC0           # top two bits set (11xxxxxx) = "this is a run count"
RLE_COUNT_MASK = 0x3F     # bottom six bits = how many times to repeat


# ----------------------------------------------------------------------
# Small helpers for reading the header's little-endian numbers
# ----------------------------------------------------------------------
def read_byte(data, offset):
    return data[offset]


def read_word(data, offset):
    """2-byte little-endian unsigned number: low byte first, then high byte."""
    low = data[offset]
    high = data[offset + 1]
    return low + high * 256


# ----------------------------------------------------------------------
# Step b: header
# ----------------------------------------------------------------------
def parse_header(data):
    """
    Pull every field out of the 128-byte PCX header.

    Byte offsets follow the ZSoft PCX specification:

        0   Manufacturer      (always 10 = ZSoft .pcx)
        1   Version           (0, 2, 3, 4 or 5)
        2   Encoding          (1 = run-length encoding)
        3   Bits per pixel    (per plane: 1, 2, 4 or 8)
        4   Xmin, Ymin, Xmax, Ymax   (4 words) -> image dimensions
        12  HDpi, VDpi        (2 words)
        16  Colormap          (48 bytes: 16-color EGA palette)
        64  Reserved
        65  Number of color planes
        66  Bytes per line    (per plane, always even)
        68  Palette info      (1 = color/BW, 2 = grayscale)
        70  Horizontal screen size, Vertical screen size (2 words)
        74  Filler            (54 bytes, blank)
    """
    if len(data) < HEADER_SIZE:
        raise ValueError("File is too small to be a PCX file (needs a 128-byte header).")

    header = {
        "manufacturer": read_byte(data, 0),
        "version": read_byte(data, 1),
        "encoding": read_byte(data, 2),
        "bits_per_pixel": read_byte(data, 3),
        "xmin": read_word(data, 4),
        "ymin": read_word(data, 6),
        "xmax": read_word(data, 8),
        "ymax": read_word(data, 10),
        "hdpi": read_word(data, 12),
        "vdpi": read_word(data, 14),
        "reserved": read_byte(data, 64),
        "num_planes": read_byte(data, 65),
        "bytes_per_line": read_word(data, 66),
        "palette_info": read_word(data, 68),
        "hscreen_size": read_word(data, 70),
        "vscreen_size": read_word(data, 72),
    }

    # The 16-color EGA palette lives inside the header (bytes 16-63).
    header_palette = []
    for i in range(16):
        start = 16 + i * 3
        header_palette.append((data[start], data[start + 1], data[start + 2]))
    header["header_palette"] = header_palette

    if header["manufacturer"] != 10:
        raise ValueError(f"Not a ZSoft PCX file (manufacturer byte is {header['manufacturer']}, expected 10).")
    if header["encoding"] != 1:
        raise ValueError(f"Unsupported PCX encoding {header['encoding']} (only RLE = 1 is defined).")

    header["width"] = header["xmax"] - header["xmin"] + 1
    header["height"] = header["ymax"] - header["ymin"] + 1
    if header["width"] <= 0 or header["height"] <= 0:
        raise ValueError("PCX header has invalid image dimensions.")
    return header


def header_lines(header):
    """The header as display-ready "Label: value" lines (matches the guide's sample output)."""
    return [
        f"Manufacturer: Zsoft .pcx ({header['manufacturer']})",
        f"Version: {header['version']}",
        f"Encoding: {header['encoding']}",
        f"Bits per Pixel: {header['bits_per_pixel']}",
        f"Image Dimensions: {header['xmin']} {header['ymin']} {header['xmax']} {header['ymax']}",
        f"HDPI: {header['hdpi']}",
        f"VDPI: {header['vdpi']}",
        f"Number of Color Planes: {header['num_planes']}",
        f"Bytes per Line: {header['bytes_per_line']}",
        f"Palette Information: {header['palette_info']}",
        f"Horizontal Screen Size: {header['hscreen_size']}",
        f"Vertical Screen Size: {header['vscreen_size']}",
    ]


# ----------------------------------------------------------------------
# Step b: 256-color palette at the end of the file
# ----------------------------------------------------------------------
def read_vga_palette(data):
    """
    "To read the color palette, seek to the end of the file and count back
    769 bytes." That byte must be the 0x0C marker; the 768 bytes after it
    are 256 (R, G, B) triples. Returns None if the marker isn't there.
    """
    if len(data) < HEADER_SIZE + PALETTE_SIZE + 1:
        return None
    marker_pos = len(data) - (PALETTE_SIZE + 1)
    if data[marker_pos] != PALETTE_MARKER:
        return None

    palette = []
    for i in range(256):
        start = marker_pos + 1 + i * 3
        palette.append((data[start], data[start + 1], data[start + 2]))
    return palette


# ----------------------------------------------------------------------
# Step c: run-length decoding
# ----------------------------------------------------------------------
def rle_decode(data, start, end, expected_bytes):
    """
    Undo PCX run-length encoding.

    Read one byte at a time:
      * If its top two bits are both 1 (byte >= 0xC0), the low six bits
        are a repeat COUNT and the NEXT byte is the VALUE to repeat.
      * Otherwise the byte is a single literal pixel value (count = 1).

    Decoding stops once expected_bytes have been produced (height * planes
    * bytes_per_line), so the palette at the end of the file is never
    mistaken for image data.
    """
    decoded = bytearray()
    pos = start
    while len(decoded) < expected_bytes and pos < end:
        byte = data[pos]
        pos += 1

        if (byte & RLE_FLAG) == RLE_FLAG:
            count = byte & RLE_COUNT_MASK
            if pos >= end:
                break
            value = data[pos]
            pos += 1
        else:
            count = 1
            value = byte

        for _ in range(count):
            decoded.append(value)

    if len(decoded) < expected_bytes:
        raise ValueError(
            f"PCX image data ended early: decoded {len(decoded)} of {expected_bytes} bytes."
        )
    # A run may spill past the last scanline; anything extra is not pixel data.
    return decoded[:expected_bytes], pos - start


# ----------------------------------------------------------------------
# Turning decoded scanlines into pixels
# ----------------------------------------------------------------------
def _unpack_bit_planes(decoded, header):
    """
    1-bit-per-pixel files (monochrome or 16-color EGA) store each scanline
    as N separate bit planes. Pixel x's color index is built by taking bit
    x from every plane: plane 0 is bit 0 of the index, plane 1 is bit 1, ...
    """
    width = header["width"]
    height = header["height"]
    planes = header["num_planes"]
    bpl = header["bytes_per_line"]

    indices = []
    for row in range(height):
        line_start = row * planes * bpl
        for x in range(width):
            byte_index = x // 8
            bit_shift = 7 - (x % 8)       # leftmost pixel is the highest bit
            index = 0
            for plane in range(planes):
                byte = decoded[line_start + plane * bpl + byte_index]
                bit = (byte >> bit_shift) & 1
                index = index + (bit << plane)
            indices.append(index)
    return indices


def read_pcx(path):
    """
    Open a PCX file and decode it completely.

    Returns a dict:
        path, file_size
        header            -- every header field (see parse_header)
        mode              -- "P" (indexed, one byte per pixel) or "RGB"
        palette           -- list of 256 (r, g, b) tuples for "P", else None
        palette_source    -- where the palette came from (for the UI)
        palette_size      -- how many palette entries are meaningful (256, 16, 2; 0 for RGB)
        pixels            -- flat list: one palette index per pixel ("P"),
                             or r, g, b, r, g, b, ... ("RGB")
        width, height
        rle_bytes_read    -- size of the compressed image-data section
        decoded_bytes     -- size of the decoded scanline data
        image             -- RGB PIL image of the reconstructed picture
    """
    with open(path, "rb") as f:
        data = f.read()

    header = parse_header(data)
    width = header["width"]
    height = header["height"]
    bpp = header["bits_per_pixel"]
    planes = header["num_planes"]
    bpl = header["bytes_per_line"]

    # Where the RLE section ends: just before the 256-color palette, if there is one.
    palette = None
    palette_source = None
    palette_size = 256
    data_end = len(data)
    if bpp == 8 and planes == 1:
        palette = read_vga_palette(data)
        if palette is not None:
            palette_source = "256-color palette (end of file)"
            data_end = len(data) - (PALETTE_SIZE + 1)

    expected = height * planes * bpl
    decoded, rle_bytes_read = rle_decode(data, HEADER_SIZE, data_end, expected)

    if bpp == 8 and planes == 1:
        mode = "P"
        pixels = []
        for row in range(height):
            line_start = row * bpl
            for x in range(width):
                pixels.append(decoded[line_start + x])
        if palette is None:
            # No palette in the file: treat the bytes as gray levels.
            palette = [(i, i, i) for i in range(256)]
            palette_source = "none in file (grayscale assumed)"

    elif bpp == 8 and planes == 3:
        # 24-bit: each scanline is the full R plane, then G, then B.
        mode = "RGB"
        pixels = []
        for row in range(height):
            line_start = row * 3 * bpl
            for x in range(width):
                pixels.append(decoded[line_start + x])               # R
                pixels.append(decoded[line_start + bpl + x])         # G
                pixels.append(decoded[line_start + 2 * bpl + x])     # B

    elif bpp == 1 and 1 <= planes <= 4:
        mode = "P"
        pixels = _unpack_bit_planes(decoded, header)
        palette_size = 2 ** planes
        if planes == 1:
            palette = [(0, 0, 0), (255, 255, 255)]
            palette_source = "monochrome (black / white)"
        else:
            palette = list(header["header_palette"])
            palette_source = "16-color palette (header bytes 16-63)"
        palette = palette + [(0, 0, 0)] * (256 - len(palette))

    else:
        raise ValueError(
            f"Unsupported PCX layout: {bpp} bits/pixel with {planes} plane(s)."
        )

    image = build_image(mode, width, height, pixels, palette)

    return {
        "path": path,
        "file_size": len(data),
        "header": header,
        "mode": mode,
        "palette": palette if mode == "P" else None,
        "palette_source": palette_source if mode == "P" else "none (24-bit true color)",
        "palette_size": palette_size if mode == "P" else 0,
        "pixels": pixels,
        "width": width,
        "height": height,
        "rle_bytes_read": rle_bytes_read,
        "decoded_bytes": expected,
        "image": image,
    }


def build_image(mode, width, height, pixels, palette=None):
    """Turn a flat pixel list (indices or RGB triples) into an RGB PIL image for display."""
    if mode == "P":
        rgb = bytearray()
        for index in pixels:
            r, g, b = palette[index]
            rgb.append(r)
            rgb.append(g)
            rgb.append(b)
        return Image.frombytes("RGB", (width, height), bytes(rgb))
    return Image.frombytes("RGB", (width, height), bytes(pixels))


def is_pcx_path(path):
    return os.path.splitext(path)[1].lower() == ".pcx"
