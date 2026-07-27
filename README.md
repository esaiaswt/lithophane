# Lithophane Generator

A Streamlit web application that converts 2D images into 3D-printable lithophane STL files. A lithophane varies material thickness so that when backlit, thinner areas appear brighter and thicker areas appear darker, recreating the original image in light and shadow.

## Features

- Upload .jpg, .jpeg, or .png images
- Configure target physical dimensions (default 100mm × 100mm)
- Automatic grayscale conversion and thickness mapping
- Watertight STL mesh generation (binary or ASCII format)
- Interactive side-by-side 3D preview with rotate, zoom, and pan
- One-click STL download with auto-generated filename
- Graceful application shutdown button

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

To stop the application, click the "Shutdown App" button in the UI or press `Ctrl+C` in the terminal.

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
- **psutil + keyboard** — Graceful application shutdown
- **python-dotenv** — Environment variable management

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

This app is ready to deploy on [Streamlit Community Cloud](https://share.streamlit.io):

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click "New app" and select this repository
4. Set the main file path to `app.py`
5. Deploy

The `requirements.txt` contains only production dependencies. The shutdown button gracefully degrades in cloud environments (uses `st.stop()` instead of process termination).

**Note:** The `keyboard` and `psutil` libraries are optional — they enable local shutdown functionality but are not required for cloud deployment.

## License

This project is for personal/educational use.
