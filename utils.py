# Lithophane Generator - Utilities Module
# Shutdown logic, filename helpers, validation (functional style, no classes)

import os
import math
from typing import Tuple


def generate_output_filename(original_filename: str) -> str:
    """Derive output filename: strip extension, append _lithophane.stl.

    Args:
        original_filename: The original uploaded image filename.

    Returns:
        Output filename with _lithophane.stl suffix.
        e.g., "photo.jpg" -> "photo_lithophane.stl"
    """
    base, _ = os.path.splitext(original_filename)
    return f"{base}_lithophane.stl"


def validate_dimensions(width: float, height: float) -> Tuple[bool, str]:
    """Validate dimension inputs are positive finite numbers.

    Args:
        width: Target width in mm.
        height: Target height in mm.

    Returns:
        Tuple of (is_valid, error_message).
        (True, "") if valid, (False, "error description") if invalid.
    """
    # Check for NaN
    if math.isnan(width) or math.isnan(height):
        return (False, "Dimensions must be valid numbers (NaN not allowed)")

    # Check for Infinity
    if math.isinf(width) or math.isinf(height):
        return (False, "Dimensions must be finite numbers (Infinity not allowed)")

    # Check for zero or negative
    if width <= 0 or height <= 0:
        return (False, "Dimensions must be positive numbers greater than zero")

    return (True, "")


def shutdown_app() -> None:
    """Gracefully terminate the Streamlit application.

    In local mode: uses keyboard simulation (ctrl+w) to close the browser tab,
    then psutil process termination. Falls back to os._exit(0).
    In cloud mode: gracefully stops the Streamlit script with st.stop().
    """
    import time
    import streamlit as st

    st.warning("Shutting down...")
    time.sleep(0.5)
    try:
        import keyboard
        import psutil
        keyboard.press_and_release("ctrl+w")
        pid = os.getpid()
        p = psutil.Process(pid)
        p.terminate()
    except (ImportError, Exception):
        # Cloud environment: keyboard/psutil unavailable or failed
        st.stop()
