# Implementation Plan: Lithophane Generator

## Overview

This plan implements a Streamlit web application that converts 2D images into 3D lithophane STL files. The implementation follows a functional programming style (no classes), uses Pillow for image processing, NumPy for array operations, numpy-stl for mesh generation, and streamlit-stl for interactive 3D preview. Tasks are organized to build the pipeline incrementally: project setup → image processing → STL generation → preview → UI orchestration → shutdown → testing.

## Tasks

- [x] 1. Set up project structure and dependencies
  - [x] 1.1 Create project files and directory structure
    - Create `requirements.txt` with dependencies: streamlit, Pillow, numpy, numpy-stl, streamlit-stl, psutil, keyboard, python-dotenv, pytest, hypothesis, pytest-cov
    - Create `.env` file (empty placeholder for secrets)
    - Create `.gitignore` with `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`
    - Create empty module files: `app.py`, `image_processing.py`, `stl_generation.py`, `preview.py`, `utils.py`
    - Create `tests/` directory with `__init__.py`, `test_image_processing.py`, `test_stl_generation.py`, `test_utils.py`, `conftest.py`
    - _Requirements: 8.2, 8.3, 8.1_

  - [x] 1.2 Create README.md with project documentation
    - Document application purpose, setup instructions (Anaconda 'project' environment), installation steps (`pip install -r requirements.txt`), usage instructions (`streamlit run app.py`), and project structure
    - _Requirements: 8.4_

- [x] 2. Implement image processing pipeline
  - [x] 2.1 Implement file validation and image loading functions
    - In `image_processing.py`, implement `validate_file_extension(filename)` that checks for .jpg, .jpeg, .png extensions (case-insensitive)
    - Implement `load_image(file_bytes)` that uses Pillow to open image bytes and returns an RGB numpy array
    - Include error handling for corrupt/unreadable images (raise ValueError)
    - _Requirements: 1.1, 1.2_

  - [x] 2.2 Write property test for file extension validation
    - **Property 1: File Extension Validation**
    - **Validates: Requirements 1.1**
    - Use Hypothesis to generate arbitrary filename strings and verify `validate_file_extension` returns True only for .jpg/.jpeg/.png extensions (case-insensitive)

  - [x] 2.3 Implement image resize with aspect ratio preservation
    - In `image_processing.py`, implement `resize_image(image, target_width_mm, target_height_mm, pixels_per_mm=1.0)` that resizes to fit target dimensions while preserving aspect ratio
    - Calculate pixel dimensions as `round(dimension_mm * pixels_per_mm)` for the fitted dimension
    - Use Pillow's resize with LANCZOS resampling
    - _Requirements: 3.1, 3.2_

  - [x] 2.4 Write property tests for aspect ratio and pixel resolution
    - **Property 3: Aspect Ratio Preservation**
    - **Property 4: Pixel Resolution Mapping**
    - **Validates: Requirements 3.1, 3.2**
    - Use Hypothesis to generate random image dimensions and target sizes, verify aspect ratio is preserved within tolerance and pixel dimensions match the formula

  - [x] 2.5 Implement grayscale conversion and thickness mapping
    - In `image_processing.py`, implement `convert_to_grayscale(image)` using luminance weights (0.2989*R + 0.5870*G + 0.1140*B)
    - Implement `compute_thickness_map(grayscale, min_thickness=0.4, max_thickness=2.0)` with formula: `max_thickness - (intensity / 255) * (max_thickness - min_thickness)`
    - Add input validation: raise ValueError for NaN, Inf, or non-2D arrays
    - _Requirements: 3.3, 3.4, 3.5, 3.6_

  - [x] 2.6 Write property tests for grayscale and thickness mapping
    - **Property 5: Grayscale Luminance Correctness**
    - **Property 6: Thickness Mapping Linearity**
    - **Property 7: Invalid Input Error Handling**
    - **Validates: Requirements 3.3, 3.4, 3.5, 3.6**
    - Use Hypothesis to verify luminance formula correctness, monotonically decreasing thickness, bounds [0.4, 2.0], and error raising for invalid inputs

