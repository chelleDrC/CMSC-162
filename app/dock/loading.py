"""
Shared "run a slow filter without freezing the window" helper.

The spatial-domain filters (averaging/median/highpass) are deliberately
implemented as plain Python sliding-window loops for clarity, which means
they can take a few seconds on a large image. Tkinter runs on a single
thread, so calling one of them directly from a button handler would freeze
the whole window until it finishes -- Windows would even grey it out and
label it "Not Responding".

_run_filter_async() avoids that: it runs the slow function on a background
thread, shows a small "Applying filter..." overlay over the tab while it
works, and hands the result back on the main thread (the only thread
allowed to touch Tkinter widgets) once it's done.
"""

import threading
import queue
import tkinter as tk
from tkinter import messagebox

from ..theme import BG_APP, TEXT_PRIMARY, FONT_UI


class BackgroundFilterMixin:
    def _run_filter_async(self, parent, compute_fn, on_result, loading_text="Applying filter"):
        """
        Parameters
        ----------
        parent : tk.Widget
            The dock tab's content frame -- covered by the loading overlay
            while compute_fn runs.
        compute_fn : callable
            A no-argument function that does the slow work (e.g. a lambda
            closing over the filter call) and returns its result.
        on_result : callable
            Called as on_result(result) on the main thread once
            compute_fn finishes. Skipped if the tab was closed meanwhile.
        """
        overlay = tk.Frame(parent, bg=BG_APP)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()
        label = tk.Label(overlay, text=loading_text, bg=BG_APP, fg=TEXT_PRIMARY, font=FONT_UI)
        label.place(relx=0.5, rely=0.5, anchor="center")

        # Animate "Applying filter" -> "Applying filter." -> "..." so it's
        # visibly alive rather than looking like a frozen screenshot.
        dots = {"n": 0}

        def animate():
            if not overlay.winfo_exists():
                return
            dots["n"] = (dots["n"] + 1) % 4
            label.configure(text=loading_text + "." * dots["n"])
            self.root.after(350, animate)

        animate()

        result_queue = queue.Queue()

        def worker():
            try:
                result_queue.put((compute_fn(), None))
            except Exception as exc:  # surfaced on the main thread below
                result_queue.put((None, exc))

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                result, error = result_queue.get_nowait()
            except queue.Empty:
                self.root.after(50, poll)
                return

            if not parent.winfo_exists():
                return  # the tab was closed while this was running

            overlay.destroy()
            if error is not None:
                messagebox.showerror("Filter Failed", str(error))
                return
            on_result(result)

        self.root.after(50, poll)
