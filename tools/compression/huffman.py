"""
Project 2 Guide 1 (item d): Huffman coding of the reconstructed image.

Huffman coding is a lossless, variable-length code: pixel values that
appear often get short bit codes, rare values get long ones. Steps:

    1. Count how often every pixel value (0-255) appears.
    2. Make one leaf node per value that actually appears.
    3. Repeatedly take the TWO nodes with the smallest counts and join them
       under a new parent whose count is their sum, until one node (the
       root) is left.
    4. Walk from the root to every leaf: going left adds a "0", going right
       adds a "1". The path to a leaf is that pixel value's Huffman code.
    5. Replace every pixel with its code and pack the bits into bytes.

The "symbols" being coded are the bytes of the reconstructed image:
    - indexed (256-color) PCX: one palette index per pixel
    - 24-bit images: the R, G and B byte of every pixel

Compression measures (Gonzalez & Woods, Ch. 8):
    compression ratio           C = n1 / n2
    relative data redundancy    R = 1 - 1 / C
where n1 = bytes of pixel data before compression and n2 = bytes of
Huffman-coded data after. (The .hfc file's header/palette/table overhead
is reported on its own so it doesn't hide what the coding itself saves.)

.hfc file layout (all numbers little-endian):

    "HFC1"                    4 bytes   magic / format version
    mode                      1 byte    1 = indexed (palette), 3 = RGB
    width, height             4 + 4     image size in pixels
    palette                   768       only when mode = 1
    symbol count              2         how many distinct values follow
    (value, frequency) pairs  1 + 4     per symbol -- enough for the decoder
                                        to rebuild the exact same tree
    bit count                 8         number of meaningful bits in the data
    encoded data              ...       Huffman bitstream, last byte 0-padded
"""

import math


MAGIC = b"HFC1"
MODE_INDEXED = 1
MODE_RGB = 3


# ----------------------------------------------------------------------
# 1. Frequencies
# ----------------------------------------------------------------------
def count_frequencies(symbols):
    """frequencies[v] = how many times byte value v appears in symbols."""
    frequencies = [0] * 256
    for value in symbols:
        frequencies[value] += 1
    return frequencies


# ----------------------------------------------------------------------
# 2-3. Building the tree
# ----------------------------------------------------------------------
class HuffmanNode:
    def __init__(self, frequency, order, symbol=None, left=None, right=None):
        self.frequency = frequency
        self.order = order      # creation order -- breaks ties the same way every time
        self.symbol = symbol    # pixel value for leaves, None for internal nodes
        self.left = left
        self.right = right

    def is_leaf(self):
        return self.left is None and self.right is None


def _pop_smallest(nodes):
    """Remove and return the node with the smallest frequency (oldest wins ties)."""
    best = 0
    for i in range(1, len(nodes)):
        a = nodes[i]
        b = nodes[best]
        if a.frequency < b.frequency or (a.frequency == b.frequency and a.order < b.order):
            best = i
    return nodes.pop(best)


def build_tree(frequencies):
    """
    Join the two least-frequent nodes over and over until one root remains.
    Deterministic, so the decoder rebuilds the identical tree from the
    frequency table stored in the .hfc file.
    """
    nodes = []
    order = 0
    for value in range(256):
        if frequencies[value] > 0:
            nodes.append(HuffmanNode(frequencies[value], order, symbol=value))
            order += 1

    if not nodes:
        raise ValueError("Cannot Huffman-code an empty image.")

    while len(nodes) > 1:
        first = _pop_smallest(nodes)
        second = _pop_smallest(nodes)
        parent = HuffmanNode(first.frequency + second.frequency, order,
                             left=first, right=second)
        order += 1
        nodes.append(parent)

    return nodes[0]


# ----------------------------------------------------------------------
# 4. Codes
# ----------------------------------------------------------------------
def build_codes(root):
    """
    Walk the tree: left edge = "0", right edge = "1".
    Returns {pixel value: code string}, e.g. {12: "010", 200: "1"}.
    """
    codes = {}
    if root.is_leaf():
        # Only one distinct value in the whole image: give it a 1-bit code.
        codes[root.symbol] = "0"
        return codes

    stack = [(root, "")]
    while stack:
        node, path = stack.pop()
        if node.is_leaf():
            codes[node.symbol] = path
        else:
            stack.append((node.right, path + "1"))
            stack.append((node.left, path + "0"))
    return codes


# ----------------------------------------------------------------------
# 5. Encoding / decoding the bitstream
# ----------------------------------------------------------------------
def encode(symbols, codes):
    """
    Replace every symbol by its code and pack the bits into bytes, most
    significant bit first. Returns (bytes, number_of_bits).
    """
    # Pre-convert "0101" strings to (integer, length) so packing is just shifts.
    table = {}
    for value, code in codes.items():
        table[value] = (int(code, 2), len(code))

    out = bytearray()
    buffer = 0        # bits waiting to be written
    buffered = 0      # how many bits are in buffer
    total_bits = 0
    for value in symbols:
        code_value, code_length = table[value]
        buffer = (buffer << code_length) | code_value
        buffered += code_length
        total_bits += code_length
        while buffered >= 8:
            buffered -= 8
            out.append((buffer >> buffered) & 0xFF)
        buffer &= (1 << buffered) - 1

    if buffered > 0:
        # Pad the last byte with zeros on the right.
        out.append((buffer << (8 - buffered)) & 0xFF)
    return bytes(out), total_bits


