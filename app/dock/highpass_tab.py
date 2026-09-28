"""
Highpass (Laplacian) dock tab (Guide 4, item c).

Unlike the smoothing filters, there's no size slider here -- the Laplacian
kernel is fixed at 3x3. Instead the user picks between the two standard
kernel variants (4-neighbor / 8-neighbor); the chosen matrix is shown on
screen since the guide asks to "show kernel used".
"""

import tkinter as tk
from PIL import Image

from tools.point_processing.channels import to_array
from tools.point_processing.histogram import compute_histogram, bucketize
from tools.point_processing.transforms import grayscale_transform
from tools.spatial_domain.sharpening import (
    laplacian_highpass, LAPLACIAN_KERNEL_4, LAPLACIAN_KERNEL_8,
)
from ..theme import (
    BG_APP, BG_PANEL_ROW, BG_PANEL_ROW_ACTIVE, BORDER, TEXT_PRIMARY, TEXT_DISABLED,
    FONT_LABEL, ACCENT_BLUE,
)


def _kernel_text(kernel):
    rows = [" ".join(f"{int(v):>2}" for v in row) for row in kernel]
    return "\n".join(rows)


class HighpassTabMixin:
    def _build_highpass_tab(self, parent):
        gray = grayscale_transform(to_array(self.image))
        state = {"variant": "4", "applied": None}

        content = tk.Frame(parent, bg=BG_APP)
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(content, text="Highpass filtering with the Laplacian operator -- "
                 "highlights edges/fine detail by reacting to sudden changes "
                 "in intensity.",
                 bg=BG_APP, fg=TEXT_DISABLED, font=FONT_LABEL, wraplength=420,
                 justify=tk.LEFT).pack(fill=tk.X, anchor="w")

        buttons_row = tk.Frame(content, bg=BG_APP)
        buttons_row.pack(fill=tk.X, pady=(10, 0))
        variant_buttons = {}
        for label, key in (("4-Neighbor", "4"), ("8-Neighbor", "8")):
            btn = tk.Label(buttons_row, text=label, bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                            font=FONT_LABEL, cursor="hand2", padx=8, pady=4)
            btn.pack(side=tk.LEFT, padx=(0, 4))
            btn.bind("<Button-1>", lambda _e, k=key: set_variant(k))
            variant_buttons[key] = btn

        apply_btn = tk.Label(buttons_row, text="Apply", bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                              font=FONT_LABEL, cursor="hand2", padx=10, pady=4)
        apply_btn.pack(side=tk.LEFT, padx=(12, 4))
        apply_btn.bind("<Button-1>", lambda _e: apply_filter())

        undo_btn = tk.Label(buttons_row, text="↶ Undo", bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                             font=FONT_LABEL, cursor="hand2", padx=10, pady=4)
        undo_btn.pack(side=tk.LEFT)
        undo_btn.bind("<Button-1>", lambda _e: undo())

        kernel_label = tk.Label(content, text="", bg=BG_APP, fg=TEXT_DISABLED,
                                 font=("Consolas", 9), justify=tk.LEFT)
        kernel_label.pack(fill=tk.X, anchor="w", pady=(8, 0))

        hist_canvas = tk.Canvas(content, bg=BG_PANEL_ROW, highlightbackground=BORDER,
                                 highlightthickness=1)
        hist_canvas.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        def set_variant(key):
            state["variant"] = key
            for k, btn in variant_buttons.items():
                btn.configure(bg=BG_PANEL_ROW_ACTIVE if k == key else BG_PANEL_ROW)
            kernel = LAPLACIAN_KERNEL_4 if key == "4" else LAPLACIAN_KERNEL_8
            kernel_label.configure(text="Kernel used:\n" + _kernel_text(kernel))

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
            variant = state["variant"]

            def compute():
                return laplacian_highpass(gray, kernel_variant=variant)

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

        set_variant("4")
        hist_canvas.bind("<Configure>", lambda _e: redraw_hist())
        redraw_hist()
