"""
PixelView - UI module
CMSC 162 - Project 1

Defines the PixelViewApp class: all widget construction, layout, and UI-level
interaction (dropdown menus, pan/zoom, redraw, and the View/Filter menus'
Channels/Histogram/Transforms/Averaging/Median/Highpass panels, docked at
the bottom of the window like an editor's integrated terminal). Each concern
lives in its own mixin module (menu bar, canvas, panels, dock tabs); this
file just wires them together.
"""

import tkinter as tk

from .theme import BG_APP
from .widgets import WidgetsMixin
from .menu_bar import MenuBarMixin
from .layers_panel import LayersPanelMixin
from .canvas_view import CanvasViewMixin
from .info_panel import InfoPanelMixin
from .bottom_toolbar import BottomToolbarMixin
from .dock.panel import DockPanelMixin
from .dock.channels_tab import ChannelsTabMixin
from .dock.histogram_tab import HistogramTabMixin
from .dock.transforms_tab import TransformsTabMixin
from .dock.loading import BackgroundFilterMixin
from .dock.averaging_tab import AveragingTabMixin
from .dock.median_tab import MedianTabMixin
from .dock.highpass_tab import HighpassTabMixin
from .dock.unsharp_tab import UnsharpTabMixin
from .dock.highboost_tab import HighboostTabMixin
from .dock.gradient_tab import GradientTabMixin

# Improve rendering sharpness
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


class PixelViewApp(
    WidgetsMixin,
    MenuBarMixin,
    LayersPanelMixin,
    CanvasViewMixin,
    InfoPanelMixin,
    BottomToolbarMixin,
    DockPanelMixin,
    ChannelsTabMixin,
    HistogramTabMixin,
    TransformsTabMixin,
    BackgroundFilterMixin,
    AveragingTabMixin,
    MedianTabMixin,
    HighpassTabMixin,
    UnsharpTabMixin,
    HighboostTabMixin,
    GradientTabMixin,
):
    def __init__(self, root):
        self.root = root
        try:
            self.root.update_idletasks()
            self._ui_scale = self.root.winfo_fpixels('1i') / 96.0
        except Exception:
            self._ui_scale = 1.0
        self.root.title("PixelView")
        self.root.geometry(f"{self._sc(1000)}x{self._sc(620)}")
        self.root.configure(bg=BG_APP)
        self.root.minsize(self._sc(860), self._sc(540))

        self._dropdown = None  # currently open File/View dropdown, if any

        # Loaded image state
        self.image = None
        self._tk_image = None
        self._canvas_display = None  # non-None while a Transforms preview overrides self.image

        # Bottom dock panel state (Channels/Histogram/Transforms tabs)
        self._dock_tabs = {}     # name -> {"tab", "label", "close", "content"}
        self._dock_order = []    # tab names, in the order they were opened
        self._dock_active_tab = None

        # Canvas view state (pan/zoom)
        self._img_w, self._img_h = 300, 168
        self._zoom = 1.0
        self._offset_x, self._offset_y = 0.0, 0.0
        self._space_down = False
        self._panning = False
        self._pan_start = (0, 0)
        self._pan_start_offset = (0.0, 0.0)

        self._build_title_bar()
        self._build_menu_bar()

        body = tk.Frame(root, bg=BG_APP)
        body.pack(fill=tk.BOTH, expand=True)

        self._build_layers_panel(body)
        self._build_canvas_area(body)
        self._build_info_panel(body)

        self._build_bottom_toolbar()
        self._build_dock_panel()

        # Close any open dropdown when clicking elsewhere in the app
        root.bind("<Button-1>", self._maybe_close_dropdown, add="+")

        # Hold Space to pan the canvas (app-wide so focus doesn't matter)
        root.bind_all("<KeyPress-space>", self._on_space_down)
        root.bind_all("<KeyRelease-space>", self._on_space_up)