- [x] 3. Checkpoint - Image processing validation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement STL mesh generation
  - [x] 4.1 Implement vertex generation from thickness map
    - In `stl_generation.py`, implement `generate_vertices(thickness_map, width_mm, height_mm)` that creates top surface vertices at (x, y, thickness) and bottom surface vertices at (x, y, 0)
    - X coordinates linearly spaced across width_mm, Y across height_mm
    - Return shape (2 * rows * cols, 3) array
    - _Requirements: 4.2, 4.3_

  - [x] 4.2 Implement face generation for watertight mesh
    - In `stl_generation.py`, implement `generate_top_faces(rows, cols)`, `generate_bottom_faces(rows, cols, vertex_offset)`, and `generate_side_faces(rows, cols, vertex_offset)`
    - Top/bottom: 2 triangles per grid cell = 2*(rows-1)*(cols-1) faces each
    - Sides: connect perimeter edges between top and bottom surfaces
    - _Requirements: 4.1, 4.4_

  - [x] 4.3 Implement mesh assembly and STL export
    - In `stl_generation.py`, implement `create_stl_mesh(thickness_map, width_mm, height_mm)` that combines all vertices and faces into a numpy-stl Mesh object
    - Implement `export_stl(stl_mesh, binary=True)` that serializes to bytes (binary or ASCII format)
    - _Requirements: 4.1, 4.5_

  - [x] 4.4 Write property tests for mesh correctness
    - **Property 8: Mesh Watertightness**
    - **Property 9: Vertex Height Correctness**
    - **Property 10: STL Export Round-Trip**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    - Use Hypothesis to generate small thickness maps (2×2 to 10×10), verify manifold condition (every edge shared by exactly 2 triangles), vertex Z values match thickness map, and binary export/import round-trip equivalence

- [x] 5. Checkpoint - STL generation validation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement utilities and preview
  - [x] 6.1 Implement utility functions
    - In `utils.py`, implement `generate_output_filename(original_filename)` that strips extension, appends `_lithophane.stl`
    - Implement `validate_dimensions(width, height)` returning `(bool, str)` tuple — reject zero, negative, NaN, Inf
    - Implement `shutdown_app()` using keyboard simulation (ctrl+w) and psutil process termination with os._exit(0) fallback
    - _Requirements: 6.3, 2.3, 7.2, 7.3_

  - [x] 6.2 Write property tests for utilities
    - **Property 2: Dimension Validation**
    - **Property 11: Filename Derivation**
    - **Validates: Requirements 2.3, 6.3**
    - Use Hypothesis to generate numeric values for dimension validation and filenames for derivation testing

  - [x] 6.3 Implement 3D preview rendering
    - In `preview.py`, implement `render_stl_preview(stl_bytes, height=400)` using streamlit-stl component
    - Handle render failures gracefully: catch exceptions, show fallback message instead of crashing
    - _Requirements: 5.2, 5.3, 5.4_

- [x] 7. Implement Streamlit UI orchestration
  - [x] 7.1 Implement main app layout and upload section
    - In `app.py`, implement `main()` entry point with `st.set_page_config()` and page title
    - Implement `render_upload_section()` with `st.file_uploader` accepting .jpg, .jpeg, .png
    - Implement `render_dimension_controls()` with `st.number_input` for width/height (default 100mm each)
    - Implement `render_format_selector()` with `st.radio` for binary/ASCII STL format
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

  - [x] 7.2 Implement processing pipeline and results display
    - In `app.py`, implement `render_results(original_image, stl_bytes, filename)` with side-by-side columns showing original image and 3D preview
    - Wire the full pipeline: upload → validate → load → resize → grayscale → thickness → mesh → export
    - Add `st.download_button` with derived filename for STL download
    - Add error handling with `st.error()` for each pipeline stage
    - _Requirements: 1.3, 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 6.1, 6.2, 6.3_

  - [x] 7.3 Implement shutdown button
    - In `app.py`, implement `render_shutdown_button()` that calls `shutdown_app()` from utils
    - Place in sidebar or at bottom of page
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 8. Final checkpoint - Full application validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document using Hypothesis
- Unit tests validate specific examples and edge cases
- All code uses functional programming style — no classes
- The Anaconda 'project' environment should be activated before running `pip install -r requirements.txt`
- Run the app with `streamlit run app.py`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "6.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "6.2", "6.3"] },
    { "id": 3, "tasks": ["2.4", "2.5"] },
    { "id": 4, "tasks": ["2.6", "4.1"] },
    { "id": 5, "tasks": ["4.2"] },
    { "id": 6, "tasks": ["4.3"] },
    { "id": 7, "tasks": ["4.4"] },
    { "id": 8, "tasks": ["7.1"] },
    { "id": 9, "tasks": ["7.2"] },
    { "id": 10, "tasks": ["7.3"] }
  ]
}
```
