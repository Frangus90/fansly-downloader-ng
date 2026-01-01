#!/usr/bin/env python3
"""Test script for crop tool features"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from gui.tools.image_crop_window import ImageCropWindow


def main():
    """Launch a test window with the crop tool"""
    # Set appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Create root window (required for CTkToplevel)
    root = ctk.CTk()
    root.withdraw()  # Hide the root window

    # Create and show crop window
    crop_window = ImageCropWindow(root)

    # Handle window close
    def on_closing():
        crop_window.destroy()
        root.destroy()

    crop_window.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the event loop
    root.mainloop()


if __name__ == "__main__":
    main()
