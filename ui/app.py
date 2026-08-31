"""
PixelView - UI module
CMSC 162 - Project 1

This module defines the PixelViewApp class: all widget construction, layout,
and UI-level interaction (dropdown menu, pan/zoom, redraw). Only the File
menu is interactive so far; everything else is a disabled placeholder that
will be wired up in later project phases.
"""

import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk
from backend.image import (
    open_image_dialog,
    load_image,
    peek_image_mode,
    get_image_metadata,
    canvas_to_image_coords,
    get_pixel_rgb,
)

# Improve rendering sharpness 
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ---------------------------------------------------------------------------
# Color palette (dark theme, matched to the design mock)
# ---------------------------------------------------------------------------
BG_APP = "#131313"
BG_TITLEBAR = "#131313"
BG_MENUBAR = "#1a1a1a"
BG_PANEL = "#161616"
BG_PANEL_ROW = "#1d1d1d"
BG_PANEL_ROW_ACTIVE = "#232323"
BG_CANVAS_AREA = "#0e0e0e"
BG_DROPDOWN = "#212121"
BORDER = "#2a2a2a"
TEXT_PRIMARY = "#e6e6e6"
TEXT_SECONDARY = "#9a9a9a"
TEXT_DISABLED = "#5a5a5a"
ACCENT_BLUE = "#3b82f6"

FONT_TITLE = ("Segoe UI", 10)
FONT_UI = ("Segoe UI", 9)
FONT_UI_BOLD = ("Segoe UI", 9, "bold")
FONT_LABEL = ("Segoe UI", 8)
FONT_LABEL_HEADER = ("Segoe UI", 8, "bold")


