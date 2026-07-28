# Lithophane Generator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://lithophane.streamlit.app/)

A Streamlit web application that converts 2D images into 3D-printable lithophane STL files. A lithophane varies material thickness so that when backlit, thinner areas appear brighter and thicker areas appear darker, recreating the original image in light and shadow.

**Live App:** https://lithophane.streamlit.app/

**Built with [AWS Kiro](https://kiro.dev) using Spec-Driven Development** — requirements, design, and implementation tasks were systematically generated and executed through Kiro's structured spec workflow.

## Features

- Upload .jpg, .jpeg, or .png images
- Configure target physical dimensions (default 100mm × 100mm)
- Adjustable mesh resolution (1–10 pixels/mm) for detail control
- Contrast enhancement (Histogram Stretch or Histogram Equalization)
- Automatic grayscale conversion and thickness mapping
- Watertight STL mesh generation (binary or ASCII format)
- Interactive side-by-side 3D preview with rotate, zoom, and pan
- One-click STL download with auto-generated filename

## Resolution (Pixels/mm)

The resolution slider controls how many mesh vertices represent each millimeter of the physical print. Higher values capture finer detail but produce larger STL files.

| Resolution | Grid size (100mm print) | Detail | STL size | Best for |
|---|---|---|---|---|
| 1 px/mm | 100×100 | Low | ~200 KB | Simple graphics, icons |
| 3 px/mm | 300×300 | Good | ~2 MB | FDM printers, photos |
| 5 px/mm | 500×500 | High | ~5 MB | Resin printers, fine detail |
| 10 px/mm | 1000×1000 | Maximum | ~20 MB | Overkill for most cases |

**Recommended:** 3 pixels/mm matches the physical capability of a standard 0.4mm FDM nozzle. Going higher than 5 won't improve the printed result on FDM — the printer can't reproduce sub-nozzle detail. Use 5+ only for resin printers.

## Contrast Enhancement

Contrast enhancement improves the tonal range of the image before it's mapped to thickness, resulting in sharper and more visually distinct lithophanes when backlit.

**Histogram Stretch** (recommended for most cases):
- Maps the image's actual darkest pixel to full 2.0mm thickness and lightest to 0.4mm
- Preserves the relative tonal relationships — gradients stay smooth and proportional
- Best for photos, portraits, and landscapes where subtle tonal transitions create depth

**Histogram Equalization:**
- Redistributes intensity values to be more uniform across the full 0–255 range
- Maximizes overall contrast but can flatten subtle gradients (like skin tones)
- May exaggerate noise in uniform areas and create a harsher look when backlit
- Better suited for images with very narrow dynamic range or high-contrast graphic artwork

**None:**
- Uses raw image intensity as-is with no enhancement
- Use when the source image already has optimal contrast

## Prerequisites

- [Anaconda](https://www.anaconda.com/download) installed on your system
- Python 3.9+

## Setup

1. Create and activate the Anaconda environment:

```bash
conda create -n project python=3.10
conda activate project
```

2. Clone or download this repository:

```bash
cd path/to/lithophane
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure secrets (if needed):

```bash
cp .env.example .env
```

Store any API keys or secrets in the `.env` file. This file is git-ignored and should never be committed.

## Usage

Run the application:

```bash
streamlit run app.py
```

This will open the Lithophane Generator in your default browser. From there:

1. Upload an image (.jpg, .jpeg, or .png)
2. Set target print dimensions in millimeters (default 100mm × 100mm)
3. Choose STL export format (binary or ASCII)
4. View the side-by-side comparison of your original image and the 3D lithophane preview
5. Download the generated STL file for 3D printing

## Project Structure

```
lithophane/
├── app.py                  # Streamlit UI orchestration and main entry point
├── image_processing.py     # Image resize, grayscale conversion, thickness mapping
├── stl_generation.py       # Mesh vertex/face generation, STL file creation
├── preview.py              # 3D preview rendering via streamlit-stl
├── utils.py                # Shutdown logic, filename helpers, validation
├── requirements.txt        # Python pip dependencies
├── .env                    # Secrets and API keys (git-ignored)
├── .gitignore              # Git ignore rules
├── README.md               # This file
└── tests/
    ├── __init__.py
    ├── conftest.py         # Shared test fixtures
    ├── test_image_processing.py
    ├── test_stl_generation.py
    └── test_utils.py
```

## Architecture

The application follows a strictly functional programming style with no classes. All modules expose pure functions, and state flows through function arguments and return values.

| Module | Responsibility |
|--------|----------------|
| `app.py` | Streamlit UI orchestration, layout, session state |
| `image_processing.py` | Image resize, grayscale conversion, thickness mapping |
| `stl_generation.py` | Mesh vertex/face generation, STL file creation |
| `preview.py` | 3D preview rendering via streamlit-stl |
| `utils.py` | Shutdown logic, filename helpers, validation |

## Key Technologies

- **Streamlit** — UI framework
- **Pillow (PIL)** — Image loading, resizing, grayscale conversion
- **NumPy** — Array operations for thickness mapping and vertex generation
- **numpy-stl** — STL mesh creation and file export
- **streamlit-stl** — Interactive 3D STL viewer

## Testing

Install development dependencies first:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov
```

Tests include unit tests for specific scenarios and property-based tests using Hypothesis for universal correctness validation.

## Cloud Deployment (Streamlit Community Cloud)

This app is deployed at https://lithophane.streamlit.app/

To deploy your own instance:

1. Fork this repository on GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click "New app" and select the forked repository
4. Set the main file path to `app.py`
5. Deploy

The `requirements.txt` contains only production dependencies needed for cloud deployment.

## License

This project is for personal/educational use.
