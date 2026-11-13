"""Title bar, menu bar, File/View/Filter/Compress dropdown menus, and Import Image."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from tools.set_up.image import (
    open_image_dialog,
    load_image,
    peek_image_mode,
    get_image_metadata,
    _format_file_size,
)
from tools.compression import pcx as pcx_codec
from tools.compression import huffman
from .theme import (
    BG_TITLEBAR, BG_MENUBAR, BG_DROPDOWN, BG_PANEL_ROW_ACTIVE, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED, ACCENT_BLUE,
    FONT_TITLE, FONT_UI, FONT_UI_BOLD, FONT_LABEL,
)


class MenuBarMixin:
    # ------------------------------------------------------------------
    # Top title strip: "PixelView UI Design"
    # ------------------------------------------------------------------
    def _build_title_bar(self):
        bar = tk.Frame(self.root, bg=BG_TITLEBAR, height=34)
        bar.pack(fill=tk.X, side=tk.TOP)
        tk.Label(
            bar, text="PixelView UI Design", bg=BG_TITLEBAR,
            fg=TEXT_SECONDARY, font=FONT_TITLE, anchor="w"
        ).pack(side=tk.LEFT, padx=16, pady=8)

    # ------------------------------------------------------------------
    # Menu bar: logo + PixelView + File/Edit/View/Help + status text
    # ------------------------------------------------------------------
    def _build_menu_bar(self):
        bar = tk.Frame(self.root, bg=BG_MENUBAR, height=36,
                        highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill=tk.X, side=tk.TOP)

        left = tk.Frame(bar, bg=BG_MENUBAR)
        left.pack(side=tk.LEFT, padx=10, pady=6)

        logo = tk.Canvas(left, width=16, height=16, bg=BG_MENUBAR,
                          highlightthickness=0)
        logo.create_oval(1, 1, 15, 15, fill=ACCENT_BLUE, outline="")
        logo.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(left, text="PixelView", bg=BG_MENUBAR, fg=TEXT_PRIMARY,
                 font=FONT_UI_BOLD).pack(side=tk.LEFT, padx=(0, 18))

        # File - functional menu (opens dropdown)
        self.file_label = tk.Label(
            left, text="File", bg=BG_MENUBAR, fg=TEXT_PRIMARY,
            font=FONT_UI, cursor="hand2"
        )
        self.file_label.pack(side=tk.LEFT, padx=10)
        self.file_label.bind("<Button-1>", lambda _e: self._toggle_dropdown(self._open_file_menu))

        # Edit - disabled placeholder
        tk.Label(left, text="Edit", bg=BG_MENUBAR, fg=TEXT_DISABLED,
                 font=FONT_UI).pack(side=tk.LEFT, padx=10)

        # View - functional menu (opens dropdown): Channels / Histogram / Transforms
        self.view_label = tk.Label(
            left, text="View", bg=BG_MENUBAR, fg=TEXT_PRIMARY,
            font=FONT_UI, cursor="hand2"
        )
        self.view_label.pack(side=tk.LEFT, padx=10)
        self.view_label.bind("<Button-1>", lambda _e: self._toggle_dropdown(self._open_view_menu))

        # Filter - functional menu (opens dropdown): spatial-domain filters (Guide 4)
        self.filter_label = tk.Label(
            left, text="Filter", bg=BG_MENUBAR, fg=TEXT_PRIMARY,
            font=FONT_UI, cursor="hand2"
        )
        self.filter_label.pack(side=tk.LEFT, padx=10)
        self.filter_label.bind("<Button-1>", lambda _e: self._toggle_dropdown(self._open_filter_menu))

        # Compress - functional menu (opens dropdown): PCX / Huffman (Project 2 Guide 1)
        self.compress_label = tk.Label(
            left, text="Compress", bg=BG_MENUBAR, fg=TEXT_PRIMARY,
            font=FONT_UI, cursor="hand2"
        )
        self.compress_label.pack(side=tk.LEFT, padx=10)
        self.compress_label.bind("<Button-1>", lambda _e: self._toggle_dropdown(self._open_compress_menu))

        # Help - disabled placeholder
        tk.Label(left, text="Help", bg=BG_MENUBAR, fg=TEXT_DISABLED,
                 font=FONT_UI).pack(side=tk.LEFT, padx=10)

        right = tk.Frame(bar, bg=BG_MENUBAR)
        right.pack(side=tk.RIGHT, padx=14, pady=6)
        tk.Label(right, text="Edge: unselected", bg=BG_MENUBAR,
                 fg=TEXT_DISABLED, font=FONT_LABEL).pack(side=tk.RIGHT)

    def _toggle_dropdown(self, open_fn):
        if self._dropdown is not None:
            self._close_dropdown()
            return
        open_fn()

    def _open_dropdown(self, anchor, entries, width=180, height=200):
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height()

        dd = tk.Toplevel(self.root)
        dd.overrideredirect(True)
        dd.configure(bg=BG_DROPDOWN, highlightbackground=BORDER,
                     highlightthickness=1)
        dd.geometry(f"{self._sc(width)}x{self._sc(height)}+{x}+{y}")
        self._dropdown = dd

        def item(text, shortcut="", enabled_look=True, arrow=False, command=None):
            row = tk.Frame(dd, bg=BG_DROPDOWN)
            row.pack(fill=tk.X, padx=1, pady=1)
            fg = TEXT_PRIMARY if enabled_look else TEXT_DISABLED
            lbl = tk.Label(row, text=text, bg=BG_DROPDOWN, fg=fg,
                            font=FONT_UI, anchor="w")
            lbl.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
            if shortcut:
                tk.Label(row, text=shortcut, bg=BG_DROPDOWN, fg=TEXT_DISABLED,
                          font=FONT_LABEL).pack(side=tk.RIGHT, padx=10)
            if arrow:
                tk.Label(row, text="›", bg=BG_DROPDOWN, fg=TEXT_DISABLED,
                          font=FONT_UI).pack(side=tk.RIGHT, padx=10)

            def on_enter(_e, r=row):
                r.configure(bg=BG_PANEL_ROW_ACTIVE)
                for c in r.winfo_children():
                    c.configure(bg=BG_PANEL_ROW_ACTIVE)

            def on_leave(_e, r=row):
                r.configure(bg=BG_DROPDOWN)
                for c in r.winfo_children():
                    c.configure(bg=BG_DROPDOWN)

            def on_click(_e):
                self._close_dropdown()
                if command is not None:
                    command()

            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)
            row.bind("<Button-1>", on_click)
            lbl.bind("<Button-1>", on_click)
            return row

        def separator():
            sep = tk.Frame(dd, bg=BORDER, height=1)
            sep.pack(fill=tk.X, padx=6, pady=4)

        for entry in entries:
            if entry is None:
                separator()
            else:
                item(**entry)

    def _open_file_menu(self):
        has_manipulation = self._canvas_display is not None
        self._open_dropdown(self.file_label, [
            dict(text="Import Image", shortcut="Ctrl+I", enabled_look=True,
                 command=self._on_import_image),
            dict(text="Open Recent", shortcut="", enabled_look=True, arrow=True),
            None,
            dict(text="Undo", shortcut="Ctrl+Z", enabled_look=has_manipulation,
                 command=self._on_undo_transform),
            None,
            dict(text="Save", shortcut="Ctrl+S", enabled_look=False),
            dict(text="Save As", shortcut="", enabled_look=False),
            dict(text="Export", shortcut="Ctrl+E", enabled_look=False),
            None,
            dict(text="Close", shortcut="", enabled_look=self.image is not None,
                 command=self._on_close_image),
        ], width=180, height=220)

    def _open_view_menu(self):
        self._open_dropdown(self.view_label, [
            dict(text="Channels", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Channels", self._build_channels_tab)),
            dict(text="Histogram", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Histogram", self._build_histogram_tab)),
            dict(text="Transforms", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Transforms", self._build_transforms_tab)),
        ], width=170, height=115)

    def _open_filter_menu(self):
        self._open_dropdown(self.filter_label, [
            dict(text="Averaging Filter", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Averaging", self._build_averaging_tab)),
            dict(text="Median Filter", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Median", self._build_median_tab)),
            dict(text="Highpass (Laplacian)", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Highpass", self._build_highpass_tab)),
            None,
            dict(text="Unsharp Masking", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Unsharp", self._build_unsharp_tab)),
            dict(text="Highboost Filter", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Highboost", self._build_highboost_tab)),
            dict(text="Gradient (Sobel)", shortcut="", enabled_look=True,
                 command=lambda: self._open_dock_tab("Gradient", self._build_gradient_tab)),
        ], width=200, height=230)

    def _open_compress_menu(self):
        self._open_dropdown(self.compress_label, [
            dict(text="PCX Header & Palette", shortcut="",
                 enabled_look=self._pcx is not None, command=self._open_pcx_tab),
            dict(text="Huffman Coding", shortcut="", enabled_look=self.image is not None,
                 command=lambda: self._open_dock_tab("Huffman", self._build_huffman_tab)),
            None,
            dict(text="Open .hfc File\u2026", shortcut="", enabled_look=True,
                 command=self._on_open_hfc),
        ], width=200, height=112)

    def _open_pcx_tab(self):
        if self._pcx is None:
            messagebox.showinfo("No PCX File",
                                "Open a .pcx file first (File \u203a Import Image).")
            return
        self._open_dock_tab("PCX Info", self._build_pcx_tab)

    def _close_dropdown(self):
        if self._dropdown is not None:
            self._dropdown.destroy()
            self._dropdown = None

    def _on_import_image(self):
        path = open_image_dialog()
        if not path:
            return  # user cancelled

        if pcx_codec.is_pcx_path(path):
            self._import_pcx(path)
            return

        # Load and validate the image
        img = load_image(path)
        if img is None:
            messagebox.showerror(
                "Import Failed",
                f"Couldn't open image:\n{path}"
            )
            return

        self._show_loaded_image(img, path)

        # Push file metadata into the Image Properties panel
        metadata = get_image_metadata(path, img, original_mode=peek_image_mode(path))
        self._show_metadata(metadata)

    def _show_loaded_image(self, img, path, pcx=None, compress_source=None):
        """Make img the current image and reset everything tied to the previous one."""
        # Compression tabs describe a specific file -- drop them for a new one.
        for name in ("PCX Info", "Huffman"):
            if name in self._dock_tabs:
                self._close_dock_tab(name)

        self.image = img
        self._image_path = path
        self._pcx = pcx
        self._compress_source = compress_source
        self._canvas_display = None  # drop any transform preview from the previous image
        self._img_w, self._img_h = img.size
        self._zoom = 1.0
        self._offset_x, self._offset_y = 0.0, 0.0
        self._redraw_canvas_content()
        self._update_zoom_display()

    def _show_metadata(self, metadata):
        self.dimensions_value.configure(text=metadata["dimensions"])
        self.resolution_value.configure(text=metadata["resolution"])
        self.color_mode_value.configure(text=metadata["color_mode"])
        self.file_type_value.configure(text=metadata["file_type"])
        self.file_size_value.configure(text=metadata["file_size"])

    # ------------------------------------------------------------------
    # PCX (Project 2 Guide 1, items a-c): open via the manual RLE decoder
    # ------------------------------------------------------------------
    def _import_pcx(self, path):
        def done(pcx):
            if pcx["mode"] == "P":
                kind = f"{pcx['palette_size']}-color indexed (palette indices)"
            else:
                kind = "24-bit RGB (R, G, B bytes)"
            source = {
                "mode": pcx["mode"], "width": pcx["width"], "height": pcx["height"],
                "pixels": pcx["pixels"], "palette": pcx["palette"],
                "label": f"RLE-reconstructed PCX, {pcx['width']} x {pcx['height']} px, {kind}",
            }
            self._show_loaded_image(pcx["image"], path, pcx=pcx, compress_source=source)

            header = pcx["header"]
            if pcx["mode"] == "RGB":
                color_mode = "RGB (24-bit)"
            elif pcx["palette_size"] == 256:
                color_mode = "P (8-bit)"
            else:
                color_mode = f"P ({pcx['palette_size']}-color)"
            self._show_metadata({
                "dimensions": f"{pcx['width']} x {pcx['height']} px",
                "resolution": f"{header['hdpi']} x {header['vdpi']} DPI",
                "color_mode": color_mode,
                "file_type": "PCX",
                "file_size": _format_file_size(pcx["file_size"]),
            })
            self._open_dock_tab("PCX Info", self._build_pcx_tab)

        self._run_filter_async(self.canvas.master, lambda: pcx_codec.read_pcx(path), done,
                               loading_text="Decoding PCX (run-length)",
                               error_title="Couldn't open PCX file")

    # ------------------------------------------------------------------
    # .hfc (Project 2 Guide 1, item d): decode a saved Huffman file back
    # ------------------------------------------------------------------
    def _on_open_hfc(self):
        path = filedialog.askopenfilename(
            title="Open Huffman-compressed image",
            filetypes=[("Huffman compressed image", "*.hfc"), ("All files", "*.*")],
        )
        if not path:
            return

        def compute():
            mode, width, height, pixels, palette = huffman.load_hfc(path)
            img = pcx_codec.build_image(mode, width, height, pixels, palette)
            return mode, width, height, pixels, palette, img

        def done(payload):
            mode, width, height, pixels, palette, img = payload
            kind = "indexed (palette indices)" if mode == "P" else "RGB (R, G, B bytes)"
            source = {
                "mode": mode, "width": width, "height": height,
                "pixels": pixels, "palette": palette,
                "label": f"Decoded .hfc, {width} x {height} px, {kind}",
            }
            self._show_loaded_image(img, path, compress_source=source)
            self._show_metadata({
                "dimensions": f"{width} x {height} px",
                "resolution": "\u2014",
                "color_mode": "P (8-bit)" if mode == "P" else "RGB (24-bit)",
                "file_type": "HFC",
                "file_size": _format_file_size(os.path.getsize(path)),
            })

        self._run_filter_async(self.canvas.master, compute, done,
                               loading_text="Decoding Huffman file",
                               error_title="Couldn't open .hfc file")

    # ------------------------------------------------------------------
    # File > Close
    # ------------------------------------------------------------------
    def _on_close_image(self):
        if self.image is None:
            return
        for name in list(self._dock_order):
            self._close_dock_tab(name)
        self.image = None
        self._image_path = None
        self._pcx = None
        self._compress_source = None
        self._canvas_display = None
        self._tk_image = None
        self._img_w, self._img_h = 300, 168
        self._zoom = 1.0
        self._offset_x, self._offset_y = 0.0, 0.0
        self._redraw_canvas_content()
        self._update_zoom_display()
        for label in (self.dimensions_value, self.resolution_value, self.color_mode_value,
                      self.file_type_value, self.file_size_value):
            label.configure(text="\u2014")

    def _maybe_close_dropdown(self, event):
        # Close if the click landed outside the File/View label / dropdown
        if self._dropdown is None:
            return
        widget = event.widget
        if widget in (self.file_label, self.view_label, self.filter_label, self.compress_label):
            return  # handled by the toggle binding
        try:
            if str(widget).startswith(str(self._dropdown)):
                return
        except Exception:
            pass
        self._close_dropdown()
