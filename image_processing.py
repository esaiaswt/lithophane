# Lithophane Generator - Image Processing Module
# Image resize, grayscale conversion, thickness mapping (functional style, no classes)

import os
import io

import numpy as np
from PIL import Image


ACCEPTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def validate_file_extension(filename: str) -> bool:
    """Check if filename has an accepted extension (.jpg, .jpeg, .png).

    Case-insensitive comparison.

    Args:
        filename: The filename string to validate.

    Returns:
        True if the extension is accepted, False otherwise.
    """
    _, ext = os.path.splitext(filename)
    return ext.lower() in ACCEPTED_EXTENSIONS


def load_image(file_bytes: bytes) -> np.ndarray:
    """Load image bytes into a PIL Image, convert to RGB, return as numpy array.

    Args:
        file_bytes: Raw image file bytes.

    Returns:
        RGB image as numpy array with shape (H, W, 3) and dtype uint8.

    Raises:
        ValueError: If the image data is corrupt or unreadable.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()
        # Re-open after verify (verify may leave file in unusable state)
        image = Image.open(io.BytesIO(file_bytes))
        rgb_image = image.convert("RGB")
        return np.array(rgb_image, dtype=np.uint8)
    except Exception as e:
        raise ValueError(f"Unable to load image: {e}") from e


def resize_image(
    image: np.ndarray,
    target_width_mm: float,
    target_height_mm: float,
    pixels_per_mm: float = 1.0,
) -> np.ndarray:
    """Resize image to fit target dimensions while preserving aspect ratio.

    Computes the target pixel box from mm dimensions and pixels_per_mm,
    then scales the image to fit within that box while maintaining the
    original aspect ratio.

    Args:
        image: RGB image as numpy array with shape (H, W, 3), dtype uint8.
        target_width_mm: Target width in millimeters.
        target_height_mm: Target height in millimeters.
        pixels_per_mm: Resolution in pixels per millimeter (default 1.0).

    Returns:
        Resized RGB image as numpy array with shape (H', W', 3), dtype uint8.
    """
    src_h, src_w = image.shape[:2]

    # Compute target pixel bounds
    target_w_px = round(target_width_mm * pixels_per_mm)
    target_h_px = round(target_height_mm * pixels_per_mm)

    # Calculate scale factor to fit within target box while preserving aspect ratio
    scale_w = target_w_px / src_w
    scale_h = target_h_px / src_h
    scale = min(scale_w, scale_h)

    # Compute fitted pixel dimensions
    new_w = round(src_w * scale)
    new_h = round(src_h * scale)

    # Ensure at least 1 pixel in each dimension
    new_w = max(1, new_w)
    new_h = max(1, new_h)

    # Convert numpy array to PIL Image, resize, convert back
    pil_image = Image.fromarray(image)
    resized_pil = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return np.array(resized_pil, dtype=np.uint8)


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert RGB image to grayscale using standard luminance weights.

    Applies the formula: 0.2989*R + 0.5870*G + 0.1140*B

    Args:
        image: RGB image as numpy array with shape (H, W, 3), dtype uint8.

    Returns:
        2D grayscale array with shape (H, W), dtype uint8, values in [0, 255].
    """
    r = image[:, :, 0].astype(np.float64)
    g = image[:, :, 1].astype(np.float64)
    b = image[:, :, 2].astype(np.float64)

    grayscale = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return np.round(grayscale).astype(np.uint8)


def enhance_contrast(grayscale: np.ndarray, method: str = "none") -> np.ndarray:
    """Enhance contrast of a grayscale image for better lithophane results.

    Args:
        grayscale: 2D numpy array with intensity values 0-255, dtype uint8.
        method: Enhancement method - "none", "histogram_stretch", or "clahe".

    Returns:
        2D uint8 array with enhanced contrast, values in [0, 255].
    """
    if method == "none":
        return grayscale

    if method == "histogram_stretch":
        # Linear stretch: map actual min-max to full 0-255 range
        img_min = float(grayscale.min())
        img_max = float(grayscale.max())
        if img_max - img_min < 1.0:
            return grayscale
        stretched = (grayscale.astype(np.float64) - img_min) / (img_max - img_min) * 255.0
        return np.round(stretched).astype(np.uint8)

    if method == "clahe":
        # Contrast Limited Adaptive Histogram Equalization
        # Implemented with numpy (no OpenCV dependency)
        # Use a simplified global histogram equalization
        hist, bins = np.histogram(grayscale.ravel(), bins=256, range=(0, 256))
        cdf = hist.cumsum()
        # Mask zero values in cdf
        cdf_masked = np.ma.masked_equal(cdf, 0)
        cdf_normalized = (cdf_masked - cdf_masked.min()) * 255 / (cdf_masked.max() - cdf_masked.min())
        cdf_final = np.ma.filled(cdf_normalized, 0).astype(np.uint8)
        return cdf_final[grayscale]

    return grayscale


def compute_thickness_map(
    grayscale: np.ndarray,
    min_thickness: float = 0.4,
    max_thickness: float = 2.0,
) -> np.ndarray:
    """Map grayscale intensity to physical thickness.

    Intensity 0 (darkest) maps to max_thickness.
    Intensity 255 (lightest) maps to min_thickness.
    Linear interpolation for intermediate values.

    Formula: thickness = max_thickness - (intensity / 255) * (max_thickness - min_thickness)

    Args:
        grayscale: 2D numpy array with intensity values 0-255.
        min_thickness: Minimum thickness in mm (default 0.4).
        max_thickness: Maximum thickness in mm (default 2.0).

    Returns:
        2D float64 array with thickness values in [min_thickness, max_thickness].

    Raises:
        ValueError: If input contains NaN, Inf, or is not a 2D array.
    """
    if not isinstance(grayscale, np.ndarray):
        raise ValueError("Input must be a numpy ndarray.")

    if grayscale.ndim != 2:
        raise ValueError(
            f"Input must be a 2D array, got {grayscale.ndim}D array."
        )

    if np.issubdtype(grayscale.dtype, np.floating):
        if np.any(np.isnan(grayscale)):
            raise ValueError("Input array contains NaN values.")
        if np.any(np.isinf(grayscale)):
            raise ValueError("Input array contains Inf values.")

    intensity = grayscale.astype(np.float64)
    thickness = max_thickness - (intensity / 255.0) * (max_thickness - min_thickness)

    return thickness
