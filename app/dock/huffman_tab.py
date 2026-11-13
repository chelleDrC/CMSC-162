"""
Huffman dock tab (Project 2 Guide 1, item d).

Huffman-codes the reconstructed image, then shows what the guide asks for:
bytes before/after, compression ratio, relative data redundancy, and every
pixel value with its Huffman code. "Save as .hfc" writes the compressed
file (format documented in tools/compression/huffman.py).

What gets coded:
    - a PCX (or .hfc) indexed image -> its palette indices, one per pixel
    - any other image               -> its R, G, B bytes
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from tools.compression import huffman
from ..theme import (
    BG_APP, BG_PANEL_ROW, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED,
    FONT_LABEL, FONT_LABEL_HEADER, ACCENT_BLUE,
)

# Decoding back to check losslessness is ~4x slower than encoding in pure
# Python, so it's skipped for very large images to keep the tab responsive.
VERIFY_LIMIT = 3_000_000


class HuffmanTabMixin:
    def _huffman_source(self):
        """(mode, width, height, pixels, palette, description) for the current image."""
        src = getattr(self, "_compress_source", None)
        if src is not None:
            return (src["mode"], src["width"], src["height"], src["pixels"],
                    src["palette"], src["label"])
        img = self.image
        return ("RGB", img.width, img.height, img.tobytes(), None,
                f"Imported image, {img.width} x {img.height} px, 24-bit RGB (R, G, B bytes)")

    def _build_huffman_tab(self, parent):
        mode, width, height, pixels, palette, label = self._huffman_source()
        state = {"result": None, "busy": False}

        content = tk.Frame(parent, bg=BG_APP)
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # -- Left: controls + statistics ------------------------------
        left = tk.Frame(content, bg=BG_APP, width=self._sc(330))
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        tk.Label(left, text="Huffman coding -- frequent pixel values get short codes, "
                 "rare ones get long codes (lossless).", bg=BG_APP, fg=TEXT_DISABLED,
                 font=FONT_LABEL, wraplength=self._sc(320), justify=tk.LEFT
                 ).pack(anchor="w")
        tk.Label(left, text=f"Source: {label}", bg=BG_APP, fg=TEXT_SECONDARY,
                 font=FONT_LABEL, wraplength=self._sc(320), justify=tk.LEFT
                 ).pack(anchor="w", pady=(4, 0))

        buttons_row = tk.Frame(left, bg=BG_APP)
        buttons_row.pack(fill=tk.X, pady=(8, 0))
        compress_btn = tk.Label(buttons_row, text="Compress", bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                                font=FONT_LABEL, cursor="hand2", padx=10, pady=4)
        compress_btn.pack(side=tk.LEFT, padx=(0, 4))
        compress_btn.bind("<Button-1>", lambda _e: run_compress())

        save_btn = tk.Label(buttons_row, text="Save as .hfc…", bg=BG_PANEL_ROW,
                            fg=TEXT_DISABLED, font=FONT_LABEL, cursor="hand2", padx=10, pady=4)
        save_btn.pack(side=tk.LEFT)
        save_btn.bind("<Button-1>", lambda _e: save())

        stats_label = tk.Label(left, text="Press Compress to run Huffman coding.", bg=BG_APP,
                               fg=TEXT_DISABLED, font=FONT_LABEL, justify=tk.LEFT, anchor="nw")
        stats_label.pack(anchor="w", fill=tk.X, pady=(8, 0))

        # -- Right: pixel value -> code table -------------------------
        right = tk.Frame(content, bg=BG_APP)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))
        tk.Label(right, text="PIXEL VALUES AND HUFFMAN CODES", bg=BG_APP, fg=TEXT_SECONDARY,
                 font=FONT_LABEL_HEADER).pack(anchor="w", pady=(0, 4))

        table_wrap = tk.Frame(right, bg=BG_PANEL_ROW, highlightbackground=BORDER,
                              highlightthickness=1)
        table_wrap.pack(fill=tk.BOTH, expand=True)
        table = tk.Text(table_wrap, bg=BG_PANEL_ROW, fg=TEXT_PRIMARY, font=("Consolas", 9),
                        relief=tk.FLAT, wrap=tk.NONE, borderwidth=0, padx=6, pady=4,
                        insertwidth=0, cursor="arrow")
        scroll = tk.Scrollbar(table_wrap, orient=tk.VERTICAL, command=table.yview)
        table.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        table.tag_configure("head", foreground=TEXT_SECONDARY)
        table.configure(state=tk.DISABLED)

        def fill_table(result):
            table.configure(state=tk.NORMAL)
            table.delete("1.0", tk.END)
            if mode == "P":
                table.insert(tk.END, "Index  Color  RGB             Count     Bits  Huffman code\n", "head")
            else:
                table.insert(tk.END, "Value  Count      Bits  Huffman code\n", "head")
            for row in result["table"]:
                v = row["value"]
                code = row["code"]
                if mode == "P":
                    rgb = palette[v]
                    color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                    tag = f"sw{v}"
                    table.tag_configure(tag, background=color)
                    table.insert(tk.END, f"{v:>5}  ")
                    table.insert(tk.END, "    ", tag)
                    rgb_text = f"({rgb[0]},{rgb[1]},{rgb[2]})"
                    table.insert(tk.END, f"   {rgb_text:<15} {row['frequency']:>8}  {len(code):>4}  {code}\n")
                else:
                    table.insert(tk.END, f"{v:>5}  {row['frequency']:>9}  {len(code):>4}  {code}\n")
            table.configure(state=tk.DISABLED)

        def show_stats(result, verified, saved_path=None):
            s = result["stats"]
            lines = [
                f"Bytes before compression:  {s['bytes_before']:,}",
                f"Bytes after compression:   {s['bytes_after']:,}",
                f"Compression ratio (C = n1/n2):   {s['compression_ratio']:.4f} : 1",
                f"Relative data redundancy (R = 1 - 1/C):  {s['relative_redundancy']:.4f}"
                f"  ({s['relative_redundancy'] * 100:.2f}%)",
                f"Avg. code length: {s['average_code_length']:.4f} bits/value  "
                f"(entropy {s['entropy']:.4f})",
                f"Distinct values coded: {len(result['codes'])}",
                f".hfc file size: {s['hfc_file_bytes']:,} bytes "
                f"(+{s['hfc_overhead_bytes']:,} header/palette/table)",
            ]
            if verified is True:
                lines.append("Decode check: lossless ✓")
            elif verified is False:
                lines.append("Decode check: MISMATCH")
            else:
                lines.append("Decode check: skipped (large image)")
            if saved_path:
                lines.append(f"Saved: {os.path.basename(saved_path)}")
            stats_label.configure(text="\n".join(lines), fg=TEXT_PRIMARY)

        def run_compress():
            if state["busy"]:
                return
            state["busy"] = True

            def compute():
                result = huffman.compress(mode, width, height, pixels, palette)
                verified = None
                if len(pixels) <= VERIFY_LIMIT:
                    _m, _w, _h, decoded, _p = huffman.unpack_hfc(result["hfc_bytes"])
                    verified = list(decoded) == list(pixels)
                return result, verified

            def done(payload):
                state["busy"] = False
                result, verified = payload
                state["result"] = result
                state["verified"] = verified
                show_stats(result, verified)
                fill_table(result)
                save_btn.configure(fg=ACCENT_BLUE)

            def failed():
                state["busy"] = False

            self._run_filter_async(content, compute, done, loading_text="Huffman coding",
                                   error_title="Compression Failed", on_error=failed)

        def save():
            result = state["result"]
            if result is None:
                messagebox.showinfo("Nothing to Save", "Press Compress first.")
                return
            base = getattr(self, "_image_path", None)
            initial = os.path.splitext(os.path.basename(base))[0] + ".hfc" if base else "image.hfc"
            path = filedialog.asksaveasfilename(
                title="Save Huffman-compressed image",
                defaultextension=".hfc",
                initialfile=initial,
                filetypes=[("Huffman compressed image", "*.hfc"), ("All files", "*.*")],
            )
            if not path:
                return
            try:
                huffman.save_hfc(path, result)
            except OSError as exc:
                messagebox.showerror("Save Failed", str(exc))
                return
            show_stats(result, state.get("verified"), saved_path=path)
