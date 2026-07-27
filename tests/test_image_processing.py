# Tests for image_processing module

import io

import numpy as np
import pytest
from PIL import Image

from image_processing import validate_file_extension, load_image


# --- validate_file_extension tests ---

class TestValidateFileExtension:
    def test_accepts_jpg(self):
        assert validate_file_extension("photo.jpg") is True

    def test_accepts_jpeg(self):
        assert validate_file_extension("photo.jpeg") is True

    def test_accepts_png(self):
        assert validate_file_extension("photo.png") is True

    def test_case_insensitive_jpg(self):
        assert validate_file_extension("photo.JPG") is True

    def test_case_insensitive_jpeg(self):
        assert validate_file_extension("photo.JPEG") is True

    def test_case_insensitive_png(self):
        assert validate_file_extension("photo.PNG") is True

    def test_mixed_case(self):
        assert validate_file_extension("photo.JpG") is True

    def test_rejects_gif(self):
        assert validate_file_extension("photo.gif") is False

    def test_rejects_bmp(self):
        assert validate_file_extension("photo.bmp") is False

    def test_rejects_tiff(self):
        assert validate_file_extension("photo.tiff") is False

    def test_rejects_no_extension(self):
        assert validate_file_extension("photo") is False

    def test_rejects_empty_string(self):
        assert validate_file_extension("") is False

    def test_dot_in_filename(self):
        assert validate_file_extension("my.photo.png") is True

    def test_rejects_partial_extension(self):
        assert validate_file_extension("photo.jp") is False


# --- load_image tests ---

class TestLoadImage:
    def _make_image_bytes(self, mode="RGB", size=(10, 10), color=(128, 64, 32), fmt="PNG"):
        img = Image.new(mode, size, color=color)
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    def test_loads_rgb_png(self):
        data = self._make_image_bytes(mode="RGB", color=(100, 150, 200), fmt="PNG")
        result = load_image(data)
        assert isinstance(result, np.ndarray)
        assert result.shape == (10, 10, 3)
        assert result.dtype == np.uint8
        assert result[0, 0, 0] == 100
        assert result[0, 0, 1] == 150
        assert result[0, 0, 2] == 200

    def test_loads_jpeg(self):
        data = self._make_image_bytes(mode="RGB", color=(100, 150, 200), fmt="JPEG")
        result = load_image(data)
        assert isinstance(result, np.ndarray)
        assert result.shape == (10, 10, 3)
        assert result.dtype == np.uint8

    def test_converts_grayscale_to_rgb(self):
        img = Image.new("L", (5, 5), color=200)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = load_image(buf.getvalue())
        assert result.shape == (5, 5, 3)
        assert result[0, 0, 0] == 200

    def test_converts_rgba_to_rgb(self):
        data = self._make_image_bytes(mode="RGBA", color=(100, 150, 200, 255), fmt="PNG")
        result = load_image(data)
        assert result.shape == (10, 10, 3)
        assert result[0, 0, 0] == 100
        assert result[0, 0, 1] == 150
        assert result[0, 0, 2] == 200

    def test_raises_valueerror_for_corrupt_data(self):
        with pytest.raises(ValueError, match="Unable to load image"):
            load_image(b"not an image at all")

    def test_raises_valueerror_for_empty_bytes(self):
        with pytest.raises(ValueError, match="Unable to load image"):
            load_image(b"")

    def test_raises_valueerror_for_truncated_data(self):
        data = self._make_image_bytes()
        with pytest.raises(ValueError, match="Unable to load image"):
            load_image(data[:10])


# --- Property-Based Tests (Hypothesis) ---

from hypothesis import given, settings, assume
from hypothesis import strategies as st


