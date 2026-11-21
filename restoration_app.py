"""
Entry point for the Noise & Restoration window (CMSC 162 Project 2 Guide 2).

    run using: python restoration_app.py
"""

import ctypes
import tkinter as tk

from restoration_ui.window import RestorationWindow

# Sharper text on high-DPI Windows displays (no-op elsewhere).
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

if __name__ == "__main__":
    root = tk.Tk()
    RestorationWindow(root)
    root.mainloop()