class PixelViewApp:
    def __init__(self, root):
        self.root = root
        try:
            self.root.update_idletasks()
            self._ui_scale = self.root.winfo_fpixels('1i') / 96.0
        except Exception:
            self._ui_scale = 1.0
        self.root.title("PixelView")
        self.root.geometry(f"{self._sc(1000)}x{self._sc(620)}")
        self.root.configure(bg=BG_APP)
        self.root.minsize(self._sc(860), self._sc(540))

        self._dropdown = None  # currently open File dropdown, if any

        # Loaded image state
        self.image = None      
        self._tk_image = None  

        # Canvas view state (pan/zoom)
        self._img_w, self._img_h = 300, 168
        self._zoom = 1.0
        self._offset_x, self._offset_y = 0.0, 0.0
        self._space_down = False
        self._panning = False
        self._pan_start = (0, 0)
        self._pan_start_offset = (0.0, 0.0)

        self._build_title_bar()
        self._build_menu_bar()

        body = tk.Frame(root, bg=BG_APP)
        body.pack(fill=tk.BOTH, expand=True)

        self._build_layers_panel(body)
        self._build_canvas_area(body)
        self._build_info_panel(body)

        self._build_bottom_toolbar()

        # Close any open dropdown when clicking elsewhere in the app
        root.bind("<Button-1>", self._maybe_close_dropdown, add="+")

        # Hold Space to pan the canvas (app-wide so focus doesn't matter)
        root.bind_all("<KeyPress-space>", self._on_space_down)
        root.bind_all("<KeyRelease-space>", self._on_space_up)


    def _sc(self, px):
        return round(px * self._ui_scale)

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

        # File - the ONLY functional menu (opens dropdown)
        self.file_label = tk.Label(
            left, text="File", bg=BG_MENUBAR, fg=TEXT_PRIMARY,
            font=FONT_UI, cursor="hand2"
        )
        self.file_label.pack(side=tk.LEFT, padx=10)
        self.file_label.bind("<Button-1>", self._toggle_file_menu)

        # Edit / View / Help - disabled placeholders
        for name in ("Edit", "View", "Help"):
            tk.Label(
                left, text=name, bg=BG_MENUBAR, fg=TEXT_DISABLED,
                font=FONT_UI
            ).pack(side=tk.LEFT, padx=10)

        right = tk.Frame(bar, bg=BG_MENUBAR)
        right.pack(side=tk.RIGHT, padx=14, pady=6)
        tk.Label(right, text="Edge: unselected", bg=BG_MENUBAR,
                 fg=TEXT_DISABLED, font=FONT_LABEL).pack(side=tk.RIGHT)

    def _toggle_file_menu(self, event=None):
        if self._dropdown is not None:
            self._close_dropdown()
            return
        self._open_file_menu()

    def _open_file_menu(self):
        x = self.file_label.winfo_rootx()
        y = self.file_label.winfo_rooty() + self.file_label.winfo_height()

        dd = tk.Toplevel(self.root)
        dd.overrideredirect(True)
        dd.configure(bg=BG_DROPDOWN, highlightbackground=BORDER,
                     highlightthickness=1)
        dd.geometry(f"{self._sc(180)}x{self._sc(200)}+{x}+{y}")
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
                tk.Label(row, text="\u203a", bg=BG_DROPDOWN, fg=TEXT_DISABLED,
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

        item("Import Image", "Ctrl+I", enabled_look=True,
             command=self._on_import_image)
        item("Open Recent", "", enabled_look=True, arrow=True)
        separator()
        item("Save", "Ctrl+S", enabled_look=False)
        item("Save As", "", enabled_look=False)
        item("Export", "Ctrl+E", enabled_look=False)
        separator()
        item("Close", "", enabled_look=True)

    def _close_dropdown(self):
        if self._dropdown is not None:
            self._dropdown.destroy()
            self._dropdown = None

    def _on_import_image(self):
        path = open_image_dialog()
        if not path:
            return

        # Load and validate the image
        img = load_image(path)
        if img is None:
            messagebox.showerror(
                "Import Failed",
                f"Couldn't open image:\n{path}"
            )
            return

        # Reset view state for the newly loaded image
        self.image = img
        self._img_w, self._img_h = img.size
        self._zoom = 1.0
        self._offset_x, self._offset_y = 0.0, 0.0
        self._redraw_canvas_content()
        self._update_zoom_display()

        # Push file metadata into the Image Properties panel
        metadata = get_image_metadata(path, img, original_mode=peek_image_mode(path))
        self.dimensions_value.configure(text=metadata["dimensions"])
        self.resolution_value.configure(text=metadata["resolution"])
        self.color_mode_value.configure(text=metadata["color_mode"])
        self.file_type_value.configure(text=metadata["file_type"])
        self.file_size_value.configure(text=metadata["file_size"])

    def _maybe_close_dropdown(self, event):
        # Close if the click landed outside the File label / dropdown
        if self._dropdown is None:
            return
        widget = event.widget
        if widget is self.file_label:
            return  # handled by the toggle binding
        try:
            if str(widget).startswith(str(self._dropdown)):
                return
        except Exception:
            pass
        self._close_dropdown()

    # ------------------------------------------------------------------
    # Left panel: LAYERS (placeholder rows, disabled)
    # ------------------------------------------------------------------
    def _build_layers_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_PANEL, width=self._sc(150),
                          highlightbackground=BORDER, highlightthickness=1)
        panel.pack(side=tk.LEFT, fill=tk.Y)
        panel.pack_propagate(False)

        header = tk.Frame(panel, bg=BG_PANEL)
        header.pack(fill=tk.X, padx=10, pady=(10, 6))
        tk.Label(header, text="\u2699 LAYERS", bg=BG_PANEL, fg=TEXT_SECONDARY,
                 font=FONT_LABEL_HEADER).pack(side=tk.LEFT)

        layers = [
            ("Layer 1", "#5b8def", False, True),
        ]

        list_frame = tk.Frame(panel, bg=BG_PANEL)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6)

        for name, color, locked, selected in layers:
            row_bg = BG_PANEL_ROW_ACTIVE if selected else BG_PANEL
            row = tk.Frame(list_frame, bg=row_bg)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text="\U0001F441", bg=row_bg, fg=TEXT_DISABLED,
                     font=FONT_LABEL).pack(side=tk.LEFT, padx=(4, 4))

            thumb = tk.Canvas(row, width=18, height=18, bg=row_bg,
                               highlightthickness=0)
            thumb.create_rectangle(1, 1, 17, 17, fill=color, outline="")
            thumb.pack(side=tk.LEFT, padx=2)

            tk.Label(row, text=name, bg=row_bg,
                     fg=TEXT_PRIMARY if selected else TEXT_SECONDARY,
                     font=FONT_LABEL, anchor="w").pack(
                side=tk.LEFT, padx=4, fill=tk.X, expand=True)

            if locked:
                tk.Label(row, text="\U0001F512", bg=row_bg, fg=TEXT_DISABLED,
                         font=FONT_LABEL).pack(side=tk.RIGHT, padx=4)

        # Add Layer - disabled placeholder button
        add_btn = tk.Label(
            panel, text="+  Add Layer", bg=BG_PANEL, fg=TEXT_DISABLED,
            font=FONT_LABEL, pady=8
        )
        add_btn.pack(fill=tk.X, side=tk.BOTTOM, padx=6, pady=8)

    # ------------------------------------------------------------------
    # Center: canvas area with placeholder white image
    # ------------------------------------------------------------------
    def _build_canvas_area(self, parent):
        wrap = tk.Frame(parent, bg=BG_CANVAS_AREA)
        wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(wrap, bg=BG_CANVAS_AREA, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", self._redraw_canvas_content)

        # Pan: hold Space, then click + drag
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Zoom: mouse wheel (Windows/Mac use <MouseWheel>, Linux uses Button-4/5)
        self.canvas.bind("<MouseWheel>", self._on_canvas_zoom)
        self.canvas.bind("<Button-4>", self._on_canvas_zoom_linux)
        self.canvas.bind("<Button-5>", self._on_canvas_zoom_linux)

        # Hover: show pixel RGB under the cursor
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Leave>", self._on_canvas_leave)

    def _redraw_canvas_content(self, event=None):
        self.canvas.delete("placeholder")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        cx = w / 2 + self._offset_x
        cy = h / 2 + self._offset_y
        pw = self._img_w * self._zoom
        ph = self._img_h * self._zoom
        x0, y0 = cx - pw / 2, cy - ph / 2

        if self.image is not None:
            # Real image: resize to current zoom and blit onto the canvas
            disp_w, disp_h = max(1, round(pw)), max(1, round(ph))
            resized = self.image.resize((disp_w, disp_h))
            self._tk_image = ImageTk.PhotoImage(resized)
            self.canvas.create_image(
                x0, y0, image=self._tk_image, anchor="nw", tags="placeholder"
            )
        else:
            self.canvas.create_rectangle(
                x0, y0, x0 + pw, y0 + ph,
                fill="#ffffff", outline="", tags="placeholder"
            )

    # -- Pan (Space + drag) -------------------------------------------
    def _on_space_down(self, event=None):
        self._space_down = True
        if not self._panning:
            self.canvas.configure(cursor="fleur")

    def _on_space_up(self, event=None):
        self._space_down = False
        if not self._panning:
            self.canvas.configure(cursor="")

    def _on_canvas_press(self, event):
        if not self._space_down:
            return
        self._panning = True
        self._pan_start = (event.x, event.y)
        self._pan_start_offset = (self._offset_x, self._offset_y)
        self.canvas.configure(cursor="fleur")

    def _on_canvas_drag(self, event):
        if not self._panning:
            return
        dx = event.x - self._pan_start[0]
        dy = event.y - self._pan_start[1]
        self._offset_x = self._pan_start_offset[0] + dx
        self._offset_y = self._pan_start_offset[1] + dy
        self._redraw_canvas_content()

    def _on_canvas_release(self, event=None):
        if not self._panning:
            return
        self._panning = False
        self.canvas.configure(cursor="fleur" if self._space_down else "")

    # -- Zoom (mouse wheel, centered on cursor) ------------------------
    def _on_canvas_zoom(self, event):
        factor = 1.1 if event.delta > 0 else (1 / 1.1)
        self._zoom_at(event.x, event.y, factor)

    def _on_canvas_zoom_linux(self, event):
        factor = 1.1 if event.num == 4 else (1 / 1.1)
        self._zoom_at(event.x, event.y, factor)

    def _zoom_at(self, mx, my, factor):
        new_zoom = max(0.2, min(5.0, self._zoom * factor))
        if new_zoom == self._zoom:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx, cy = w / 2, h / 2
        rel_x = mx - cx - self._offset_x
        rel_y = my - cy - self._offset_y
        ratio = new_zoom / self._zoom
        self._offset_x = mx - cx - rel_x * ratio
        self._offset_y = my - cy - rel_y * ratio
        self._zoom = new_zoom
        self._redraw_canvas_content()
        self._update_zoom_display()

    def _update_zoom_display(self):
        pct_text = f"{round(self._zoom * 100)}%"
        if hasattr(self, "zoom_pct_label"):
            self.zoom_pct_label.configure(text=pct_text)
        if hasattr(self, "zoom_level_value"):
            self.zoom_level_value.configure(text=pct_text)
        if hasattr(self, "zoom_scale_value"):
            self.zoom_scale_value.configure(text=f"{self._zoom:.2f}x")

    # -- Hover pixel readout --
    def _on_canvas_motion(self, event):
        if self.image is None:
            self._update_pixel_info(None, None, None)
            return

        # Convert the mouse position to an image pixel and look up its RGB
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        x, y = canvas_to_image_coords(
            event.x, event.y, w, h,
            self._img_w, self._img_h,
            self._zoom, self._offset_x, self._offset_y,
        )
        rgb = get_pixel_rgb(self.image, x, y)
        if rgb is None:
            self._update_pixel_info(None, None, None)
        else:
            self._update_pixel_info(x, y, rgb)

    def _on_canvas_leave(self, event=None):
        self._update_pixel_info(None, None, None)

    def _update_pixel_info(self, x, y, rgb):
        # Cursor position
        self.cursor_x_value.configure(text=str(x) if x is not None else "\u2014")
        self.cursor_y_value.configure(text=str(y) if y is not None else "\u2014")

        if rgb is None:
            # Cursor left the image / canvas: reset to placeholder dashes
            self.pixel_swatch.itemconfig(self._swatch_rect, fill=BG_PANEL_ROW)
            for box_label in self.rgb_value_labels:
                box_label.configure(text="\u2014")
            return

        # Update the swatch color and the R/G/B value boxes
        r, g, b = rgb
        self.pixel_swatch.itemconfig(
            self._swatch_rect, fill=f"#{r:02x}{g:02x}{b:02x}"
        )
        for box_label, value in zip(self.rgb_value_labels, (r, g, b)):
            box_label.configure(text=str(value))

    # ------------------------------------------------------------------
    # Right panel: INFO (cursor pos / pixel color / image props / zoom)
    # ------------------------------------------------------------------
    def _build_info_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_PANEL, width=self._sc(170),
                          highlightbackground=BORDER, highlightthickness=1)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)

        tk.Label(panel, text="\u2139 INFO", bg=BG_PANEL, fg=TEXT_SECONDARY,
                 font=FONT_LABEL_HEADER).pack(anchor="w", padx=12, pady=(10, 8))

        def section(title):
            tk.Label(panel, text=title, bg=BG_PANEL, fg=TEXT_SECONDARY,
                     font=FONT_LABEL_HEADER).pack(anchor="w", padx=12, pady=(6, 4))

        def kv_row(label, value="\u2014"):
            row = tk.Frame(panel, bg=BG_PANEL)
            row.pack(fill=tk.X, padx=12, pady=1)
            tk.Label(row, text=label, bg=BG_PANEL, fg=TEXT_DISABLED,
                     font=FONT_LABEL).pack(side=tk.LEFT)
            value_label = tk.Label(row, text=value, bg=BG_PANEL, fg=TEXT_DISABLED,
                     font=FONT_LABEL)
            value_label.pack(side=tk.RIGHT)
            return value_label

        section("\u25be CURSOR POSITION")
        self.cursor_x_value = kv_row("X")
        self.cursor_y_value = kv_row("Y")

        section("\u25be PIXEL COLOR")
        swatch_row = tk.Frame(panel, bg=BG_PANEL)
        swatch_row.pack(fill=tk.X, padx=12, pady=(2, 2))
        sw = tk.Canvas(swatch_row, width=20, height=20, bg=BG_PANEL,
                        highlightbackground=BORDER, highlightthickness=1)
        self._swatch_rect = sw.create_rectangle(0, 0, 20, 20, fill=BG_PANEL_ROW, outline="")
        sw.pack(side=tk.LEFT)
        self.pixel_swatch = sw
        tk.Label(swatch_row, text="hover canvas", bg=BG_PANEL,
                 fg=TEXT_DISABLED, font=FONT_LABEL).pack(side=tk.LEFT, padx=8)

        rgb_row = tk.Frame(panel, bg=BG_PANEL)
        rgb_row.pack(fill=tk.X, padx=12, pady=(6, 2))
        self.rgb_value_labels = []
        channel_colors = {"R": "#ef4444", "G": "#22c55e", "B": "#3b82f6"}
        for ch in ("R", "G", "B"):
            col = tk.Frame(rgb_row, bg=BG_PANEL)
            col.pack(side=tk.LEFT, padx=3)

            box = tk.Frame(col, bg=BG_PANEL_ROW, width=self._sc(42), height=self._sc(28),
                            highlightbackground=BORDER, highlightthickness=1)
            box.pack()
            box.pack_propagate(False)
            box_label = tk.Label(box, text="\u2014", bg=BG_PANEL_ROW, fg=TEXT_DISABLED,
                     font=FONT_LABEL)
            box_label.pack(expand=True)
            self.rgb_value_labels.append(box_label)

            tk.Label(col, text=ch, bg=BG_PANEL, fg=channel_colors[ch],
                     font=FONT_LABEL).pack(pady=(1, 0))

        section("\u25be IMAGE PROPERTIES")
        self.dimensions_value = kv_row("Dimensions")
        self.resolution_value = kv_row("Resolution")
        self.color_mode_value = kv_row("Color Mode")
        self.file_type_value = kv_row("File Type")
        self.file_size_value = kv_row("File Size")

        section("\u25be ZOOM")
        level_row = tk.Frame(panel, bg=BG_PANEL)
        level_row.pack(fill=tk.X, padx=12, pady=1)
        tk.Label(level_row, text="Level", bg=BG_PANEL, fg=TEXT_DISABLED,
                 font=FONT_LABEL).pack(side=tk.LEFT)
        self.zoom_level_value = tk.Label(level_row, text="100%", bg=BG_PANEL,
                                          fg=TEXT_DISABLED, font=FONT_LABEL)
        self.zoom_level_value.pack(side=tk.RIGHT)

        scale_row = tk.Frame(panel, bg=BG_PANEL)
        scale_row.pack(fill=tk.X, padx=12, pady=1)
        tk.Label(scale_row, text="Scale", bg=BG_PANEL, fg=TEXT_DISABLED,
                 font=FONT_LABEL).pack(side=tk.LEFT)
        self.zoom_scale_value = tk.Label(scale_row, text="1.00x", bg=BG_PANEL,
                                          fg=TEXT_DISABLED, font=FONT_LABEL)
        self.zoom_scale_value.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Bottom toolbar: tool icons (disabled placeholders, select "active")
    # ------------------------------------------------------------------
    def _build_bottom_toolbar(self):
        bar = tk.Frame(self.root, bg=BG_MENUBAR, height=44,
                        highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill=tk.X, side=tk.BOTTOM)

        center = tk.Frame(bar, bg=BG_MENUBAR)
        center.pack(pady=6)

        # Selection tool - visually active (blue), still non-functional
        select_box = tk.Frame(center, bg=ACCENT_BLUE, width=28, height=28)
        select_box.pack(side=tk.LEFT, padx=4)
        select_box.pack_propagate(False)
        tk.Label(select_box, text="\u2934", bg=ACCENT_BLUE, fg="white",
                 font=FONT_UI).pack(expand=True)

        icons = ["\U0001F50D", "\u21bb", "\u2702", "\U0001F58A", "\U0001F489"]
        for icon in icons:
            box = tk.Frame(center, bg=BG_MENUBAR, width=28, height=28)
            box.pack(side=tk.LEFT, padx=4)
            box.pack_propagate(False)
            tk.Label(box, text=icon, bg=BG_MENUBAR, fg=TEXT_DISABLED,
                     font=FONT_UI).pack(expand=True)

        tk.Label(center, text="\u2212", bg=BG_MENUBAR, fg=TEXT_DISABLED,
                 font=FONT_UI).pack(side=tk.LEFT, padx=10)
        self.zoom_pct_label = tk.Label(center, text="100%", bg=BG_MENUBAR,
                                        fg=TEXT_DISABLED, font=FONT_LABEL)
        self.zoom_pct_label.pack(side=tk.LEFT, padx=4)
        tk.Label(center, text="+", bg=BG_MENUBAR, fg=TEXT_DISABLED,
                 font=FONT_UI).pack(side=tk.LEFT, padx=10)
        tk.Label(center, text="\u26f6", bg=BG_MENUBAR, fg=TEXT_DISABLED,
                 font=FONT_UI).pack(side=tk.LEFT, padx=10)
