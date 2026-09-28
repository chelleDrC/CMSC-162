"""Channels dock tab: R/G/B tinted thumbnails side by side."""

import tkinter as tk
from PIL import ImageTk

from tools.point_processing.channels import split_channels, channel_as_color
from ..theme import BG_APP, TEXT_PRIMARY, FONT_UI


class ChannelsTabMixin:
    def _build_channels_tab(self, parent):
        channels = split_channels(self.image)
        thumb_w = self._sc(180)
        scale = thumb_w / self.image.width
        thumb_h = max(1, round(self.image.height * scale))

        row = tk.Frame(parent, bg=BG_APP)
        row.pack(padx=12, pady=12)

        parent._images = []  # keep PhotoImage references alive
        for label, key in (("Red", "R"), ("Green", "G"), ("Blue", "B")):
            col = tk.Frame(row, bg=BG_APP)
            col.pack(side=tk.LEFT, padx=8)

            tinted = channel_as_color(channels[key], key).resize((thumb_w, thumb_h))
            tk_img = ImageTk.PhotoImage(tinted)
            parent._images.append(tk_img)

            tk.Label(col, image=tk_img, bg=BG_APP).pack()
            tk.Label(col, text=label, bg=BG_APP, fg=TEXT_PRIMARY,
                     font=FONT_UI).pack(pady=(6, 0))
