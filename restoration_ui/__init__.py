"""
Noise & Restoration window (CMSC 162 Project 2 Guide 2).

A standalone, single-purpose UI on top of tools/restoration:

    theme.py    -- colors and fonts
    widgets.py  -- reusable pieces: Button, SegmentedControl, LabeledSlider, ImageCard
    window.py   -- RestorationWindow: lays out the sidebar + three image cards
                   (Original / Degraded / Restored) and connects the controls
                   to the noise and filter functions

Run it with:  python restoration_app.py
"""
