"""
Gradient (Sobel magnitude) dock tab (Guide 4, item f).

Sobel was chosen over Prewitt -- see tools/spatial_domain/gradient.py for
the full justification. No kernel-size slider here: Sobel's Gx/Gy kernels
are fixed at 3x3, and both are shown on screen since the guide asks to
"show kernel used".
"""

import tkinter as tk
from PIL import Image

from tools.point_processing.channels import to_array
from tools.point_processing.histogram import compute_histogram, bucketize
from tools.point_processing.transforms import grayscale_transform
from tools.spatial_domain.gradient import sobel_magnitude, SOBEL_KX, SOBEL_KY
from ..theme import BG_APP, BG_PANEL_ROW, BORDER, TEXT_PRIMARY, TEXT_DISABLED, FONT_LABEL, ACCENT_BLUE


def _kernel_text(kernel):
    rows = [" ".join(f"{int(v):>2}" for v in row) for row in kernel]
    return "\n".join(rows)


class GradientTabMixin:
    def _build_gradient_tab(self, parent):
        gray = grayscale_transform(to_array(self.image))
        state = {"applied": None}

        content = tk.Frame(parent, bg=BG_APP)
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(content, text="Gradient magnitude (Sobel) -- combines horizontal (Gx) "
                 "and vertical (Gy) intensity-change kernels into a single edge-"
                 "strength value per pixel: sqrt(Gx^2 + Gy^2).",
                 bg=BG_APP, fg=TEXT_DISABLED, font=FONT_LABEL, wraplength=420,
                 justify=tk.LEFT).pack(fill=tk.X, anchor="w")

        # Fixed kernels -- shown explicitly per the guideline ("show
        # kernel used"), no slider since Sobel's kernels don't vary.
        kernel_row = tk.Frame(content, bg=BG_APP)
        kernel_row.pack(fill=tk.X, pady=(10, 0))

        gx_col = tk.Frame(kernel_row, bg=BG_APP)
        gx_col.pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(gx_col, text="Gx (horizontal):", bg=BG_APP, fg=TEXT_DISABLED,
                 font=FONT_LABEL).pack(anchor="w")
        tk.Label(gx_col, text=_kernel_text(SOBEL_KX), bg=BG_APP, fg=TEXT_DISABLED,
                 font=("Consolas", 9), justify=tk.LEFT).pack(anchor="w")

        gy_col = tk.Frame(kernel_row, bg=BG_APP)
        gy_col.pack(side=tk.LEFT)
        tk.Label(gy_col, text="Gy (vertical):", bg=BG_APP, fg=TEXT_DISABLED,
                 font=FONT_LABEL).pack(anchor="w")
        tk.Label(gy_col, text=_kernel_text(SOBEL_KY), bg=BG_APP, fg=TEXT_DISABLED,
                 font=("Consolas", 9), justify=tk.LEFT).pack(anchor="w")

        buttons_row = tk.Frame(content, bg=BG_APP)
        buttons_row.pack(fill=tk.X, pady=(10, 0))
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

            def compute():
                return sobel_magnitude(gray)

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
