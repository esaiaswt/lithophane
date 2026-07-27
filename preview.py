# Lithophane Generator - 3D Preview Module
# 3D preview rendering via streamlit-stl (functional style, no classes)

import streamlit as st
from streamlit_stl import stl_from_text


def render_stl_preview(stl_bytes: bytes, height: int = 400) -> None:
    """Render interactive 3D preview using streamlit-stl component.

    Displays the STL model with Three.js orbit controls supporting
    rotate, zoom, and pan interactions. If rendering fails for any
    reason, a fallback warning message is shown instead of crashing.

    Args:
        stl_bytes: The STL file content as bytes (binary or ASCII).
        height: Height of the 3D viewer frame in pixels (default 400).
    """
    try:
        stl_from_text(text=stl_bytes, height=height)
    except Exception:
        st.warning(
            "3D preview could not be rendered. "
            "You can still download the STL file and view it in an external application."
        )
