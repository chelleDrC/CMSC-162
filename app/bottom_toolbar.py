"""Bottom toolbar: tool icons (disabled placeholders) and zoom readout."""

import tkinter as tk

from .theme import BG_MENUBAR, BORDER, ACCENT_BLUE, TEXT_DISABLED, FONT_UI, FONT_LABEL


class BottomToolbarMixin:
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
        tk.Label(select_box, text="⤴", bg=ACCENT_BLUE, fg="white",
                 font=FONT_UI).pack(expand=True)

        icons = ["\U0001F50D", "↻", "✂", "\U0001F58A", "\U0001F489"]
        for icon in icons:
            box = tk.Frame(center, bg=BG_MENUBAR, width=28, height=28)
            box.pack(side=tk.LEFT, padx=4)
            box.pack_propagate(False)
            tk.Label(box, text=icon, bg=BG_MENUBAR, fg=TEXT_DISABLED,
                     font=FONT_UI).pack(expand=True)

        tk.Label(center, text="−", bg=BG_MENUBAR, fg=TEXT_DISABLED,
                 font=FONT_UI).pack(side=tk.LEFT, padx=10)
        self.zoom_pct_label = tk.Label(center, text="100%", bg=BG_MENUBAR,
                                        fg=TEXT_DISABLED, font=FONT_LABEL)
        self.zoom_pct_label.pack(side=tk.LEFT, padx=4)
        tk.Label(center, text="+", bg=BG_MENUBAR, fg=TEXT_DISABLED,
                 font=FONT_UI).pack(side=tk.LEFT, padx=10)
        tk.Label(center, text="⛶", bg=BG_MENUBAR, fg=TEXT_DISABLED,
                 font=FONT_UI).pack(side=tk.LEFT, padx=10)
