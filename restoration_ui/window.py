"""
RestorationWindow -- the whole Project 2 Guide 2 UI.

    +----------------------------------------------------------------+
    |  Noise & Restoration                            [Open Image]   |
    +--------------+-------------------------------------------------+
    | 1  Degrade   |  Original   |   Degraded       |   Restored     |
    |   noise type |             |   + histogram    |                |
    |   parameters |             |   (drag = patch) |                |
    | 2  Restore   |             |                  |                |
    |   filter     |             |                  |                |
    |   kernel, Q  |             |                  |                |
    +--------------+-------------------------------------------------+
    |  status message                                                |
    +----------------------------------------------------------------+

Flow: Open Image -> Add Noise (item a) -> look at the histogram (item b.i)
-> Apply Filter / Apply Again (item b.ii).
"""

import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np
from PIL import Image

from tools.restoration.noise import (
    add_salt_and_pepper_noise, add_gaussian_noise, add_rayleigh_noise,
)
from tools.restoration.mean_filters import geometric_mean_filter, contraharmonic_mean_filter
from tools.restoration.order_statistics import median_filter
from .theme import BG, SURFACE, BORDER, TEXT, TEXT_MUTED, ACCENT, FONT_SMALL, FONT_SECTION, FONT_TITLE
from .widgets import Button, SegmentedControl, LabeledSlider, ImageCard

NOISE_TYPES = ("Salt & Pepper", "Gaussian", "Rayleigh")
FILTER_TYPES = ("Geometric", "Contraharmonic", "Median")

FILTER_HINTS = {
    "Geometric": "Geometric mean filter: each pixel becomes the geometric mean of its "
                 "neighborhood. Smooths Gaussian-type noise with less blurring.",
    "Contraharmonic": "Contraharmonic mean filter: Q > 0 removes pepper (black) noise, "
                      "Q < 0 removes salt (white) noise.",
    "Median": "Order-statistic filter: each pixel becomes the median of its neighborhood. "
              "Best for salt-and-pepper noise -- use Apply Again for more passes.",
}

IMAGE_TYPES = [("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.pcx"), ("All files", "*.*")]


