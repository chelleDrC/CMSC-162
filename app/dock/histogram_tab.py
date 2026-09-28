"""Histogram dock tab: RGB/R/G/B buttons pick what the histogram shows."""

import tkinter as tk

from tools.point_processing.channels import split_channels
from tools.point_processing.histogram import compute_histogram, bucketize
from ..theme import BG_APP, BG_PANEL_ROW, BG_PANEL_ROW_ACTIVE, BORDER, TEXT_PRIMARY, FONT_LABEL


class HistogramTabMixin:
    def _build_histogram_tab(self, parent):
        channels = split_channels(self.image)
        channel_colors = {"R": "#ef4444", "G": "#22c55e", "B": "#3b82f6"}
        state = {"mode": "RGB"}  # "RGB" (overlaid) | "R" | "G" | "B"

        buttons_row = tk.Frame(parent, bg=BG_APP)
        buttons_row.pack(fill=tk.X, padx=12, pady=(12, 6))
        buttons = {}
        for name in ("RGB", "R", "G", "B"):
            color = TEXT_PRIMARY if name == "RGB" else channel_colors[name]
            btn = tk.Label(buttons_row, text=name, bg=BG_PANEL_ROW, fg=color,
                            font=FONT_LABEL, cursor="hand2", width=4, padx=4, pady=4)
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Button-1>", lambda _e, m=name: set_mode(m))
            buttons[name] = btn

        canvas = tk.Canvas(parent, bg=BG_PANEL_ROW, highlightbackground=BORDER,
                            highlightthickness=1)
        canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        def draw(_e=None):
            canvas.delete("hist")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w <= 1 or h <= 1:
                return

            mode = state["mode"]
            if mode == "RGB":
                series = [(channels["R"], "#ef4444"),
                          (channels["G"], "#22c55e"),
                          (channels["B"], "#3b82f6")]
            else:
                series = [(channels[mode], channel_colors[mode])]

            bucketed = [(bucketize(compute_histogram(arr), w), color) for arr, color in series]
            max_count = max((max(b) for b, _ in bucketed if b), default=1) or 1
            # Overlaying all three needs stippling so they don't fully hide
            # each other; a single channel is solid since there's nothing
            # to blend with.
            stipple = "gray50" if len(bucketed) > 1 else ""
            for buckets, color in bucketed:
                for x, count in enumerate(buckets):
                    bar_h = (count / max_count) * (h - 4)
                    if bar_h <= 0:
                        continue
                    canvas.create_line(x, h - 2, x, h - 2 - bar_h, fill=color,
                                        stipple=stipple, tags="hist")

            for name, btn in buttons.items():
                btn.configure(bg=BG_PANEL_ROW_ACTIVE if name == mode else BG_PANEL_ROW)

        def set_mode(mode):
            state["mode"] = mode
            draw()

        canvas.bind("<Configure>", draw)
