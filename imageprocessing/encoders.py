"""Optional encoder integrations with graceful fallback.

This module provides wrappers for optional image processing dependencies:
- SSIM quality validation (requires scikit-image)
- MozJPEG lossless optimization (requires mozjpeg-lossless-optimization)

All functions gracefully degrade if dependencies are not installed.
"""

from typing import Optional
import numpy as np
from PIL import Image

# SSIM availability check
try:
    from skimage.metrics import structural_similarity
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False

# MozJPEG availability check
try:
    import mozjpeg_lossless_optimization
    MOZJPEG_AVAILABLE = True
except ImportError:
    MOZJPEG_AVAILABLE = False


# Chroma subsampling modes for JPEG
# These map to Pillow's subsampling parameter values
CHROMA_SUBSAMPLING = {
    'best': 0,      # 4:4:4 - No subsampling, best quality
    'balanced': 1,  # 4:2:2 - Horizontal subsampling
    'smallest': 2,  # 4:2:0 - Both directions, smallest files (default)
}

# Human-readable labels for UI
CHROMA_LABELS = {
    0: "Best Quality (4:4:4)",
    1: "Balanced (4:2:2)",
    2: "Smallest (4:2:0)",
}


def get_encoder_capabilities() -> dict:
    """Return available encoder features for UI display.

    Returns:
        dict with boolean flags for each optional feature
    """
    return {
        'ssim_validation': SSIM_AVAILABLE,
        'mozjpeg_optimization': MOZJPEG_AVAILABLE,
    }


def calculate_ssim(
    original: Image.Image,
    compressed: Image.Image,
    channel_axis: int = -1
) -> Optional[float]:
    """Calculate SSIM between two images.

    Args:
        original: Original PIL Image
        compressed: Compressed PIL Image
        channel_axis: Axis for color channels (default -1 for last axis)

    Returns:
        SSIM score (0.0 to 1.0) or None if scikit-image unavailable
    """
    if not SSIM_AVAILABLE:
        return None

    # Convert to same mode for comparison
    if original.mode != compressed.mode:
        compressed = compressed.convert(original.mode)

    # Resize compressed to match original if dimensions differ
    if original.size != compressed.size:
        compressed = compressed.resize(original.size, Image.Resampling.LANCZOS)

    # Convert to numpy arrays
    orig_array = np.array(original)
    comp_array = np.array(compressed)

    # Handle grayscale vs color
    if len(orig_array.shape) == 2:
        # Grayscale - no channel axis
        return structural_similarity(orig_array, comp_array, data_range=255)
    else:
        # Color image
        return structural_similarity(
            orig_array,
            comp_array,
            data_range=255,
            channel_axis=channel_axis
        )


def optimize_with_mozjpeg(jpeg_bytes: bytes) -> bytes:
    """Apply MozJPEG lossless optimization to JPEG data.

    This applies optimal Huffman coding and progressive encoding
    without any quality loss.

    Args:
        jpeg_bytes: Raw JPEG file bytes

    Returns:
        Optimized JPEG bytes, or original if MozJPEG unavailable
    """
    if not MOZJPEG_AVAILABLE:
        return jpeg_bytes

    try:
        return mozjpeg_lossless_optimization.optimize(jpeg_bytes)
    except Exception:
        # If optimization fails, return original
        return jpeg_bytes
