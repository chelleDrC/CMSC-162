"""Shared low-level widget helpers: DPI scaling and the custom slider."""

import tkinter as tk

from .theme import BG_APP, BG_PANEL_ROW, ACCENT_BLUE


class WidgetsMixin:
    def _sc(self, px):
        return round(px * self._ui_scale)

    def _build_slider(self, parent, from_, to_, value, command, height=20, pady=(0, 8)):
        """
        Canvas-based horizontal slider with a round handle -- tk.Scale's
        stock rectangular bar doesn't fit the flat dark theme.
        """
        canvas = tk.Canvas(parent, height=self._sc(height), bg=BG_APP, highlightthickness=0)
        canvas.pack(fill=tk.X, pady=pady)

        state = {"value": value}
        handle_r = self._sc(7)
        track_h = self._sc(4)

        def value_to_x(v, w):
            pad = handle_r + 2
            span = to_ - from_
            frac = 0 if span == 0 else (v - from_) / span
            return pad + frac * (w - 2 * pad)

        def x_to_value(x, w):
            pad = handle_r + 2
            w_eff = max(1, w - 2 * pad)
            frac = min(1, max(0, (x - pad) / w_eff))
            return from_ + frac * (to_ - from_)

        def redraw():
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w <= 1:
                return
            mid_y = h / 2
            hx = value_to_x(state["value"], w)
            # Full track, then the filled portion up to the handle
            canvas.create_line(handle_r + 2, mid_y, w - handle_r - 2, mid_y,
                                fill=BG_PANEL_ROW, width=track_h, capstyle=tk.ROUND)
            canvas.create_line(handle_r + 2, mid_y, hx, mid_y,
                                fill=ACCENT_BLUE, width=track_h, capstyle=tk.ROUND)
            canvas.create_oval(hx - handle_r, mid_y - handle_r, hx + handle_r, mid_y + handle_r,
                                fill=ACCENT_BLUE, outline=BG_APP, width=2)

        def set_from_event(x):
            state["value"] = x_to_value(x, canvas.winfo_width())
            redraw()
            command(state["value"])

        canvas.bind("<Configure>", lambda _e: redraw())
        canvas.bind("<ButtonPress-1>", lambda e: set_from_event(e.x))
        canvas.bind("<B1-Motion>", lambda e: set_from_event(e.x))
        redraw()
