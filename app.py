# Lithophane Generator - Main Streamlit Application
# UI orchestration module (functional style, no classes)

from typing import Optional, Tuple

import numpy as np
import streamlit as st
from PIL import Image
from streamlit.runtime.uploaded_file_manager import UploadedFile

from image_processing import (
    validate_file_extension,
    load_image,
    resize_image,
    convert_to_grayscale,
    compute_thickness_map,
)
from stl_generation import create_stl_mesh, export_stl
from preview import render_stl_preview
from utils import generate_output_filename, validate_dimensions, shutdown_app


def render_upload_section() -> Optional[UploadedFile]:
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


def render_format_selector() -> str:
    """Render STL format radio button, return 'binary' or 'ascii'."""
    choice = st.radio("STL Format", options=["Binary", "ASCII"])
    return choice.lower()


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


def render_shutdown_button() -> None:
    """Render shutdown button in the sidebar. Calls shutdown_app() when clicked."""
    if st.sidebar.button("Shutdown App"):
        shutdown_app()


def main() -> None:
    """Entry point. Configures page, renders UI, orchestrates pipeline."""
    st.set_page_config(page_title="Lithophane Generator", layout="wide")
    st.title("Lithophane Generator")

    render_shutdown_button()

    uploaded_file = render_upload_section()
    width_mm, height_mm = render_dimension_controls()
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

        try:
            # Resize image
            resized = resize_image(image, width_mm, height_mm)
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
            # Compute thickness map
            thickness_map = compute_thickness_map(grayscale)
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
        render_results(image, stl_bytes, filename)


if __name__ == "__main__":
    main()
