# Lithophane Generator - Main Streamlit Application
# UI orchestration module (functional style, no classes)

from typing import Optional, Tuple

import numpy as np
import streamlit as st
from PIL import Image

from image_processing import (
    validate_file_extension,
    load_image,
    resize_image,
    convert_to_grayscale,
    enhance_contrast,
    compute_thickness_map,
)
from stl_generation import create_stl_mesh, export_stl
from preview import render_stl_preview
from utils import generate_output_filename, validate_dimensions


def render_upload_section():
    """Render file uploader, return uploaded file or None."""
    uploaded_file = st.file_uploader(
        "Upload an image", type=["jpg", "jpeg", "png"]
    )
    return uploaded_file


def render_dimension_controls() -> Tuple[float, float]:
    """Render width/height inputs, return (width_mm, height_mm)."""
    col1, col2 = st.columns(2)
    with col1:
        width_mm = st.number_input(
            "Width (mm)", min_value=1.0, value=100.0, step=1.0
        )
    with col2:
        height_mm = st.number_input(
            "Height (mm)", min_value=1.0, value=100.0, step=1.0
        )
    return (width_mm, height_mm)


def render_resolution_slider() -> float:
    """Render resolution slider, return pixels_per_mm value."""
    pixels_per_mm = st.slider(
        "Resolution (pixels/mm)",
        min_value=1.0,
        max_value=10.0,
        value=3.0,
        step=0.5,
        help="Higher values produce sharper detail but larger STL files. "
             "3-5 recommended for photos with fine detail."
    )
    return pixels_per_mm


def render_contrast_selector() -> str:
    """Render contrast enhancement selector, return method name."""
    method = st.selectbox(
        "Contrast Enhancement",
        options=["None", "Histogram Stretch", "Histogram Equalization"],
        index=1,
        help="Enhances image contrast before thickness mapping. "
             "'Histogram Stretch' spreads pixel values to full 0-255 range. "
             "'Histogram Equalization' redistributes intensity for maximum contrast."
    )
    method_map = {
        "None": "none",
        "Histogram Stretch": "histogram_stretch",
        "Histogram Equalization": "clahe",
    }
    return method_map[method]


def render_format_selector() -> str:
    """Render STL format radio button, return 'binary' or 'ascii'."""
    choice = st.radio("STL Format", options=["Binary", "ASCII"])
    return choice.lower()


def render_mirror_checkbox() -> bool:
    """Render 'View from Smooth side' checkbox, return True if enabled."""
    view_smooth = st.checkbox(
        "View from Smooth side",
        value=True,
        help="When checked, the STL is mirrored so the image appears correct "
             "when viewing the lithophane from the smooth (flat) back side with "
             "backlighting. Uncheck to view from the textured front side."
    )
    return view_smooth


def render_results(original_image: np.ndarray, stl_bytes: bytes, filename: str) -> None:
    """Render side-by-side comparison of original image and 3D preview, plus download button.

    Args:
        original_image: RGB image as numpy array (H, W, 3) for display.
        stl_bytes: Serialized STL file bytes.
        filename: Derived output filename for download.
    """
    col_left, col_right = st.columns(2)
    with col_left:
        st.image(original_image, caption="Original Image")
    with col_right:
        render_stl_preview(stl_bytes)

    st.download_button(
        label=f"Download {filename}",
        data=stl_bytes,
        file_name=filename,
        mime="application/octet-stream",
    )


def main() -> None:
    """Entry point. Configures page, renders UI, orchestrates pipeline."""
    st.set_page_config(page_title="Lithophane Generator", layout="wide")
    st.title("Lithophane Generator")

    uploaded_file = render_upload_section()
    width_mm, height_mm = render_dimension_controls()
    pixels_per_mm = render_resolution_slider()
    contrast_method = render_contrast_selector()
    mirror_image = render_mirror_checkbox()
    stl_format = render_format_selector()

    if uploaded_file is not None:
        # Validate file extension
        if not validate_file_extension(uploaded_file.name):
            st.error("Invalid file type. Accepted formats: .jpg, .jpeg, .png")
            return

        # Validate dimensions
        valid, error_msg = validate_dimensions(width_mm, height_mm)
        if not valid:
            st.error(error_msg)
            return

        try:
            # Load image
            image = load_image(uploaded_file.getvalue())
        except ValueError as e:
            st.error(f"Failed to load image: {e}")
            return

        # Keep original for display (never flipped)
        display_image = image

        # Flip horizontally for STL when "View from Smooth side" is checked
        # so the image reads correctly when viewing the lithophane from the back
        process_image = np.fliplr(image).copy() if mirror_image else image

        try:
            # Resize image
            resized = resize_image(process_image, width_mm, height_mm, pixels_per_mm)
        except Exception as e:
            st.error(f"Failed to resize image: {e}")
            return

        try:
            # Convert to grayscale
            grayscale = convert_to_grayscale(resized)
        except Exception as e:
            st.error(f"Failed to convert image to grayscale: {e}")
            return

        try:
            # Enhance contrast
            enhanced = enhance_contrast(grayscale, method=contrast_method)
        except Exception as e:
            st.error(f"Failed to enhance contrast: {e}")
            return

        try:
            # Compute thickness map
            thickness_map = compute_thickness_map(enhanced)
        except ValueError as e:
            st.error(f"Failed to compute thickness map: {e}")
            return

        try:
            # Create STL mesh
            stl_mesh = create_stl_mesh(thickness_map, width_mm, height_mm)
        except Exception as e:
            st.error(f"Failed to generate STL mesh: {e}")
            return

        try:
            # Export STL
            stl_bytes = export_stl(stl_mesh, binary=(stl_format == "binary"))
        except Exception as e:
            st.error(f"Failed to export STL file: {e}")
            return

        # Generate output filename and render results
        filename = generate_output_filename(uploaded_file.name)
        render_results(display_image, stl_bytes, filename)


if __name__ == "__main__":
    main()