class TestFileExtensionValidationProperty:
    """Feature: lithophane-generator, Property 1: File Extension Validation

    Validates: Requirements 1.1

    For any filename string, validate_file_extension returns True if and only if
    the file extension (case-insensitive) is one of .jpg, .jpeg, or .png.
    """

    VALID_EXTENSIONS = [".jpg", ".jpeg", ".png"]

    @settings(max_examples=100)
    @given(
        basename=st.text(
            alphabet=st.characters(
                blacklist_categories=("Cs",),
                blacklist_characters="./\\",
            ),
            min_size=1,
            max_size=50,
        ),
        ext=st.sampled_from([".jpg", ".jpeg", ".png"]),
        upper=st.booleans(),
    )
    def test_accepts_valid_extensions(self, basename, ext, upper):
        """Any filename ending with .jpg/.jpeg/.png (any case) should be accepted."""
        extension = ext.upper() if upper else ext
        filename = basename + extension
        assert validate_file_extension(filename) is True

    @settings(max_examples=100)
    @given(
        basename=st.text(min_size=0, max_size=50),
        ext=st.text(min_size=0, max_size=10),
    )
    def test_rejects_invalid_extensions(self, basename, ext):
        """Any filename whose extension is NOT .jpg/.jpeg/.png should be rejected."""
        # Construct a filename with a dot + extension
        if ext:
            filename = basename + "." + ext
        else:
            filename = basename
        # Only check filenames where the resulting extension is NOT a valid one
        import os
        _, actual_ext = os.path.splitext(filename)
        assume(actual_ext.lower() not in {".jpg", ".jpeg", ".png"})
        assert validate_file_extension(filename) is False

    @settings(max_examples=100)
    @given(filename=st.text(min_size=0, max_size=100))
    def test_returns_true_iff_valid_extension(self, filename):
        """For any arbitrary string, validate_file_extension returns True iff
        the extension (case-insensitive) is .jpg, .jpeg, or .png."""
        import os
        _, ext = os.path.splitext(filename)
        expected = ext.lower() in {".jpg", ".jpeg", ".png"}
        assert validate_file_extension(filename) is expected


from image_processing import resize_image


