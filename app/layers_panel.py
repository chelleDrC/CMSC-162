"""Left LAYERS panel (placeholder rows, disabled)."""

import tkinter as tk

from .theme import (
    BG_PANEL, BG_PANEL_ROW_ACTIVE, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED, FONT_LABEL, FONT_LABEL_HEADER,
)


class LayersPanelMixin:
    def _build_layers_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_PANEL, width=self._sc(150),
                          highlightbackground=BORDER, highlightthickness=1)
        panel.pack(side=tk.LEFT, fill=tk.Y)
        panel.pack_propagate(False)

        header = tk.Frame(panel, bg=BG_PANEL)
        header.pack(fill=tk.X, padx=10, pady=(10, 6))
        tk.Label(header, text="⚙ LAYERS", bg=BG_PANEL, fg=TEXT_SECONDARY,
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
