"""Right INFO panel: cursor position, pixel color, image properties, zoom."""

import tkinter as tk

from .theme import (
    BG_PANEL, BG_PANEL_ROW, BORDER, TEXT_SECONDARY, TEXT_DISABLED,
    FONT_LABEL, FONT_LABEL_HEADER,
)


class InfoPanelMixin:
    def _build_info_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_PANEL, width=self._sc(170),
                          highlightbackground=BORDER, highlightthickness=1)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)

        tk.Label(panel, text="ℹ INFO", bg=BG_PANEL, fg=TEXT_SECONDARY,
                 font=FONT_LABEL_HEADER).pack(anchor="w", padx=12, pady=(10, 8))

        def section(title):
            tk.Label(panel, text=title, bg=BG_PANEL, fg=TEXT_SECONDARY,
                     font=FONT_LABEL_HEADER).pack(anchor="w", padx=12, pady=(6, 4))

        def kv_row(label, value="—"):
            row = tk.Frame(panel, bg=BG_PANEL)
            row.pack(fill=tk.X, padx=12, pady=1)
            tk.Label(row, text=label, bg=BG_PANEL, fg=TEXT_DISABLED,
                     font=FONT_LABEL).pack(side=tk.LEFT)
            value_label = tk.Label(row, text=value, bg=BG_PANEL, fg=TEXT_DISABLED,
                     font=FONT_LABEL)
            value_label.pack(side=tk.RIGHT)
            return value_label

        section("▾ CURSOR POSITION")
        self.cursor_x_value = kv_row("X")
        self.cursor_y_value = kv_row("Y")

        section("▾ PIXEL COLOR")
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
            box_label = tk.Label(box, text="—", bg=BG_PANEL_ROW, fg=TEXT_DISABLED,
                     font=FONT_LABEL)
            box_label.pack(expand=True)
            self.rgb_value_labels.append(box_label)

            tk.Label(col, text=ch, bg=BG_PANEL, fg=channel_colors[ch],
                     font=FONT_LABEL).pack(pady=(1, 0))

        section("▾ IMAGE PROPERTIES")
        self.dimensions_value = kv_row("Dimensions")
        self.resolution_value = kv_row("Resolution")
        self.color_mode_value = kv_row("Color Mode")
        self.file_type_value = kv_row("File Type")
        self.file_size_value = kv_row("File Size")

        section("▾ ZOOM")
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

    def _update_pixel_info(self, x, y, rgb):
        # Cursor position
        self.cursor_x_value.configure(text=str(x) if x is not None else "—")
        self.cursor_y_value.configure(text=str(y) if y is not None else "—")

        if rgb is None:
            # Cursor left the image / canvas: reset to placeholder dashes
            self.pixel_swatch.itemconfig(self._swatch_rect, fill=BG_PANEL_ROW)
            for box_label in self.rgb_value_labels:
                box_label.configure(text="—")
            return

        # Update the swatch color and the R/G/B value boxes
        r, g, b = rgb
        self.pixel_swatch.itemconfig(
            self._swatch_rect, fill=f"#{r:02x}{g:02x}{b:02x}"
        )
        for box_label, value in zip(self.rgb_value_labels, (r, g, b)):
            box_label.configure(text=str(value))
