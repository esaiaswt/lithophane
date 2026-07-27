# Tests for utils module
# Property-based tests using Hypothesis

import math
import os
import sys

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import validate_dimensions, generate_output_filename


# =============================================================================
# Property 2: Dimension Validation
# Feature: lithophane-generator, Property 2: Dimension Validation
# Validates: Requirements 2.3
# =============================================================================


@settings(max_examples=100)
@given(
    width=st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
    height=st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
)
def test_dimension_validation_accepts_positive_finite(width, height):
    """
    **Validates: Requirements 2.3**
    For any positive finite numbers, validate_dimensions SHALL accept them.
    """
    is_valid, msg = validate_dimensions(width, height)
    assert is_valid is True
    assert msg == ""


@settings(max_examples=100)
@given(
    width=st.floats(min_value=-1e10, max_value=0.0, allow_nan=False, allow_infinity=False),
    height=st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
)
def test_dimension_validation_rejects_non_positive_width(width, height):
    """
    **Validates: Requirements 2.3**
    For any zero or negative width, validate_dimensions SHALL reject.
    """
    is_valid, msg = validate_dimensions(width, height)
    assert is_valid is False
    assert len(msg) > 0


@settings(max_examples=100)
@given(
    width=st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
    height=st.floats(min_value=-1e10, max_value=0.0, allow_nan=False, allow_infinity=False),
)
def test_dimension_validation_rejects_non_positive_height(width, height):
    """
    **Validates: Requirements 2.3**
    For any zero or negative height, validate_dimensions SHALL reject.
    """
    is_valid, msg = validate_dimensions(width, height)
    assert is_valid is False
    assert len(msg) > 0


@settings(max_examples=100)
@given(
    height=st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
)
def test_dimension_validation_rejects_nan_width(height):
    """
    **Validates: Requirements 2.3**
    NaN width SHALL be rejected.
    """
    is_valid, msg = validate_dimensions(float("nan"), height)
    assert is_valid is False
    assert len(msg) > 0


@settings(max_examples=100)
@given(
    width=st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
)
def test_dimension_validation_rejects_nan_height(width):
    """
    **Validates: Requirements 2.3**
    NaN height SHALL be rejected.
    """
    is_valid, msg = validate_dimensions(width, float("nan"))
    assert is_valid is False
    assert len(msg) > 0


@settings(max_examples=100)
@given(
    width=st.sampled_from([float("inf"), float("-inf")]),
    height=st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
)
def test_dimension_validation_rejects_infinite_width(width, height):
    """
    **Validates: Requirements 2.3**
    Infinite width SHALL be rejected.
    """
    is_valid, msg = validate_dimensions(width, height)
    assert is_valid is False
    assert len(msg) > 0


@settings(max_examples=100)
@given(
    width=st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False),
    height=st.sampled_from([float("inf"), float("-inf")]),
)
def test_dimension_validation_rejects_infinite_height(width, height):
    """
    **Validates: Requirements 2.3**
    Infinite height SHALL be rejected.
    """
    is_valid, msg = validate_dimensions(width, height)
    assert is_valid is False
    assert len(msg) > 0


# =============================================================================
# Property 11: Filename Derivation
# Feature: lithophane-generator, Property 11: Filename Derivation
# Validates: Requirements 6.3
# =============================================================================

# Strategy to generate valid base filenames (no extension)
_valid_base_chars = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"),  # Letters and numbers
        whitelist_characters="_- ",
    ),
    min_size=1,
    max_size=50,
)

# Recognized image extensions
_recognized_extensions = st.sampled_from([".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG", ".Jpg", ".Png"])


@settings(max_examples=100)
@given(
    base=_valid_base_chars,
    ext=_recognized_extensions,
)
def test_filename_derivation_strips_extension_appends_lithophane_stl(base, ext):
    """
    **Validates: Requirements 6.3**
    For any valid filename with a recognized extension, generate_output_filename
    SHALL produce original filename with extension stripped, _lithophane appended,
    and .stl as new extension.
    """
    original_filename = base + ext
    result = generate_output_filename(original_filename)
    expected = base + "_lithophane.stl"
    assert result == expected


@settings(max_examples=100)
@given(
    base=_valid_base_chars,
    ext=_recognized_extensions,
)
def test_filename_derivation_always_ends_with_stl(base, ext):
    """
    **Validates: Requirements 6.3**
    Output filename SHALL always end with .stl extension.
    """
    original_filename = base + ext
    result = generate_output_filename(original_filename)
    assert result.endswith(".stl")


@settings(max_examples=100)
@given(
    base=_valid_base_chars,
    ext=_recognized_extensions,
)
def test_filename_derivation_contains_lithophane_suffix(base, ext):
    """
    **Validates: Requirements 6.3**
    Output filename SHALL contain _lithophane before the .stl extension.
    """
    original_filename = base + ext
    result = generate_output_filename(original_filename)
    assert result.endswith("_lithophane.stl")
