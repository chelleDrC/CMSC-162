"""Center canvas: image display, pan/zoom, and hover pixel readout."""

import tkinter as tk
from PIL import ImageTk

from tools.set_up.image import canvas_to_image_coords, get_pixel_rgb
from .theme import BG_CANVAS_AREA


class CanvasViewMixin:
    def _build_canvas_area(self, parent):
        wrap = tk.Frame(parent, bg=BG_CANVAS_AREA)
        wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(wrap, bg=BG_CANVAS_AREA, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", self._redraw_canvas_content)

        # Pan: hold Space, then click + drag
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Zoom: mouse wheel (Windows/Mac use <MouseWheel>, Linux uses Button-4/5)
        self.canvas.bind("<MouseWheel>", self._on_canvas_zoom)
        self.canvas.bind("<Button-4>", self._on_canvas_zoom_linux)
        self.canvas.bind("<Button-5>", self._on_canvas_zoom_linux)

        # Hover: show pixel RGB under the cursor
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Leave>", self._on_canvas_leave)

    def _redraw_canvas_content(self, event=None):
        self.canvas.delete("placeholder")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        cx = w / 2 + self._offset_x
        cy = h / 2 + self._offset_y
        pw = self._img_w * self._zoom
        ph = self._img_h * self._zoom
        x0, y0 = cx - pw / 2, cy - ph / 2

        display_img = self._canvas_display if self._canvas_display is not None else self.image
        if display_img is not None:
            # Real image: resize to current zoom and blit onto the canvas
            disp_w, disp_h = max(1, round(pw)), max(1, round(ph))
            resized = display_img.resize((disp_w, disp_h))
            self._tk_image = ImageTk.PhotoImage(resized)
            self.canvas.create_image(
                x0, y0, image=self._tk_image, anchor="nw", tags="placeholder"
            )
        else:
            self.canvas.create_rectangle(
                x0, y0, x0 + pw, y0 + ph,
                fill="#ffffff", outline="", tags="placeholder"
            )

    # -- Pan (Space + drag) -------------------------------------------
    def _on_space_down(self, event=None):
        self._space_down = True
        if not self._panning:
            self.canvas.configure(cursor="fleur")

    def _on_space_up(self, event=None):
        self._space_down = False
        if not self._panning:
            self.canvas.configure(cursor="")

    def _on_canvas_press(self, event):
        if not self._space_down:
            return
        self._panning = True
        self._pan_start = (event.x, event.y)
        self._pan_start_offset = (self._offset_x, self._offset_y)
        self.canvas.configure(cursor="fleur")

    def _on_canvas_drag(self, event):
        if not self._panning:
            return
        dx = event.x - self._pan_start[0]
        dy = event.y - self._pan_start[1]
        self._offset_x = self._pan_start_offset[0] + dx
        self._offset_y = self._pan_start_offset[1] + dy
        self._redraw_canvas_content()

    def _on_canvas_release(self, event=None):
        if not self._panning:
            return
        self._panning = False
        self.canvas.configure(cursor="fleur" if self._space_down else "")

    # -- Zoom (mouse wheel, centered on cursor) ------------------------
    def _on_canvas_zoom(self, event):
        factor = 1.1 if event.delta > 0 else (1 / 1.1)
        self._zoom_at(event.x, event.y, factor)

    def _on_canvas_zoom_linux(self, event):
        factor = 1.1 if event.num == 4 else (1 / 1.1)
        self._zoom_at(event.x, event.y, factor)

    def _zoom_at(self, mx, my, factor):
        new_zoom = max(0.2, min(5.0, self._zoom * factor))
        if new_zoom == self._zoom:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx, cy = w / 2, h / 2
        rel_x = mx - cx - self._offset_x
        rel_y = my - cy - self._offset_y
        ratio = new_zoom / self._zoom
        self._offset_x = mx - cx - rel_x * ratio
        self._offset_y = my - cy - rel_y * ratio
        self._zoom = new_zoom
        self._redraw_canvas_content()
        self._update_zoom_display()

    def _update_zoom_display(self):
        pct_text = f"{round(self._zoom * 100)}%"
        if hasattr(self, "zoom_pct_label"):
            self.zoom_pct_label.configure(text=pct_text)
        if hasattr(self, "zoom_level_value"):
            self.zoom_level_value.configure(text=pct_text)
        if hasattr(self, "zoom_scale_value"):
            self.zoom_scale_value.configure(text=f"{self._zoom:.2f}x")

    # -- Hover pixel readout --
    def _on_canvas_motion(self, event):
        # Read from whatever's actually on screen (a Transforms preview,
        # if one is active) rather than always the original image.
        display_img = self._canvas_display if self._canvas_display is not None else self.image
        if display_img is None:
            self._update_pixel_info(None, None, None)
            return

        # Convert the mouse position to an image pixel and look up its RGB
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        x, y = canvas_to_image_coords(
            event.x, event.y, w, h,
            self._img_w, self._img_h,
            self._zoom, self._offset_x, self._offset_y,
        )
        rgb = get_pixel_rgb(display_img, x, y)
        if rgb is None:
            self._update_pixel_info(None, None, None)
        else:
            if isinstance(rgb, int):
                # Grayscale ("L" mode) preview: one intensity value, not
                # a 3-tuple -- show it as an equal R/G/B reading.
                rgb = (rgb, rgb, rgb)
            self._update_pixel_info(x, y, rgb)

    def _on_canvas_leave(self, event=None):
        self._update_pixel_info(None, None, None)
