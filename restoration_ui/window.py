import threading
import tkinter as tk
from tkinter import filedialog, messagebox

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
# "Contraharmonic" is too wide for its button, so it is shown on two lines.
FILTER_LABELS = {"Contraharmonic": "Contra-\nharmonic"}

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
        self.original = None   # clean grayscale image: list of rows, gray[y][x] in 0-255
        self.noisy = None      # degraded image (item a)
        self.restored = None   # filtered image (item b.ii)
        self.passes = 0        # how many times the current filter has been applied
        self.busy = False      # True while a filter is running in the background
        self.history = []      # one (image, subtitle) per filter pass, used by Undo Pass

        root.title("Noise & Restoration — CMSC 162 Project 2 Guide 2")
        root.geometry("1360x840")
        root.minsize(1100, 780)
        root.configure(bg=BG)

        self._build_header()
        self._build_status_bar()

        body = tk.Frame(root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
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
        tk.Label(titles, text="Project 2 Guide 2",
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
        inner.pack(fill=tk.BOTH, expand=True, padx=18, pady=12)

        self._build_degrade_section(inner)
        tk.Frame(inner, bg=BORDER, height=1).pack(fill=tk.X, pady=12)  # divider
        self._build_restore_section(inner)

    def _caption(self, parent, text, wraplength=330):
        return tk.Label(parent, text=text, bg=SURFACE, fg=TEXT_MUTED, font=FONT_SMALL,
                        wraplength=wraplength, justify=tk.LEFT, anchor="w")

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
        self._caption(parent, "Always starts from the original image, so noise does not stack."
                      ).pack(fill=tk.X, pady=(2, 0))

    def _build_restore_section(self, parent):
        self._section_title(parent, "2", "Restore", "Filter the degraded image")

        self.filter_type = SegmentedControl(parent, FILTER_TYPES, "Contraharmonic",
                                            on_change=self._show_filter_settings,
                                            labels=FILTER_LABELS)
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
        self.filter_buttons = buttons  # the Q slider is packed just above this frame

        Button(buttons, "Apply Filter", lambda: self.apply_filter(again=False),
               primary=True).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        Button(buttons, "Apply Again", lambda: self.apply_filter(again=True)
               ).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self._caption(buttons, "One pass on the degraded image (does not stack).",
                      wraplength=150).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=(2, 0))
        self._caption(buttons, "Another pass on the result (stacks with each click).",
                      wraplength=150).grid(row=1, column=1, sticky="w", padx=(4, 0), pady=(2, 0))

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

        self._build_restore_actions(self.restored_card.footer)

    def _build_restore_actions(self, footer):
        """Undo Pass and Reset sit under the Restored image."""
        footer.grid_columnconfigure((0, 1), weight=1, uniform="restore_actions")
        guides = []
        for column, (text, command, guide) in enumerate((
                ("Undo Pass", self.undo_pass, "Goes back one filter pass"),
                ("Reset", self.reset, "Clears all noise and filter"))):
            padx = (0, 4) if column == 0 else (4, 0)
            Button(footer, text, command).grid(row=0, column=column, sticky="ew",
                                               padx=padx, pady=(10, 0))
            label = self._caption(footer, guide, wraplength=100)
            label.grid(row=1, column=column, sticky="w", padx=padx, pady=(2, 0))
            guides.append(label)

        def fit_guides(event):  # wrap the guides to the card width as the window resizes
            for label in guides:
                label.configure(wraplength=max(event.width // 2 - 8, 60))
        footer.bind("<Configure>", fit_guides)

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
        if self.busy:
            self.set_status("Wait for the filter to finish first.")
            return
        path = filedialog.askopenfilename(title="Open Image", filetypes=IMAGE_TYPES)
        if not path:
            return
        try:
            with Image.open(path) as img:
                gray_img = img.convert("L")
                w, h = gray_img.size
                pixels = list(gray_img.tobytes()) 
        except Exception as error:
            messagebox.showerror("Couldn't open image", str(error))
            return

        gray = [pixels[y * w:(y + 1) * w] for y in range(h)]  # cut into rows: gray[y][x]
        self.original, self.noisy, self.restored, self.passes = gray, None, None, 0
        self.history = []
        self.original_card.set_image(gray, f"{w} × {h} px, grayscale")
        self.noisy_card.set_image(None)
        self.restored_card.set_image(None)
        self.set_status(f"Opened {path}. Next: choose a noise type and click Add Noise.")

    def add_noise(self):
        """Item a: degrade the original image with the selected noise."""
        if self.original is None:
            self.set_status("Open an image first.")
            return
        if self.busy:
            self.set_status("Wait for the filter to finish first.")
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

        self.restored, self.passes, self.history = None, 0, []
        self.noisy_card.set_image(self.noisy, description)
        self.restored_card.set_image(None)
        self.set_status(f"Added {description}. Next: pick a filter and click Apply Filter.")

    def apply_filter(self, again):
        """
        Item b.ii: restore the degraded image.
        Apply Filter -> filters the degraded image (pass 1).
        Apply Again  -> filters the last result again (pass 2, 3, ...).

        The filter runs in a background thread so the window stays responsive;
        _finish_filter picks up the result when the thread is done.
        """
        if self.busy:
            self.set_status("A filter is still running.")
            return
        if self.noisy is None:
            self.set_status("Add noise first (step 1).")
            return

        if again and self.restored is not None:
            source, passes = self.restored, self.passes + 1
        else:
            source, passes = self.noisy, 1

        filter_type = self.filter_type.value
        size = int(self.kernel_size.get())
        q = round(self.q_value.get(), 1)

        if filter_type == "Geometric":
            run = lambda: geometric_mean_filter(source, size)
            description = f"Geometric mean {size}×{size}"
        elif filter_type == "Contraharmonic":
            run = lambda: contraharmonic_mean_filter(source, size, q)
            description = f"Contraharmonic {size}×{size}, Q = {q:+.1f}"
        else:
            run = lambda: median_filter(source, size)
            description = f"Median {size}×{size}"

        outcome = {}  # the worker thread leaves its result (or error) here

        def work():
            try:
                outcome["image"] = run()
            except Exception as error:
                outcome["error"] = error

        self.busy = True
        self.root.configure(cursor="watch")
        self.set_status(f"Applying {description} (pass {passes})…")
        worker = threading.Thread(target=work, daemon=True)
        worker.start()
        self._finish_filter(worker, outcome, description, passes)

    def _finish_filter(self, worker, outcome, description, passes):
        """Check every 100 ms whether the filter thread is done, then show the result."""
        if worker.is_alive():
            self.root.after(100, self._finish_filter, worker, outcome, description, passes)
            return

        self.busy = False
        self.root.configure(cursor="")
        if "error" in outcome:
            messagebox.showerror("Filter failed", str(outcome["error"]))
            self.set_status("The filter failed.")
            return

        subtitle = f"{description}  •  pass {passes}"
        if passes == 1:
            self.history = []  # a fresh Apply Filter starts a new chain of passes
        self.history.append((outcome["image"], subtitle))
        self.restored, self.passes = outcome["image"], passes
        self.restored_card.set_image(self.restored, subtitle)
        self.set_status(f"Applied {description} (pass {passes}).")

    def undo_pass(self):
        """Go back one filter pass: pass 3 -> pass 2 -> pass 1 -> degraded image only."""
        if self.busy:
            self.set_status("Wait for the filter to finish first.")
            return
        if not self.history:
            self.set_status("Nothing to undo.")
            return

        self.history.pop()
        self.passes = len(self.history)
        if self.history:
            self.restored, subtitle = self.history[-1]
            self.restored_card.set_image(self.restored, subtitle)
            self.set_status(f"Undid one pass. Showing pass {self.passes}.")
        else:
            self.restored = None
            self.restored_card.set_image(None)
            self.set_status("Undid the last pass. Back to the degraded image.")

    def reset(self):
        """Clear the degraded and restored images."""
        if self.busy:
            self.set_status("Wait for the filter to finish first.")
            return
        if self.original is None:
            self.set_status("Open an image first.")
            return

        self.noisy, self.restored, self.passes, self.history = None, None, 0, []
        self.noisy_card.set_image(None)
        self.restored_card.set_image(None)
        self.set_status("Reset. The original is still loaded: choose a noise type and click Add Noise.")

    def set_status(self, message):
        self.status.configure(text=message)