def decode(data, bit_count, root, symbol_count):
    """Walk the tree bit by bit: 0 = go left, 1 = go right, leaf = output its value."""
    if root.is_leaf():
        return [root.symbol] * symbol_count

    symbols = []
    node = root
    bits_read = 0
    for byte in data:
        for shift in range(7, -1, -1):
            if bits_read == bit_count:
                return symbols
            bits_read += 1
            bit = (byte >> shift) & 1
            node = node.right if bit else node.left
            if node.is_leaf():
                symbols.append(node.symbol)
                node = root
    return symbols


# ----------------------------------------------------------------------
# Whole-image compression + statistics
# ----------------------------------------------------------------------
def compress(mode, width, height, pixels, palette=None):
    """
    Huffman-code a reconstructed image.

    mode    -- "P" (pixels are palette indices) or "RGB" (pixels are r,g,b,...)
    pixels  -- flat list of byte values

    Returns a dict with the codes, frequencies, encoded bytes, the full
    .hfc file contents and the compression statistics.
    """
    frequencies = count_frequencies(pixels)
    root = build_tree(frequencies)
    codes = build_codes(root)
    encoded, bit_count = encode(pixels, codes)
    hfc_bytes = pack_hfc(mode, width, height, palette, frequencies, encoded, bit_count)

    # n1 = the reconstructed pixel data (1 byte per value), n2 = the same
    # data after Huffman coding. This isolates what the coding itself saves.
    bytes_before = len(pixels)
    bytes_after = len(encoded)
    stats = compression_stats(bytes_before, bytes_after)
    stats["bit_count"] = bit_count
    # The .hfc file also carries a header, the palette and the frequency
    # table so it can be decoded on its own -- reported separately.
    stats["hfc_file_bytes"] = len(hfc_bytes)
    stats["hfc_overhead_bytes"] = len(hfc_bytes) - len(encoded)
    stats["average_code_length"] = bit_count / len(pixels)
    stats["entropy"] = entropy(frequencies, len(pixels))

    table = []
    for value in sorted(codes, key=lambda v: (-frequencies[v], v)):
        table.append({
            "value": value,
            "frequency": frequencies[value],
            "code": codes[value],
        })

    return {
        "mode": mode,
        "width": width,
        "height": height,
        "palette": palette,
        "frequencies": frequencies,
        "codes": codes,
        "table": table,
        "encoded": encoded,
        "hfc_bytes": hfc_bytes,
        "stats": stats,
    }


def compression_stats(bytes_before, bytes_after):
    ratio = bytes_before / bytes_after
    redundancy = 1 - (1 / ratio)
    return {
        "bytes_before": bytes_before,
        "bytes_after": bytes_after,
        "compression_ratio": ratio,
        "relative_redundancy": redundancy,
    }


def entropy(frequencies, total):
    """Shannon entropy in bits/symbol -- the lower bound Huffman gets close to."""
    h = 0.0
    for count in frequencies:
        if count > 0:
            p = count / total
            h -= p * math.log2(p)
    return h


# ----------------------------------------------------------------------
# .hfc file read/write
# ----------------------------------------------------------------------
def _le(number, size):
    return number.to_bytes(size, "little")


def pack_hfc(mode, width, height, palette, frequencies, encoded, bit_count):
    out = bytearray()
    out += MAGIC
    out.append(MODE_INDEXED if mode == "P" else MODE_RGB)
    out += _le(width, 4)
    out += _le(height, 4)
    if mode == "P":
        for i in range(256):
            r, g, b = palette[i] if i < len(palette) else (0, 0, 0)
            out.append(r)
            out.append(g)
            out.append(b)

    used = [v for v in range(256) if frequencies[v] > 0]
    out += _le(len(used), 2)
    for value in used:
        out.append(value)
        out += _le(frequencies[value], 4)

    out += _le(bit_count, 8)
    out += encoded
    return bytes(out)


def save_hfc(path, result):
    with open(path, "wb") as f:
        f.write(result["hfc_bytes"])


def unpack_hfc(data):
    """Inverse of pack_hfc: returns (mode, width, height, pixels, palette)."""
    if data[:4] != MAGIC:
        raise ValueError("Not a .hfc file (missing HFC1 signature).")
    pos = 4
    mode_byte = data[pos]
    pos += 1
    if mode_byte not in (MODE_INDEXED, MODE_RGB):
        raise ValueError(f"Unknown .hfc image mode {mode_byte}.")
    mode = "P" if mode_byte == MODE_INDEXED else "RGB"

    width = int.from_bytes(data[pos:pos + 4], "little")
    pos += 4
    height = int.from_bytes(data[pos:pos + 4], "little")
    pos += 4

    palette = None
    if mode == "P":
        palette = []
        for i in range(256):
            palette.append((data[pos], data[pos + 1], data[pos + 2]))
            pos += 3

    symbol_count = int.from_bytes(data[pos:pos + 2], "little")
    pos += 2
    frequencies = [0] * 256
    for _ in range(symbol_count):
        value = data[pos]
        frequencies[value] = int.from_bytes(data[pos + 1:pos + 5], "little")
        pos += 5

    bit_count = int.from_bytes(data[pos:pos + 8], "little")
    pos += 8

    total_symbols = width * height * (1 if mode == "P" else 3)
    root = build_tree(frequencies)
    pixels = decode(data[pos:], bit_count, root, total_symbols)
    if len(pixels) != total_symbols:
        raise ValueError(f".hfc data is truncated: got {len(pixels)} of {total_symbols} values.")
    return mode, width, height, pixels, palette


def load_hfc(path):
    with open(path, "rb") as f:
        return unpack_hfc(f.read())
