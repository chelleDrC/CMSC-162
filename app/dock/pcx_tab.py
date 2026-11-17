"""
PCX Info dock tab (Project 2 Guide 1, items b-c).

Three columns, mirroring the guide's sample output:
    - PCX Header Information: every field of the 128-byte header
    - Color Palette: the palette as a grid of swatches (hover for index/RGB)
    - Run-Length Decoding: how big the RLE section was vs. what it decoded to

The reconstructed (RLE-decoded) image itself is what's on the canvas.
"""

import tkinter as tk

from tools.compression.pcx import header_lines, HEADER_SIZE, PALETTE_SIZE
from ..theme import (
    BG_APP, BG_PANEL_ROW, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED,
    FONT_LABEL, FONT_LABEL_HEADER,
)


def _hex(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


class PcxTabMixin:
    def _build_pcx_tab(self, parent):
        pcx = self._pcx
        header = pcx["header"]

        content = tk.Frame(parent, bg=BG_APP)
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        def column(title, padx=(0, 24)):
            col = tk.Frame(content, bg=BG_APP)
            col.pack(side=tk.LEFT, fill=tk.Y, anchor="n", padx=padx)
            tk.Label(col, text=title, bg=BG_APP, fg=TEXT_SECONDARY,
                     font=FONT_LABEL_HEADER).pack(anchor="w", pady=(0, 6))
            return col

        # -- Header ---------------------------------------------------
        header_col = column("PCX HEADER INFORMATION")
        tk.Label(header_col, text="\n".join(header_lines(header)), bg=BG_APP,
                 fg=TEXT_PRIMARY, font=FONT_LABEL, justify=tk.LEFT).pack(anchor="w")

        # -- Palette --------------------------------------------------
        palette_col = column("COLOR PALETTE")
        palette = pcx["palette"]
        count = pcx["palette_size"]
        hover_label = tk.Label(palette_col, text="hover a swatch", bg=BG_APP,
                               fg=TEXT_DISABLED, font=FONT_LABEL, anchor="w")

        if palette is None or count == 0:
            tk.Label(palette_col, text="No palette --\n24-bit true color image\n"
                     "(R, G, B planes per scanline)", bg=BG_APP, fg=TEXT_DISABLED,
                     font=FONT_LABEL, justify=tk.LEFT).pack(anchor="w")
        else:
            per_row = 16 if count >= 16 else count
            rows = (count + per_row - 1) // per_row
            cell = self._sc(10 if count >= 256 else 20)
            grid = tk.Canvas(palette_col, width=per_row * cell, height=rows * cell,
                             bg=BG_PANEL_ROW, highlightbackground=BORDER,
                             highlightthickness=1)
            grid.pack(anchor="w")
            for i in range(count):
                r, c = divmod(i, per_row)
                grid.create_rectangle(c * cell, r * cell, (c + 1) * cell, (r + 1) * cell,
                                      fill=_hex(palette[i]), outline="")

            def on_hover(event):
                c = event.x // cell
                r = event.y // cell
                i = r * per_row + c
                if 0 <= c < per_row and 0 <= i < count:
                    rgb = palette[i]
                    hover_label.configure(text=f"Index {i}: ({rgb[0]}, {rgb[1]}, {rgb[2]})",
                                          fg=TEXT_PRIMARY)

            grid.bind("<Motion>", on_hover)
            grid.bind("<Leave>", lambda _e: hover_label.configure(text="hover a swatch",
                                                                  fg=TEXT_DISABLED))
            hover_label.pack(anchor="w", pady=(4, 0))
            tk.Label(palette_col, text=f"{count} colors, {pcx['palette_source']}",
                     bg=BG_APP, fg=TEXT_DISABLED, font=FONT_LABEL, wraplength=self._sc(180),
                     justify=tk.LEFT).pack(anchor="w")

        # -- RLE ------------------------------------------------------
        rle_col = column("RUN-LENGTH DECODING", padx=(0, 0))
        rle = pcx["rle_bytes_read"]
        decoded = pcx["decoded_bytes"]
        has_vga_palette = pcx["palette_size"] == 256 and "end of file" in (pcx["palette_source"] or "")
        lines = [
            f"File size: {pcx['file_size']:,} bytes",
            f"  Header: {HEADER_SIZE} bytes",
            f"  RLE image data: {rle:,} bytes",
        ]
        if has_vga_palette:
            lines.append(f"  Palette: 1 + {PALETTE_SIZE} bytes")
        lines += [
            "",
            f"Decoded scanlines: {decoded:,} bytes",
            f"  = {header['height']} rows x {header['num_planes']} plane(s)",
            f"     x {header['bytes_per_line']} bytes/line",
            f"RLE ratio (decoded / encoded): {decoded / rle:.3f}" if rle else "",
            "",
            f"Reconstructed: {pcx['width']} x {pcx['height']} px (shown on canvas)",
        ]
        tk.Label(rle_col, text="\n".join(lines), bg=BG_APP, fg=TEXT_PRIMARY,
                 font=FONT_LABEL, justify=tk.LEFT).pack(anchor="w")
