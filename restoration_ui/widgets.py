import tkinter as tk
from PIL import Image, ImageTk
from .theme import (
    SURFACE, SURFACE_ALT, BORDER, TEXT, TEXT_MUTED, TEXT_FAINT,
    ACCENT, ACCENT_HOVER, ACCENT_SOFT, PATCH, HISTOGRAM,
    FONT, FONT_SMALL, FONT_BOLD, FONT_SECTION,
)


class Button(tk.Label):
    def __init__(self, parent, text, command, primary=False):
        if primary:
            self._colors = (ACCENT, ACCENT_HOVER, "#ffffff")
        else:
            self._colors = (ACCENT_SOFT, "#e0e7ff", ACCENT)
        normal, hover, fg = self._colors
        super().__init__(parent, text=text, bg=normal, fg=fg, font=FONT_BOLD,
                         padx=14, pady=7, cursor="hand2")
        self.bind("<Enter>", lambda _e: self.configure(bg=hover))
        self.bind("<Leave>", lambda _e: self.configure(bg=normal))
        self.bind("<Button-1>", lambda _e: command())


class SegmentedControl(tk.Frame):
    def __init__(self, parent, options, value, on_change=None, labels=None):
        super().__init__(parent, bg=BORDER, padx=1, pady=1)  # BORDER shows as a 1px outline
        self.value = value
        self._on_change = on_change
        self._labels = {}
        labels = labels or {}

        for column, option in enumerate(options):
            self.grid_columnconfigure(column, weight=1, uniform="segment")
            label = tk.Label(self, text=labels.get(option, option), font=FONT_SMALL,
                             pady=6, cursor="hand2")
            label.grid(row=0, column=column, sticky="nsew")
            label.bind("<Button-1>", lambda _e, o=option: self.select(o))
            self._labels[option] = label

        self._refresh()

    def select(self, option):
        self.value = option
        self._refresh()
        if self._on_change is not None:
            self._on_change(option)

    def _refresh(self):
        for option, label in self._labels.items():
            if option == self.value:
                label.configure(bg=ACCENT, fg="#ffffff")
            else:
                label.configure(bg=SURFACE, fg=TEXT_MUTED)


class LabeledSlider(tk.Frame):

    def __init__(self, parent, label, from_, to, resolution, value, fmt=str):
        super().__init__(parent, bg=SURFACE)
        self._fmt = fmt
        self._var = tk.DoubleVar(value=value)

        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill=tk.X)
        tk.Label(header, text=label, bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL).pack(side=tk.LEFT)
        self._value_label = tk.Label(header, text=fmt(value), bg=SURFACE, fg=TEXT, font=FONT_BOLD)
        self._value_label.pack(side=tk.RIGHT)

        tk.Scale(
            self, from_=from_, to=to, resolution=resolution, variable=self._var,
            orient=tk.HORIZONTAL, showvalue=False, command=self._on_move,
            bg=ACCENT, troughcolor=BORDER, activebackground=ACCENT_HOVER,  # bg = handle color
            highlightthickness=0, bd=0, sliderrelief=tk.FLAT, sliderlength=18, width=8,
        ).pack(fill=tk.X, pady=(2, 0))

    def get(self):
        return self._var.get()

    def _on_move(self, _value):
        self._value_label.configure(text=self._fmt(self.get()))


def _to_pil(gray):
    h, w = len(gray), len(gray[0])
    return Image.frombytes("L", (w, h), bytes([value for row in gray for value in row]))


