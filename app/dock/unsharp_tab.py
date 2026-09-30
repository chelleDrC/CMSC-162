"""
Unsharp Masking dock tab (Guide 4, item d).

Same interaction pattern as the smoothing tabs (averaging_tab.py): pick a
kernel size for the internal blur step, click Apply to run the filter (on
a background thread -- see dock/loading.py), and see the result on the
canvas and its histogram here.
"""

import tkinter as tk
from PIL import Image

from tools.point_processing.channels import to_array
from tools.point_processing.histogram import compute_histogram, bucketize
from tools.point_processing.transforms import grayscale_transform
from tools.spatial_domain.sharpening import unsharp_mask
from ..theme import BG_APP, BG_PANEL_ROW, BORDER, TEXT_PRIMARY, TEXT_DISABLED, FONT_LABEL, ACCENT_BLUE


class UnsharpTabMixin:
    def _build_unsharp_tab(self, parent):
        gray = grayscale_transform(to_array(self.image))
        state = {"kernel_size": 3, "applied": None}

        content = tk.Frame(parent, bg=BG_APP)
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(content, text="Unsharp masking -- blurs the image, subtracts that "
                 "blur from the original to isolate edge/detail information, then "
                 "adds it back to sharpen.",
                 bg=BG_APP, fg=TEXT_DISABLED, font=FONT_LABEL, wraplength=420,
                 justify=tk.LEFT).pack(fill=tk.X, anchor="w")

        size_row = tk.Frame(content, bg=BG_APP)
        size_row.pack(fill=tk.X, pady=(10, 0))
        tk.Label(size_row, text="Blur Kernel Size", bg=BG_APP, fg=TEXT_DISABLED,
                 font=FONT_LABEL).pack(side=tk.LEFT)
        size_value_label = tk.Label(size_row, text="3 x 3", bg=BG_APP,
                                     fg=TEXT_DISABLED, font=FONT_LABEL)
        size_value_label.pack(side=tk.RIGHT)
        self._build_slider(content, 3, 9, state["kernel_size"], lambda v: on_kernel_change(v))

        buttons_row = tk.Frame(content, bg=BG_APP)
        buttons_row.pack(fill=tk.X, pady=(4, 0))
        apply_btn = tk.Label(buttons_row, text="Apply", bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                              font=FONT_LABEL, cursor="hand2", padx=10, pady=4)
        apply_btn.pack(side=tk.LEFT, padx=(0, 4))
        apply_btn.bind("<Button-1>", lambda _e: apply_filter())

        undo_btn = tk.Label(buttons_row, text="\u21b6 Undo", bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                             font=FONT_LABEL, cursor="hand2", padx=10, pady=4)
        undo_btn.pack(side=tk.LEFT)
        undo_btn.bind("<Button-1>", lambda _e: undo())

        hist_canvas = tk.Canvas(content, bg=BG_PANEL_ROW, highlightbackground=BORDER,
                                 highlightthickness=1)
        hist_canvas.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        def on_kernel_change(value):
            size = int(round(value))
            if size % 2 == 0:
                size += 1
            size = max(3, min(9, size))
            state["kernel_size"] = size
            size_value_label.configure(text=f"{size} x {size}")

        def redraw_hist():
            hist_canvas.delete("hist")
            hw = hist_canvas.winfo_width()
            hh = hist_canvas.winfo_height()
            if hw <= 1 or hh <= 1:
                return
            source = state["applied"] if state["applied"] is not None else gray
            buckets = bucketize(compute_histogram(source), hw - 2)
            max_count = max(buckets) or 1
            for x, count in enumerate(buckets):
                bar_h = (count / max_count) * (hh - 4)
                if bar_h <= 0:
                    continue
                hist_canvas.create_line(x + 1, hh - 2, x + 1, hh - 2 - bar_h,
                                         fill=ACCENT_BLUE, tags="hist")

        def apply_filter():
            if state.get("busy"):
                return
            state["busy"] = True
            kernel_size = state["kernel_size"]

            def compute():
                return unsharp_mask(gray, kernel_size=kernel_size)

            def done(arr):
                state["busy"] = False
                state["applied"] = arr
                self._canvas_display = Image.fromarray(arr, mode="L")
                self._redraw_canvas_content()
                redraw_hist()

            self._run_filter_async(content, compute, done)

        def undo():
            if state.get("busy"):
                return
            state["applied"] = None
            self._on_undo_transform()
            redraw_hist()

        hist_canvas.bind("<Configure>", lambda _e: redraw_hist())
        redraw_hist()