class RestorationWindow:
    def __init__(self, root):
        self.root = root
        self.original = None   # clean grayscale image, (H, W) uint8
        self.noisy = None      # degraded image (item a)
        self.restored = None   # filtered image (item b.ii)
        self.passes = 0        # how many times the current filter has been applied

        root.title("Noise & Restoration — CMSC 162 Project 2 Guide 2")
        root.geometry("1360x820")
        root.minsize(1100, 680)
        root.configure(bg=BG)

        self._build_header()
        self._build_status_bar()

        body = tk.Frame(root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        self._build_sidebar(body)
        self._build_cards(body)

    # ================================================================ layout
    def _build_header(self):
        header = tk.Frame(self.root, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill=tk.X)

        titles = tk.Frame(header, bg=SURFACE)
        titles.pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(titles, text="Noise & Restoration", bg=SURFACE, fg=TEXT,
                 font=FONT_TITLE).pack(anchor="w")
        tk.Label(titles, text="Image degradation and restoration  •  Project 2 Guide 2",
                 bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w")

        Button(header, "Open Image", self.open_image, primary=True).pack(side=tk.RIGHT, padx=20)

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status = tk.Label(bar, text="Open an image to begin.", bg=SURFACE, fg=TEXT_MUTED,
                               font=FONT_SMALL, anchor="w")
        self.status.pack(fill=tk.X, padx=20, pady=6)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=SURFACE, width=370,
                           highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
        sidebar.pack_propagate(False)  # keep the fixed width

        inner = tk.Frame(sidebar, bg=SURFACE)
        inner.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)

        self._build_degrade_section(inner)
        tk.Frame(inner, bg=BORDER, height=1).pack(fill=tk.X, pady=18)  # divider
        self._build_restore_section(inner)

    def _section_title(self, parent, number, title, subtitle):
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill=tk.X, pady=(0, 10))
        tk.Label(row, text=number, bg=ACCENT, fg="#ffffff", font=FONT_SECTION,
                 width=2).pack(side=tk.LEFT, padx=(0, 10))
        text = tk.Frame(row, bg=SURFACE)
        text.pack(side=tk.LEFT)
        tk.Label(text, text=title, bg=SURFACE, fg=TEXT, font=FONT_SECTION).pack(anchor="w")
        tk.Label(text, text=subtitle, bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w")

    def _build_degrade_section(self, parent):
        self._section_title(parent, "1", "Degrade", "Add noise to the image")

        self.noise_type = SegmentedControl(parent, NOISE_TYPES, "Salt & Pepper",
                                           on_change=self._show_noise_settings)
        self.noise_type.pack(fill=tk.X)

        # One settings panel per noise type; only the selected one is shown.
        holder = tk.Frame(parent, bg=SURFACE)
        holder.pack(fill=tk.X, pady=(10, 0))
        self.noise_panels = {name: tk.Frame(holder, bg=SURFACE) for name in NOISE_TYPES}

        def two(v): return f"{v:.2f}"
        def one(v): return f"{v:.0f}"

        panel = self.noise_panels["Salt & Pepper"]
        self.salt_prob = LabeledSlider(panel, "Salt probability (white)", 0, 0.5, 0.01, 0.05, two)
        self.pepper_prob = LabeledSlider(panel, "Pepper probability (black)", 0, 0.5, 0.01, 0.05, two)

        panel = self.noise_panels["Gaussian"]
        self.gauss_mean = LabeledSlider(panel, "Mean", -50, 50, 1, 0, one)
        self.gauss_sigma = LabeledSlider(panel, "Standard deviation (σ)", 1, 80, 1, 20, one)

        panel = self.noise_panels["Rayleigh"]
        self.rayleigh_a = LabeledSlider(panel, "a (offset)", 0, 100, 1, 0, one)
        self.rayleigh_b = LabeledSlider(panel, "b (spread)", 50, 5000, 50, 800, one)

        for slider in (self.salt_prob, self.pepper_prob, self.gauss_mean,
                       self.gauss_sigma, self.rayleigh_a, self.rayleigh_b):
            slider.pack(fill=tk.X, pady=(0, 8))

        self._show_noise_settings("Salt & Pepper")

        Button(parent, "Add Noise", self.add_noise, primary=True).pack(fill=tk.X, pady=(4, 0))

    def _build_restore_section(self, parent):
        self._section_title(parent, "2", "Restore", "Filter the degraded image")

        self.filter_type = SegmentedControl(parent, FILTER_TYPES, "Contraharmonic",
                                            on_change=self._show_filter_settings)
        self.filter_type.pack(fill=tk.X)

        self.filter_hint = tk.Label(parent, bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL,
                                    wraplength=330, justify=tk.LEFT, anchor="w")
        self.filter_hint.pack(fill=tk.X, pady=(8, 8))

        self.kernel_size = LabeledSlider(parent, "Kernel size", 3, 9, 2, 3,
                                         lambda v: f"{int(v)} × {int(v)}")
        self.kernel_size.pack(fill=tk.X, pady=(0, 8))

        # Q only matters for the contraharmonic filter, so it lives in its own holder.
        self.q_holder = tk.Frame(parent, bg=SURFACE)
        self.q_holder.pack(fill=tk.X)
        self.q_value = LabeledSlider(self.q_holder, "Order Q", -3, 3, 0.1, 1.5, lambda v: f"{v:+.1f}")
        self.q_value.pack(fill=tk.X, pady=(0, 8))

        buttons = tk.Frame(parent, bg=SURFACE)
        buttons.pack(fill=tk.X, pady=(4, 0))
        buttons.grid_columnconfigure((0, 1), weight=1, uniform="buttons")
        self.filter_buttons = buttons
        Button(buttons, "Apply Filter", lambda: self.apply_filter(again=False),
               primary=True).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        Button(buttons, "Apply Again", lambda: self.apply_filter(again=True)
               ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self._show_filter_settings("Contraharmonic")

    def _build_cards(self, parent):
        cards = tk.Frame(parent, bg=BG)
        cards.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cards.grid_rowconfigure(0, weight=1)
        cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards")

        self.original_card = ImageCard(cards, "Original")
        self.noisy_card = ImageCard(cards, "Degraded", show_histogram=True, selectable=True)
        self.restored_card = ImageCard(cards, "Restored")

        for column, card in enumerate((self.original_card, self.noisy_card, self.restored_card)):
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))

    # ===================================================== show / hide settings
    def _show_noise_settings(self, noise_type):
        for name, panel in self.noise_panels.items():
            if name == noise_type:
                panel.pack(fill=tk.X)
            else:
                panel.pack_forget()

    def _show_filter_settings(self, filter_type):
        self.filter_hint.configure(text=FILTER_HINTS[filter_type])
        if filter_type == "Contraharmonic":
            self.q_holder.pack(fill=tk.X, before=self.filter_buttons)  # keep it above the buttons
        else:
            self.q_holder.pack_forget()

    # ================================================================ actions
    def open_image(self):
        path = filedialog.askopenfilename(title="Open Image", filetypes=IMAGE_TYPES)
        if not path:
            return
        try:
            with Image.open(path) as img:
                gray = np.array(img.convert("L"), dtype=np.uint8)
        except Exception as error:
            messagebox.showerror("Couldn't open image", str(error))
            return

        self.original, self.noisy, self.restored, self.passes = gray, None, None, 0
        h, w = gray.shape
        self.original_card.set_image(gray, f"{w} × {h} px, grayscale")
        self.noisy_card.set_image(None)
        self.restored_card.set_image(None)
        self.set_status(f"Opened {path}. Next: choose a noise type and click Add Noise.")

    def add_noise(self):
        """Item a: degrade the original image with the selected noise."""
        if self.original is None:
            self.set_status("Open an image first.")
            return

        noise_type = self.noise_type.value
        if noise_type == "Salt & Pepper":
            salt, pepper = self.salt_prob.get(), self.pepper_prob.get()
            self.noisy = add_salt_and_pepper_noise(self.original, salt, pepper)
            description = f"Salt & pepper  •  Ps = {salt:.2f}, Pp = {pepper:.2f}"
        elif noise_type == "Gaussian":
            mean, sigma = self.gauss_mean.get(), self.gauss_sigma.get()
            self.noisy = add_gaussian_noise(self.original, mean, sigma)
            description = f"Gaussian  •  mean = {mean:.0f}, σ = {sigma:.0f}"
        else:
            a, b = self.rayleigh_a.get(), self.rayleigh_b.get()
            self.noisy = add_rayleigh_noise(self.original, a, b)
            description = f"Rayleigh  •  a = {a:.0f}, b = {b:.0f}"

        self.restored, self.passes = None, 0
        self.noisy_card.set_image(self.noisy, description)
        self.restored_card.set_image(None)
        self.set_status(f"Added {description}. Next: pick a filter and click Apply Filter.")

    def apply_filter(self, again):
        """
        Item b.ii: restore the degraded image.
        Apply Filter -> filters the degraded image (pass 1).
        Apply Again  -> filters the last result again (pass 2, 3, ...).
        """
        if self.noisy is None:
            self.set_status("Add noise first (step 1).")
            return

        if again and self.restored is not None:
            source, self.passes = self.restored, self.passes + 1
        else:
            source, self.passes = self.noisy, 1

        filter_type = self.filter_type.value
        size = int(self.kernel_size.get())
        q = round(self.q_value.get(), 1)

        self.root.configure(cursor="watch")
        self.root.update_idletasks()
        try:
            if filter_type == "Geometric":
                self.restored = geometric_mean_filter(source, size)
                description = f"Geometric mean {size}×{size}"
            elif filter_type == "Contraharmonic":
                self.restored = contraharmonic_mean_filter(source, size, q)
                description = f"Contraharmonic {size}×{size}, Q = {q:+.1f}"
            else:
                self.restored = median_filter(source, size)
                description = f"Median {size}×{size}"
        finally:
            self.root.configure(cursor="")

        self.restored_card.set_image(self.restored, f"{description}  •  pass {self.passes}")
        self.set_status(f"Applied {description} (pass {self.passes}).")

    def set_status(self, message):
        self.status.configure(text=message)
