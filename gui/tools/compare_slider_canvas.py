"""Before/After comparison slider widget for compression preview"""

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
from typing import Optional, Callable


class CompareSliderCanvas(ctk.CTkFrame):
    """Canvas widget with before/after slider for compression comparison"""

    def __init__(
        self,
        parent,
        on_request_comparison: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)

        self.on_request_comparison = on_request_comparison

        # Image state
        self.original_image: Optional[Image.Image] = None
        self.compressed_image: Optional[Image.Image] = None
        self.display_composite: Optional[ImageTk.PhotoImage] = None

        # Slider position (0.0 to 1.0, where 0.5 is center)
        self.slider_position = 0.5

        # Canvas dimensions
        self.canvas_width = 600
        self.canvas_height = 500

        # Image display area
        self.display_width = 0
        self.display_height = 0
        self.image_x_offset = 0
        self.image_y_offset = 0

        # Zoom and pan state
        self.zoom_level = 1.0  # 1.0 = fit to canvas
        self.min_zoom = 1.0
        self.max_zoom = 10.0
        self.pan_x = 0.0  # Pan offset as ratio of image (0.0 = centered)
        self.pan_y = 0.0

        # Comparison data
        self.ssim_score: Optional[float] = None
        self.original_size_bytes: Optional[int] = None
        self.compressed_size_bytes: Optional[int] = None

        # Dragging state
        self.is_dragging = False
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_start_offset_x = 0.0
        self.pan_start_offset_y = 0.0

        self._build_ui()

    def _build_ui(self):
        """Build the comparison slider UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Compression Preview",
            font=("Arial", 18, "bold"),
            anchor="w"
        )
        title.pack(padx=15, pady=(15, 5), anchor="w")

        # Canvas frame
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='#2b2b2b',
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Bind events - slider dragging (left click)
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Bind events - zoom (mouse wheel)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)     # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)     # Linux scroll down

        # Bind events - pan (right click drag)
        self.canvas.bind("<Button-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_end)

        # Info labels frame
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=(0, 5))

        # Original size label (left)
        self.original_label = ctk.CTkLabel(
            info_frame,
            text="Original: --",
            font=("Arial", 10),
            anchor="w"
        )
        self.original_label.pack(side="left", padx=10)

        # SSIM label (center)
        self.ssim_label = ctk.CTkLabel(
            info_frame,
            text="SSIM: --",
            font=("Arial", 11, "bold"),
            text_color="#3b8ed0"
        )
        self.ssim_label.pack(side="left", expand=True)

        # Compressed size label (right)
        self.compressed_label = ctk.CTkLabel(
            info_frame,
            text="Compressed: --",
            font=("Arial", 10),
            anchor="e"
        )
        self.compressed_label.pack(side="right", padx=10)

        # Zoom controls frame
        zoom_frame = ctk.CTkFrame(self)
        zoom_frame.pack(fill="x", padx=10, pady=(0, 5))

        # Zoom label
        self.zoom_label = ctk.CTkLabel(
            zoom_frame,
            text="Zoom: 100%",
            font=("Arial", 10),
            width=80
        )
        self.zoom_label.pack(side="left", padx=5)

        # Zoom out button
        zoom_out_btn = ctk.CTkButton(
            zoom_frame,
            text="-",
            command=self._zoom_out,
            width=30,
            height=24
        )
        zoom_out_btn.pack(side="left", padx=2)

        # Zoom in button
        zoom_in_btn = ctk.CTkButton(
            zoom_frame,
            text="+",
            command=self._zoom_in,
            width=30,
            height=24
        )
        zoom_in_btn.pack(side="left", padx=2)

        # Reset zoom button
        reset_zoom_btn = ctk.CTkButton(
            zoom_frame,
            text="Reset",
            command=self._reset_zoom,
            width=50,
            height=24
        )
        reset_zoom_btn.pack(side="left", padx=5)

        # Hint label
        hint_label = ctk.CTkLabel(
            zoom_frame,
            text="Scroll to zoom • Right-drag to pan",
            font=("Arial", 9),
            text_color="gray50"
        )
        hint_label.pack(side="right", padx=5)

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self,
            text="Refresh Preview",
            command=self._on_refresh,
            height=30
        )
        self.refresh_btn.pack(pady=(0, 10))

        # Empty state label (shown when no comparison)
        self.empty_label = ctk.CTkLabel(
            self.canvas,
            text="No comparison available\n\nLoad an image and adjust settings,\nthen switch to this tab to see the comparison.",
            font=("Arial", 12),
            text_color="gray60",
            justify="center"
        )
        # Position will be set on canvas resize

        # Lossless format flag
        self.is_lossless = False

    def set_images(
        self,
        original: Image.Image,
        compressed: Image.Image,
        original_size_bytes: int,
        compressed_size_bytes: int,
        ssim_score: Optional[float] = None,
        is_lossless: bool = False
    ):
        """Set the original and compressed images for comparison.

        Args:
            original: Original PIL Image
            compressed: Compressed PIL Image
            original_size_bytes: Size of original in bytes
            compressed_size_bytes: Size of compressed in bytes
            ssim_score: Optional SSIM score (0.0 to 1.0)
            is_lossless: True if format is lossless (PNG)
        """
        # Check if widget still exists (window may have been closed)
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self.original_image = original.copy()
        self.compressed_image = compressed.copy()
        self.original_size_bytes = original_size_bytes
        self.compressed_size_bytes = compressed_size_bytes
        self.ssim_score = ssim_score
        self.is_lossless = is_lossless

        # Hide empty label
        self.canvas.delete("empty_label")

        # Update info labels
        self._update_info_labels()

        # Redraw
        self._draw_comparison()

    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes as human-readable size"""
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def _draw_comparison(self):
        """Draw the before/after comparison with slider, applying zoom and pan"""
        self.canvas.delete("all")

        if not self.original_image or not self.compressed_image:
            self._show_empty_state()
            return

        # Get canvas size
        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()

        if self.canvas_width < 10 or self.canvas_height < 10:
            return

        # Calculate base scale (fit to canvas at zoom 1.0)
        orig_w, orig_h = self.original_image.size
        width_scale = (self.canvas_width - 40) / orig_w
        height_scale = (self.canvas_height - 40) / orig_h
        base_scale = min(width_scale, height_scale, 1.0)

        # Apply zoom to scale
        effective_scale = base_scale * self.zoom_level

        # Full zoomed image dimensions
        zoomed_width = int(orig_w * effective_scale)
        zoomed_height = int(orig_h * effective_scale)

        # Viewport (what we display) is limited to canvas size
        self.display_width = min(zoomed_width, self.canvas_width - 20)
        self.display_height = min(zoomed_height, self.canvas_height - 20)

        # Calculate pan bounds (how far we can pan)
        max_pan_x = max(0, (zoomed_width - self.display_width) / 2)
        max_pan_y = max(0, (zoomed_height - self.display_height) / 2)

        # Clamp pan values
        self.pan_x = max(-max_pan_x, min(max_pan_x, self.pan_x))
        self.pan_y = max(-max_pan_y, min(max_pan_y, self.pan_y))

        # Calculate crop region from original image
        # Center of the crop in zoomed coordinates
        crop_center_x = zoomed_width / 2 + self.pan_x
        crop_center_y = zoomed_height / 2 + self.pan_y

        # Crop box in zoomed image coordinates
        crop_x1 = crop_center_x - self.display_width / 2
        crop_y1 = crop_center_y - self.display_height / 2
        crop_x2 = crop_x1 + self.display_width
        crop_y2 = crop_y1 + self.display_height

        # Convert to original image coordinates
        orig_crop_x1 = int(crop_x1 / effective_scale)
        orig_crop_y1 = int(crop_y1 / effective_scale)
        orig_crop_x2 = int(crop_x2 / effective_scale)
        orig_crop_y2 = int(crop_y2 / effective_scale)

        # Clamp to image bounds
        orig_crop_x1 = max(0, min(orig_w, orig_crop_x1))
        orig_crop_y1 = max(0, min(orig_h, orig_crop_y1))
        orig_crop_x2 = max(0, min(orig_w, orig_crop_x2))
        orig_crop_y2 = max(0, min(orig_h, orig_crop_y2))

        # Crop and resize the region we want to display
        if orig_crop_x2 > orig_crop_x1 and orig_crop_y2 > orig_crop_y1:
            cropped_orig = self.original_image.crop((orig_crop_x1, orig_crop_y1, orig_crop_x2, orig_crop_y2))
            cropped_comp = self.compressed_image.crop((orig_crop_x1, orig_crop_y1, orig_crop_x2, orig_crop_y2))

            # Resize cropped region to display size
            display_orig = cropped_orig.resize(
                (self.display_width, self.display_height),
                Image.Resampling.LANCZOS
            )
            display_comp = cropped_comp.resize(
                (self.display_width, self.display_height),
                Image.Resampling.LANCZOS
            )
        else:
            # Fallback if crop is invalid
            display_orig = self.original_image.resize(
                (self.display_width, self.display_height),
                Image.Resampling.LANCZOS
            )
            display_comp = self.compressed_image.resize(
                (self.display_width, self.display_height),
                Image.Resampling.LANCZOS
            )

        # Calculate offsets to center the display
        self.image_x_offset = (self.canvas_width - self.display_width) // 2
        self.image_y_offset = (self.canvas_height - self.display_height) // 2

        # Calculate split position
        split_x = int(self.display_width * self.slider_position)

        # Composite: left side is original, right side is compressed
        composite = Image.new('RGB', (self.display_width, self.display_height))

        # Paste left portion of original
        if split_x > 0:
            left_box = (0, 0, split_x, self.display_height)
            composite.paste(display_orig.crop(left_box), (0, 0))

        # Paste right portion of compressed
        if split_x < self.display_width:
            right_box = (split_x, 0, self.display_width, self.display_height)
            composite.paste(display_comp.crop(right_box), (split_x, 0))

        # Convert to PhotoImage
        self.display_composite = ImageTk.PhotoImage(composite)

        # Draw composite image
        self.canvas.create_image(
            self.image_x_offset, self.image_y_offset,
            anchor="nw",
            image=self.display_composite,
            tags="image"
        )

        # Draw slider line
        slider_canvas_x = self.image_x_offset + split_x
        self.canvas.create_line(
            slider_canvas_x, self.image_y_offset - 5,
            slider_canvas_x, self.image_y_offset + self.display_height + 5,
            fill="white",
            width=2,
            tags="slider"
        )

        # Draw slider handle (circle)
        handle_y = self.image_y_offset + self.display_height // 2
        handle_radius = 15
        self.canvas.create_oval(
            slider_canvas_x - handle_radius, handle_y - handle_radius,
            slider_canvas_x + handle_radius, handle_y + handle_radius,
            fill="#3b8ed0",
            outline="white",
            width=2,
            tags="slider"
        )

        # Draw arrows on handle
        self.canvas.create_text(
            slider_canvas_x, handle_y,
            text="\u25C0  \u25B6",  # Left and right arrows
            fill="white",
            font=("Arial", 9, "bold"),
            tags="slider"
        )

        # Labels for left/right sides
        self.canvas.create_text(
            self.image_x_offset + 10, self.image_y_offset + 10,
            text="Original",
            anchor="nw",
            fill="white",
            font=("Arial", 10, "bold"),
            tags="label"
        )

        self.canvas.create_text(
            self.image_x_offset + self.display_width - 10, self.image_y_offset + 10,
            text="Compressed",
            anchor="ne",
            fill="white",
            font=("Arial", 10, "bold"),
            tags="label"
        )

        # Show lossless format banner if applicable
        if self.is_lossless:
            banner_y = self.image_y_offset + self.display_height + 15
            self.canvas.create_text(
                self.canvas_width // 2, banner_y,
                text="PNG is lossless - no quality difference visible. Use JPEG or WebP for compression preview.",
                fill="#ffc107",
                font=("Arial", 10),
                tags="banner"
            )

        # Update zoom label
        self._update_zoom_label()

    def _show_empty_state(self):
        """Show empty state message"""
        self.canvas.delete("all")
        cx = self.canvas_width // 2
        cy = self.canvas_height // 2
        self.canvas.create_text(
            cx, cy,
            text="No comparison available\n\nLoad an image and adjust settings,\nthen switch to this tab to see the comparison.",
            fill="gray60",
            font=("Arial", 12),
            justify="center",
            tags="empty_label"
        )

    def _on_mouse_down(self, event):
        """Handle mouse button press"""
        if self._is_near_slider(event.x):
            self.is_dragging = True
            self.canvas.configure(cursor="sb_h_double_arrow")

    def _on_mouse_drag(self, event):
        """Handle mouse drag"""
        if not self.is_dragging:
            return

        if not self.display_composite or self.display_width == 0:
            return

        # Calculate new slider position (clamped to image bounds)
        new_x = max(self.image_x_offset, min(event.x, self.image_x_offset + self.display_width))
        self.slider_position = (new_x - self.image_x_offset) / self.display_width

        # Redraw
        self._draw_comparison()

    def _on_mouse_up(self, event):
        """Handle mouse button release"""
        self.is_dragging = False
        self.canvas.configure(cursor="arrow")

    def _on_mouse_move(self, event):
        """Handle mouse movement (for cursor change)"""
        if not self.is_dragging:
            if self._is_near_slider(event.x):
                self.canvas.configure(cursor="sb_h_double_arrow")
            else:
                self.canvas.configure(cursor="arrow")

    def _is_near_slider(self, x: int) -> bool:
        """Check if x coordinate is near the slider"""
        if not self.display_composite or self.display_width == 0:
            return False

        slider_x = self.image_x_offset + int(self.display_width * self.slider_position)
        return abs(x - slider_x) < 20

    def _on_canvas_resize(self, event):
        """Handle canvas resize"""
        self.canvas_width = event.width
        self.canvas_height = event.height

        if self.original_image:
            self._draw_comparison()
        else:
            self._show_empty_state()

    def _update_info_labels(self):
        """Update the info labels with current data"""
        # Original size
        if self.original_size_bytes:
            orig_text = f"Original: {self._format_bytes(self.original_size_bytes)}"
        else:
            orig_text = "Original: --"
        self.original_label.configure(text=orig_text)

        # Compressed size
        if self.compressed_size_bytes:
            comp_text = f"Compressed: {self._format_bytes(self.compressed_size_bytes)}"
        else:
            comp_text = "Compressed: --"
        self.compressed_label.configure(text=comp_text)

        # SSIM score
        if self.ssim_score is not None:
            # Color code based on score
            if self.ssim_score >= 0.95:
                color = "#28a745"  # Green - excellent
            elif self.ssim_score >= 0.90:
                color = "#ffc107"  # Yellow - good
            else:
                color = "#dc3545"  # Red - poor
            self.ssim_label.configure(
                text=f"SSIM: {self.ssim_score:.4f}",
                text_color=color
            )
        else:
            self.ssim_label.configure(text="SSIM: N/A", text_color="gray60")

    def _on_refresh(self):
        """Handle refresh button click"""
        if self.on_request_comparison:
            self.on_request_comparison()

    def clear(self):
        """Clear the comparison display"""
        # Check if widget still exists (window may have been closed)
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self.original_image = None
        self.compressed_image = None
        self.display_composite = None
        self.ssim_score = None
        self.original_size_bytes = None
        self.compressed_size_bytes = None

        self._show_empty_state()
        self._update_info_labels()

    # =========================================================================
    # Zoom and Pan Methods
    # =========================================================================

    def _update_zoom_label(self):
        """Update the zoom percentage label"""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_label.configure(text=f"Zoom: {zoom_percent}%")

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        if not self.original_image:
            return

        # Get zoom direction
        if hasattr(event, 'delta'):
            # Windows
            delta = event.delta / 120
        elif event.num == 4:
            # Linux scroll up
            delta = 1
        else:
            # Linux scroll down
            delta = -1

        # Calculate new zoom level
        zoom_factor = 1.15  # 15% per scroll step
        if delta > 0:
            new_zoom = self.zoom_level * zoom_factor
        else:
            new_zoom = self.zoom_level / zoom_factor

        # Clamp zoom level
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))

        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self._draw_comparison()

    def _zoom_in(self):
        """Zoom in button handler"""
        if not self.original_image:
            return

        new_zoom = min(self.max_zoom, self.zoom_level * 1.25)
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self._draw_comparison()

    def _zoom_out(self):
        """Zoom out button handler"""
        if not self.original_image:
            return

        new_zoom = max(self.min_zoom, self.zoom_level / 1.25)
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self._draw_comparison()

    def _reset_zoom(self):
        """Reset zoom and pan to defaults"""
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        if self.original_image:
            self._draw_comparison()

    def _on_pan_start(self, event):
        """Handle right mouse button press for pan start"""
        if not self.original_image or self.zoom_level <= 1.0:
            return

        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.pan_start_offset_x = self.pan_x
        self.pan_start_offset_y = self.pan_y
        self.canvas.configure(cursor="fleur")

    def _on_pan_drag(self, event):
        """Handle right mouse button drag for panning"""
        if not self.is_panning:
            return

        # Calculate delta from drag start
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y

        # Apply delta to pan offset (invert for natural dragging)
        self.pan_x = self.pan_start_offset_x - dx
        self.pan_y = self.pan_start_offset_y - dy

        self._draw_comparison()

    def _on_pan_end(self, event):
        """Handle right mouse button release"""
        self.is_panning = False
        self.canvas.configure(cursor="arrow")
