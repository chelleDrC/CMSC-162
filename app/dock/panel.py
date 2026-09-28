"""
Bottom dock panel mechanics: tabbed Channels/Histogram/Transforms views,
pinned above the toolbar. Each tab has its own close (x) button; the dock
hides itself once no tabs remain. The tab *content* builders themselves
live in channels_tab.py / histogram_tab.py / transforms_tab.py.
"""

import tkinter as tk
from tkinter import messagebox

from ..theme import BG_APP, BG_MENUBAR, BG_PANEL_ROW, BG_PANEL_ROW_ACTIVE, BORDER, TEXT_PRIMARY, TEXT_DISABLED, FONT_LABEL


class DockPanelMixin:
    def _build_dock_panel(self):
        self._dock_frame = tk.Frame(self.root, bg=BG_MENUBAR,
                                     highlightbackground=BORDER, highlightthickness=1)
        # Not packed yet -- shown once the first tab opens (see _show_dock).

        self._dock_tabs_bar = tk.Frame(self._dock_frame, bg=BG_MENUBAR)
        self._dock_tabs_bar.pack(fill=tk.X, side=tk.TOP)

        content_wrapper = tk.Frame(self._dock_frame, bg=BG_APP, height=self._sc(260))
        content_wrapper.pack(fill=tk.X, side=tk.TOP)
        content_wrapper.pack_propagate(False)

        self._dock_content = tk.Frame(content_wrapper, bg=BG_APP)
        self._dock_content.pack(fill=tk.BOTH, expand=True)
        self._dock_content.grid_rowconfigure(0, weight=1)
        self._dock_content.grid_columnconfigure(0, weight=1)

    def _show_dock(self):
        if not self._dock_frame.winfo_ismapped():
            self._dock_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def _hide_dock(self):
        self._dock_frame.pack_forget()

    def _open_dock_tab(self, name, build_fn):
        """
        Open (or refresh, if already open) a dock tab. build_fn(parent)
        populates the tab's content frame -- called fresh each time, so
        the tab always reflects the currently loaded image.
        """
        if self.image is None:
            messagebox.showinfo("No Image", "Import an image first.")
            return

        existing = self._dock_tabs.get(name)
        if existing is not None:
            existing["content"].destroy()
        else:
            self._add_dock_tab_button(name)

        content = tk.Frame(self._dock_content, bg=BG_APP)
        content.grid(row=0, column=0, sticky="nsew")
        build_fn(content)
        self._dock_tabs[name]["content"] = content

        self._show_dock()
        self._activate_dock_tab(name)

    def _add_dock_tab_button(self, name):
        tab = tk.Frame(self._dock_tabs_bar, bg=BG_PANEL_ROW)
        tab.pack(side=tk.LEFT, padx=(6, 2), pady=4)

        label = tk.Label(tab, text=name, bg=BG_PANEL_ROW, fg=TEXT_PRIMARY,
                          font=FONT_LABEL, padx=8, pady=3, cursor="hand2")
        label.pack(side=tk.LEFT)
        label.bind("<Button-1>", lambda _e, n=name: self._activate_dock_tab(n))

        close_btn = tk.Label(tab, text="✕", bg=BG_PANEL_ROW, fg=TEXT_DISABLED,
                              font=FONT_LABEL, padx=6, cursor="hand2")
        close_btn.pack(side=tk.LEFT)
        close_btn.bind("<Button-1>", lambda _e, n=name: self._close_dock_tab(n))

        self._dock_tabs[name] = {"tab": tab, "label": label, "close": close_btn, "content": None}
        self._dock_order.append(name)

    def _activate_dock_tab(self, name):
        info = self._dock_tabs.get(name)
        if info is None:
            return
        self._dock_active_tab = name
        info["content"].tkraise()
        for n, tab_info in self._dock_tabs.items():
            bg = BG_PANEL_ROW_ACTIVE if n == name else BG_PANEL_ROW
            tab_info["tab"].configure(bg=bg)
            tab_info["label"].configure(bg=bg)
            tab_info["close"].configure(bg=bg)

    def _close_dock_tab(self, name):
        info = self._dock_tabs.pop(name, None)
        if info is None:
            return
        info["tab"].destroy()
        info["content"].destroy()
        self._dock_order.remove(name)

        if self._dock_active_tab == name:
            self._dock_active_tab = None
            if self._dock_order:
                self._activate_dock_tab(self._dock_order[-1])
            else:
                self._hide_dock()
