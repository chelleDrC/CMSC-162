"""
Transforms dock tab: Gray/Negative/B-W/Gamma buttons + Undo, driving the
main canvas preview, plus the histogram of whatever's currently shown.
"""

import tkinter as tk
from PIL import Image

from tools.point_processing.channels import split_channels, to_array
from tools.point_processing.histogram import compute_histogram, bucketize
from tools.point_processing.transforms import (
    grayscale_transform,
    negative_transform,
    threshold_transform,
    gamma_transform,
)
from ..theme import (
    BG_APP, BG_PANEL_ROW, BG_PANEL_ROW_ACTIVE, BORDER, TEXT_PRIMARY, TEXT_DISABLED,
    FONT_LABEL, ACCENT_BLUE,
)


class TransformsTabMixin:
    def _build_transforms_tab(self, parent):
        state = {"mode": "Original", "threshold": 128, "gamma": 1.0}
        gray = grayscale_transform(to_array(self.image))
        channels = split_channels(self.image)  # for the true R/G/B histogram on Original

        def get_array():
            mode = state["mode"]
            if mode == "Gray":
                return gray
            if mode == "Negative":
                return negative_transform(gray)
            if mode == "B/W":
                return threshold_transform(gray, state["threshold"])
            if mode == "Gamma":
                return gamma_transform(gray, state["gamma"])
            return None  # Original

        content = tk.Frame(parent, bg=BG_APP)
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        buttons_row = tk.Frame(content, bg=BG_APP)
        buttons_row.pack(fill=tk.X)
        buttons = {}
        for name in ("Original", "Gray", "Negative", "B/W", "Gamma"):
            btn = tk.Label(buttons_row, text=name, bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                            font=FONT_LABEL, cursor="hand2", padx=6, pady=4)
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Button-1>", lambda _e, m=name: set_mode(m))
            buttons[name] = btn

        undo_btn = tk.Label(buttons_row, text="↶ Undo", bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                             font=FONT_LABEL, cursor="hand2", padx=6, pady=4)
        undo_btn.pack(side=tk.RIGHT, padx=2)
        undo_btn.bind("<Button-1>", lambda _e: set_mode("Original"))

        # Threshold and Gamma each live in their own frame so only the
        # slider relevant to the active mode is shown -- B/W ignores
        # Gamma and vice versa, so showing both is misleading.
        threshold_frame = tk.Frame(content, bg=BG_APP)
        threshold_row = tk.Frame(threshold_frame, bg=BG_APP)
        threshold_row.pack(fill=tk.X)
        tk.Label(threshold_row, text="Threshold", bg=BG_APP, fg=TEXT_DISABLED,
                 font=FONT_LABEL).pack(side=tk.LEFT)
        threshold_value_label = tk.Label(threshold_row, text=str(state["threshold"]),
                                          bg=BG_APP, fg=TEXT_DISABLED, font=FONT_LABEL)
        threshold_value_label.pack(side=tk.RIGHT)
        self._build_slider(threshold_frame, 0, 255, state["threshold"], lambda v: on_threshold(v))

        gamma_frame = tk.Frame(content, bg=BG_APP)
        gamma_row = tk.Frame(gamma_frame, bg=BG_APP)
        gamma_row.pack(fill=tk.X)
        tk.Label(gamma_row, text="Gamma", bg=BG_APP, fg=TEXT_DISABLED,
                 font=FONT_LABEL).pack(side=tk.LEFT)
        gamma_value_label = tk.Label(gamma_row, text=f"{state['gamma']:.2f}",
                                      bg=BG_APP, fg=TEXT_DISABLED, font=FONT_LABEL)
        gamma_value_label.pack(side=tk.RIGHT)
        self._build_slider(gamma_frame, 0.1, 3.0, state["gamma"], lambda v: on_gamma(v))

        hist_canvas = tk.Canvas(content, bg=BG_PANEL_ROW, highlightbackground=BORDER,
                                 highlightthickness=1)
        hist_canvas.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        def update_slider_visibility():
            mode = state["mode"]
            if mode == "B/W":
                gamma_frame.pack_forget()
                threshold_frame.pack(fill=tk.X, before=hist_canvas, pady=(8, 0))
            elif mode == "Gamma":
                threshold_frame.pack_forget()
                gamma_frame.pack(fill=tk.X, before=hist_canvas, pady=(8, 0))
            else:
                # Original/Gray/Negative are fixed formulas -- neither
                # slider changes their output, so show neither.
                threshold_frame.pack_forget()
                gamma_frame.pack_forget()

        def redraw():
            arr = get_array()

            # Drive the main canvas with the same result shown here.
            self._canvas_display = None if arr is None else Image.fromarray(arr, mode="L")
            self._redraw_canvas_content()

            hist_canvas.delete("hist")
            hw = hist_canvas.winfo_width()
            hh = hist_canvas.winfo_height()
            if hw > 1 and hh > 1:
                if state["mode"] == "Original":
                    # No single grayscale array represents a color image --
                    # show the real overlaid R/G/B histogram instead.
                    series = [(channels["R"], "#ef4444"),
                              (channels["G"], "#22c55e"),
                              (channels["B"], "#3b82f6")]
                    bucketed = [(bucketize(compute_histogram(c), hw - 2), color) for c, color in series]
                    max_count = max((max(b) for b, _ in bucketed if b), default=1) or 1
                    for buckets, color in bucketed:
                        for x, count in enumerate(buckets):
                            bar_h = (count / max_count) * (hh - 4)
                            if bar_h <= 0:
                                continue
                            hist_canvas.create_line(x + 1, hh - 2, x + 1, hh - 2 - bar_h,
                                                     fill=color, stipple="gray50", tags="hist")
                else:
                    buckets = bucketize(compute_histogram(arr), hw - 2)
                    max_count = max(buckets) or 1
                    for x, count in enumerate(buckets):
                        bar_h = (count / max_count) * (hh - 4)
                        if bar_h <= 0:
                            continue
                        hist_canvas.create_line(x + 1, hh - 2, x + 1, hh - 2 - bar_h,
                                                 fill=ACCENT_BLUE, tags="hist")

            for name, btn in buttons.items():
                btn.configure(bg=BG_PANEL_ROW_ACTIVE if name == state["mode"] else BG_PANEL_ROW)
            update_slider_visibility()

        def set_mode(mode):
            state["mode"] = mode
            redraw()

        def on_threshold(value):
            state["threshold"] = int(float(value))
            threshold_value_label.configure(text=str(state["threshold"]))
            if state["mode"] == "B/W":
                redraw()

        def on_gamma(value):
            state["gamma"] = float(value)
            gamma_value_label.configure(text=f"{state['gamma']:.2f}")
            if state["mode"] == "Gamma":
                redraw()

        # File > Undo (menu_bar.py) reaches into whichever transform is
        # currently selected via this hook, so both undo entry points
        # (this tab's button and the File menu) share one code path.
        self._transforms_set_mode = set_mode

        hist_canvas.bind("<Configure>", lambda _e: redraw())
        redraw()

    def _on_undo_transform(self):
        """Revert the canvas to the original image (File > Undo)."""
        if self._canvas_display is None:
            return
        if "Transforms" in self._dock_tabs:
            self._transforms_set_mode("Original")
        else:
            self._canvas_display = None
            self._redraw_canvas_content()