class TestAspectRatioPreservationProperty:
    """Feature: lithophane-generator, Property 3: Aspect Ratio Preservation

    Validates: Requirements 3.1, 3.2

    For any image with dimensions (H, W) and target dimensions (target_width_mm,
    target_height_mm) with pixels_per_mm > 0:
    - The resized image's aspect ratio (width/height) should equal original (W/H)
      within floating-point tolerance
    - The resized pixel dimensions should fit within the target pixel bounds
    """

    @settings(max_examples=100)
    @given(
        img_h=st.integers(min_value=2, max_value=200),
        img_w=st.integers(min_value=2, max_value=200),
        target_width_mm=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        target_height_mm=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        pixels_per_mm=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    def test_aspect_ratio_preserved(self, img_h, img_w, target_width_mm, target_height_mm, pixels_per_mm):
        """The resized image aspect ratio should match the original within tolerance."""
        # Create a random image with the given dimensions
        image = np.random.randint(0, 256, size=(img_h, img_w, 3), dtype=np.uint8)

        resized = resize_image(image, target_width_mm, target_height_mm, pixels_per_mm)
        resized_h, resized_w = resized.shape[:2]

        # Skip degenerate cases where rounding collapses a dimension to 1 pixel
        assume(resized_h > 1 and resized_w > 1)

        original_aspect = img_w / img_h
        resized_aspect = resized_w / resized_h

        # Allow tolerance for rounding effects: the smaller the image, the larger
        # the relative rounding error. Use a tolerance proportional to 1/min_dim.
        min_dim = min(resized_h, resized_w)
        tolerance = max(0.05, 1.5 / min_dim)
        assert abs(resized_aspect - original_aspect) / original_aspect < tolerance, (
            f"Aspect ratio not preserved: original={original_aspect:.4f}, "
            f"resized={resized_aspect:.4f}, tolerance={tolerance:.4f}"
        )

    @settings(max_examples=100)
    @given(
        img_h=st.integers(min_value=2, max_value=200),
        img_w=st.integers(min_value=2, max_value=200),
        target_width_mm=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        target_height_mm=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        pixels_per_mm=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    def test_resized_fits_within_target_bounds(self, img_h, img_w, target_width_mm, target_height_mm, pixels_per_mm):
        """The resized pixel dimensions should fit within the target pixel bounds."""
        image = np.random.randint(0, 256, size=(img_h, img_w, 3), dtype=np.uint8)

        resized = resize_image(image, target_width_mm, target_height_mm, pixels_per_mm)
        resized_h, resized_w = resized.shape[:2]

        target_w_px = round(target_width_mm * pixels_per_mm)
        target_h_px = round(target_height_mm * pixels_per_mm)

        # Resized dimensions should not exceed target pixel bounds (allow +1 for rounding)
        assert resized_w <= target_w_px + 1, (
            f"Resized width {resized_w} exceeds target {target_w_px}"
        )
        assert resized_h <= target_h_px + 1, (
            f"Resized height {resized_h} exceeds target {target_h_px}"
        )


class TestPixelResolutionMappingProperty:
    """Feature: lithophane-generator, Property 4: Pixel Resolution Mapping

    Validates: Requirements 3.1, 3.2

    The resized image's pixel dimensions should match round(dimension_mm * pixels_per_mm)
    for the fitted dimension. The invariant: physical_mm x pixels_per_mm = pixel_count.
    """

    @settings(max_examples=100)
    @given(
        img_h=st.integers(min_value=2, max_value=200),
        img_w=st.integers(min_value=2, max_value=200),
        target_width_mm=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        target_height_mm=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        pixels_per_mm=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    def test_pixel_resolution_matches_formula(self, img_h, img_w, target_width_mm, target_height_mm, pixels_per_mm):
        """The fitted dimension's pixel count should equal round(dimension_mm * pixels_per_mm)
        scaled by the constraining axis."""
        image = np.random.randint(0, 256, size=(img_h, img_w, 3), dtype=np.uint8)

        resized = resize_image(image, target_width_mm, target_height_mm, pixels_per_mm)
        resized_h, resized_w = resized.shape[:2]

        # Compute target pixel bounds
        target_w_px = round(target_width_mm * pixels_per_mm)
        target_h_px = round(target_height_mm * pixels_per_mm)

        # Determine which dimension constrains the scaling
        scale_w = target_w_px / img_w
        scale_h = target_h_px / img_h
        scale = min(scale_w, scale_h)

        # Expected pixel dimensions based on the formula
        expected_w = max(1, round(img_w * scale))
        expected_h = max(1, round(img_h * scale))

        # The resized image should match the expected formula-based dimensions
        assert resized_w == expected_w, (
            f"Width mismatch: got {resized_w}, expected {expected_w} "
            f"(scale={scale:.4f}, img_w={img_w})"
        )
        assert resized_h == expected_h, (
            f"Height mismatch: got {resized_h}, expected {expected_h} "
            f"(scale={scale:.4f}, img_h={img_h})"
        )

    @settings(max_examples=100)
    @given(
        target_width_mm=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        target_height_mm=st.floats(min_value=10.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        pixels_per_mm=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    def test_pixel_count_invariant(self, target_width_mm, target_height_mm, pixels_per_mm):
        """For a square image that exactly fills the target, one dimension should
        satisfy physical_mm * pixels_per_mm ≈ pixel_count."""
        # Use a square image so the constraining dimension is the smaller target
        img_size = 50
        image = np.random.randint(0, 256, size=(img_size, img_size, 3), dtype=np.uint8)

        resized = resize_image(image, target_width_mm, target_height_mm, pixels_per_mm)
        resized_h, resized_w = resized.shape[:2]

        # For a square source image, the constraining dimension is the smaller target
        target_w_px = round(target_width_mm * pixels_per_mm)
        target_h_px = round(target_height_mm * pixels_per_mm)

        # The constraining dimension should match exactly
        constraining_px = min(target_w_px, target_h_px)

        # For a square image, both output dimensions should equal the constraining pixel count
        assert resized_w == max(1, constraining_px), (
            f"Square image width {resized_w} != constraining {constraining_px}"
        )
        assert resized_h == max(1, constraining_px), (
            f"Square image height {resized_h} != constraining {constraining_px}"
        )


from image_processing import convert_to_grayscale, compute_thickness_map


class TestGrayscaleLuminanceCorrectnessProperty:
    """Feature: lithophane-generator, Property 5: Grayscale Luminance Correctness

    Validates: Requirements 3.3

    For any RGB pixel value (R, G, B) where each channel is in [0, 255], the grayscale
    conversion shall produce a value equal to round(0.2989*R + 0.5870*G + 0.1140*B),
    ensuring the output is a single-channel 2D array with values in [0, 255].
    """

    @settings(max_examples=100)
    @given(
        r=st.integers(min_value=0, max_value=255),
        g=st.integers(min_value=0, max_value=255),
        b=st.integers(min_value=0, max_value=255),
    )
    def test_luminance_formula_correctness(self, r, g, b):
        """For any RGB pixel, grayscale value equals round(0.2989*R + 0.5870*G + 0.1140*B)."""
        # Create a 1x1 RGB image with the given pixel
        image = np.array([[[r, g, b]]], dtype=np.uint8)

        result = convert_to_grayscale(image)

        # Verify output shape and type
        assert result.shape == (1, 1)
        assert result.dtype == np.uint8

        # Verify luminance formula
        expected = round(0.2989 * r + 0.5870 * g + 0.1140 * b)
        assert result[0, 0] == expected, (
            f"Grayscale mismatch for RGB=({r},{g},{b}): "
            f"got {result[0, 0]}, expected {expected}"
        )

    @settings(max_examples=100)
    @given(
        h=st.integers(min_value=1, max_value=20),
        w=st.integers(min_value=1, max_value=20),
    )
    def test_output_is_2d_with_valid_range(self, h, w):
        """The output is a 2D array with values in [0, 255]."""
        image = np.random.randint(0, 256, size=(h, w, 3), dtype=np.uint8)

        result = convert_to_grayscale(image)

        # Output should be 2D with same H, W
        assert result.ndim == 2
        assert result.shape == (h, w)
        assert result.dtype == np.uint8
        # All values should be in [0, 255]
        assert np.all(result >= 0)
        assert np.all(result <= 255)


class TestThicknessMappingLinearityProperty:
    """Feature: lithophane-generator, Property 6: Thickness Mapping Linearity

    Validates: Requirements 3.4, 3.5

    For any grayscale intensity i in [0, 255]:
      thickness = 2.0 - (i/255) * 1.6
    Results strictly within [0.4, 2.0].
    Monotonically decreasing: for i1 < i2, thickness(i1) >= thickness(i2).
    """

    @settings(max_examples=100)
    @given(intensity=st.integers(min_value=0, max_value=255))
    def test_thickness_formula_correctness(self, intensity):
        """For any intensity in [0, 255], thickness equals 2.0 - (i/255)*1.6."""
        grayscale = np.array([[intensity]], dtype=np.uint8)

        result = compute_thickness_map(grayscale, min_thickness=0.4, max_thickness=2.0)

        assert result.shape == (1, 1)
        assert result.dtype == np.float64

        expected = 2.0 - (intensity / 255.0) * 1.6
        assert abs(result[0, 0] - expected) < 1e-10, (
            f"Thickness mismatch for intensity={intensity}: "
            f"got {result[0, 0]}, expected {expected}"
        )

    @settings(max_examples=100)
    @given(intensity=st.integers(min_value=0, max_value=255))
    def test_thickness_within_bounds(self, intensity):
        """For any intensity, thickness is strictly within [0.4, 2.0]."""
        grayscale = np.array([[intensity]], dtype=np.uint8)

        result = compute_thickness_map(grayscale, min_thickness=0.4, max_thickness=2.0)

        assert result[0, 0] >= 0.4 - 1e-10, (
            f"Thickness {result[0, 0]} below min 0.4 for intensity={intensity}"
        )
        assert result[0, 0] <= 2.0 + 1e-10, (
            f"Thickness {result[0, 0]} above max 2.0 for intensity={intensity}"
        )

    @settings(max_examples=100)
    @given(
        i1=st.integers(min_value=0, max_value=254),
        delta=st.integers(min_value=1, max_value=255),
    )
    def test_monotonically_decreasing(self, i1, delta):
        """For i1 < i2, thickness(i1) >= thickness(i2) — monotonically decreasing."""
        i2 = min(i1 + delta, 255)
        assume(i1 < i2)

        grayscale = np.array([[i1, i2]], dtype=np.uint8)
        result = compute_thickness_map(grayscale, min_thickness=0.4, max_thickness=2.0)

        thickness_i1 = result[0, 0]
        thickness_i2 = result[0, 1]

        assert thickness_i1 >= thickness_i2, (
            f"Not monotonically decreasing: thickness({i1})={thickness_i1} < "
            f"thickness({i2})={thickness_i2}"
        )


class TestInvalidInputErrorHandlingProperty:
    """Feature: lithophane-generator, Property 7: Invalid Input Error Handling

    Validates: Requirements 3.6

    For any input array that contains NaN values, infinite values, or has incorrect
    shape (not 2D), compute_thickness_map shall raise ValueError.
    """

    @settings(max_examples=100)
    @given(
        h=st.integers(min_value=1, max_value=10),
        w=st.integers(min_value=1, max_value=10),
        nan_row=st.integers(min_value=0, max_value=9),
        nan_col=st.integers(min_value=0, max_value=9),
    )
    def test_raises_for_nan_values(self, h, w, nan_row, nan_col):
        """Arrays containing NaN values should raise ValueError."""
        nan_row = nan_row % h
        nan_col = nan_col % w

        grayscale = np.zeros((h, w), dtype=np.float64)
        grayscale[nan_row, nan_col] = np.nan

        with pytest.raises(ValueError, match="NaN"):
            compute_thickness_map(grayscale)

    @settings(max_examples=100)
    @given(
        h=st.integers(min_value=1, max_value=10),
        w=st.integers(min_value=1, max_value=10),
        inf_row=st.integers(min_value=0, max_value=9),
        inf_col=st.integers(min_value=0, max_value=9),
        sign=st.sampled_from([1, -1]),
    )
    def test_raises_for_inf_values(self, h, w, inf_row, inf_col, sign):
        """Arrays containing Inf (positive or negative) should raise ValueError."""
        inf_row = inf_row % h
        inf_col = inf_col % w

        grayscale = np.zeros((h, w), dtype=np.float64)
        grayscale[inf_row, inf_col] = sign * np.inf

        with pytest.raises(ValueError, match="Inf"):
            compute_thickness_map(grayscale)

    @settings(max_examples=100)
    @given(length=st.integers(min_value=1, max_value=50))
    def test_raises_for_1d_array(self, length):
        """1D arrays should raise ValueError (not 2D)."""
        grayscale = np.zeros(length, dtype=np.uint8)

        with pytest.raises(ValueError, match="2D"):
            compute_thickness_map(grayscale)

    @settings(max_examples=100)
    @given(
        d1=st.integers(min_value=1, max_value=10),
        d2=st.integers(min_value=1, max_value=10),
        d3=st.integers(min_value=1, max_value=10),
    )
    def test_raises_for_3d_array(self, d1, d2, d3):
        """3D arrays should raise ValueError (not 2D)."""
        grayscale = np.zeros((d1, d2, d3), dtype=np.uint8)

        with pytest.raises(ValueError, match="2D"):
            compute_thickness_map(grayscale)