class ImageCard(tk.Frame):
    def __init__(self, parent, title, show_histogram=False, selectable=False):
        super().__init__(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        self.image = None       # list of rows (gray[y][x], 0-255) currently shown
        self._pil = None        # the same image as a Pillow image, built once for drawing
        self.patch = None       # (x0, y0, x1, y1) in image pixels, or None
        self._photo = None      # keeps the Tk image alive
        self._scale = 1.0       # display pixels per image pixel
        self._origin = (0, 0)   # canvas position of the image's top-left corner
        self._drag_start = None

        # Title row
        tk.Label(self, text=title, bg=SURFACE, fg=TEXT, font=FONT_SECTION,
                 anchor="w").pack(fill=tk.X, padx=14, pady=(12, 0))
        self._subtitle = tk.Label(self, text="", bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL,
                                  anchor="w")
        self._subtitle.pack(fill=tk.X, padx=14, pady=(0, 8))

        # Picture
        self._canvas = tk.Canvas(self, bg=SURFACE_ALT, highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=14)
        self._canvas.bind("<Configure>", lambda _e: self._draw_image())

        # Histogram
        self._hist_canvas = None
        if show_histogram:
            self._hist_caption = tk.Label(self, text="Histogram", bg=SURFACE, fg=TEXT_MUTED,
                                          font=FONT_SMALL, anchor="w")
            self._hist_caption.pack(fill=tk.X, padx=14, pady=(10, 0))
            if selectable:
                tk.Label(self, text="Drag to pick a patch, click to reset.",
                         bg=SURFACE, fg=TEXT_FAINT, font=FONT_SMALL,
                         anchor="w").pack(fill=tk.X, padx=14, pady=(0, 4))
            self._hist_canvas = tk.Canvas(self, height=110, bg=SURFACE_ALT, highlightthickness=0)
            self._hist_canvas.pack(fill=tk.X, padx=14)
            self._hist_canvas.bind("<Configure>", lambda _e: self._draw_histogram())

        # Optional spot under the card for buttons (empty unless the caller adds some).
        self.footer = tk.Frame(self, bg=SURFACE)
        self.footer.pack(fill=tk.X, padx=14)

        tk.Frame(self, bg=SURFACE, height=14).pack(fill=tk.X)  # bottom padding

        if selectable:
            self._canvas.configure(cursor="crosshair")
            self._canvas.bind("<ButtonPress-1>", self._on_press)
            self._canvas.bind("<B1-Motion>", self._on_drag)
            self._canvas.bind("<ButtonRelease-1>", self._on_release)

    # ---------------------------------------------------------------- public
    def set_image(self, gray, subtitle=""):
        """Show a new list-of-rows image (or None to clear the card)."""
        self.image = gray
        self._pil = _to_pil(gray) if gray is not None else None
        self.patch = None
        self._subtitle.configure(text=subtitle)
        self._draw_image()
        self._draw_histogram()

    # ---------------------------------------------------------------- drawing
    def _draw_image(self):
        canvas = self._canvas
        canvas.delete("all")
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            return

        if self.image is None:
            canvas.create_text(cw / 2, ch / 2, text="No image yet", fill=TEXT_FAINT, font=FONT)
            return

        # Fit the image inside the canvas, keeping its aspect ratio.
        h, w = len(self.image), len(self.image[0])
        self._scale = min(cw / w, ch / h)
        dw, dh = max(1, int(w * self._scale)), max(1, int(h * self._scale))
        self._origin = ((cw - dw) // 2, (ch - dh) // 2)

        # NEAREST when enlarging keeps single noisy pixels crisp; BOX averages when shrinking.
        resample = Image.NEAREST if self._scale >= 1 else Image.BOX
        shown = self._pil.resize((dw, dh), resample)
        self._photo = ImageTk.PhotoImage(shown)
        canvas.create_image(*self._origin, image=self._photo, anchor="nw")

        if self.patch is not None:
            x0, y0, x1, y1 = self.patch
            canvas.create_rectangle(*self._to_canvas(x0, y0), *self._to_canvas(x1, y1),
                                    outline=PATCH, width=2)

    def _draw_histogram(self):
        canvas = self._hist_canvas
        if canvas is None:
            return
        canvas.delete("all")
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if self.image is None or cw <= 1:
            self._hist_caption.configure(text="Histogram")
            return

        x0, y0, x1, y1 = 0, 0, len(self.image[0]), len(self.image)  # whole image
        if self.patch is not None:
            x0, y0, x1, y1 = self.patch
            caption = f"Histogram — patch {x1 - x0} × {y1 - y0} px"
        else:
            caption = "Histogram — whole image"
        self._hist_caption.configure(text=caption)

        # Count the pixels at each value: counts[r] = number of pixels equal to r.
        counts = [0] * 256
        for row in self.image[y0:y1]:
            for value in row[x0:x1]:
                counts[value] += 1
        tallest = max(counts) or 1
        bar_width = cw / 256
        for value, count in enumerate(counts):
            if count == 0:
                continue
            x = value * bar_width
            top = ch - (count / tallest) * (ch - 6)
            canvas.create_rectangle(x, top, x + max(bar_width, 1), ch,
                                    fill=HISTOGRAM, outline="")

    # ---------------------------------------------------------- patch select
    def _to_canvas(self, x, y):
        """Image pixel -> canvas position."""
        return self._origin[0] + x * self._scale, self._origin[1] + y * self._scale

    def _to_image(self, cx, cy):
        """Canvas position -> image pixel, clamped to the image."""
        h, w = len(self.image), len(self.image[0])
        x = int((cx - self._origin[0]) / self._scale)
        y = int((cy - self._origin[1]) / self._scale)
        return min(max(x, 0), w), min(max(y, 0), h)

    def _on_press(self, event):
        if self.image is not None:
            self._drag_start = (event.x, event.y)

    def _on_drag(self, event):
        if self._drag_start is None:
            return
        self._canvas.delete("drag")
        self._canvas.create_rectangle(*self._drag_start, event.x, event.y,
                                      outline=PATCH, width=2, dash=(4, 2), tags="drag")

    def _on_release(self, event):
        if self._drag_start is None:
            return
        (ax, ay), (bx, by) = self._to_image(*self._drag_start), self._to_image(event.x, event.y)
        self._drag_start = None

        x0, x1 = sorted((ax, bx))
        y0, y1 = sorted((ay, by))
        if x1 - x0 >= 2 and y1 - y0 >= 2:
            self.patch = (x0, y0, x1, y1)
        else:
            self.patch = None  # a plain click goes back to the whole image
        self._draw_image()
        self._draw_histogram()
