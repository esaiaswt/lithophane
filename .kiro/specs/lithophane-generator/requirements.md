# Requirements Document

## Introduction

A web application that converts 2D images into 3D lithophane STL files suitable for 3D printing. The application uses Streamlit for the UI, processes uploaded images by mapping pixel intensity to physical thickness, generates a 3D mesh, and provides an interactive preview alongside the original image. The user can then download the resulting STL file.

## Glossary

- **Lithophane_Generator**: The Streamlit web application that orchestrates image upload, processing, STL generation, preview, and download.
- **Image_Processor**: The functional module responsible for resizing images proportionally, converting to grayscale, and mapping pixel intensity to a thickness map.
- **STL_Generator**: The functional module responsible for converting a thickness map into a valid 3D triangulated mesh in STL format.
- **Thickness_Map**: A 2D array where each value represents the physical thickness (in mm) at that pixel location, derived from grayscale intensity.
- **Base_Thickness**: The minimum thickness (0.4mm default) assigned to the lightest pixels (value 255), ensuring structural integrity of the printed lithophane.
- **Max_Thickness**: The maximum thickness (2.0mm) assigned to the darkest pixels (value 0).
- **Preview_Viewer**: A Streamlit-compatible 3D viewer component that renders an interactive preview of the generated STL mesh.

## Requirements

### Requirement 1: Image Upload

**User Story:** As a user, I want to upload an image file so that I can convert it into a lithophane.

#### Acceptance Criteria

1. WHEN a user uploads a file, THE Lithophane_Generator SHALL accept files with extensions .jpg, .jpeg, and .png only.
2. WHEN a user uploads a file with an unsupported format, THE Lithophane_Generator SHALL display an error message indicating the accepted formats.
3. WHEN a valid image is successfully accepted, THE Lithophane_Generator SHALL display the original image in the interface.

### Requirement 2: Dimension Controls

**User Story:** As a user, I want to define the target print size in millimeters so that the lithophane matches my desired physical dimensions.

#### Acceptance Criteria

1. THE Lithophane_Generator SHALL provide input fields for target length (width) and breadth (height) in millimeters.
2. WHEN no custom dimensions are provided, THE Lithophane_Generator SHALL use default values of 100mm for length and 100mm for breadth.
3. WHEN a user enters dimension values, THE Lithophane_Generator SHALL accept only positive numeric values greater than zero.

### Requirement 3: Image Processing

**User Story:** As a user, I want the application to process my image into a thickness map so that it accurately represents the lithophane relief.

#### Acceptance Criteria

1. WHEN a valid image is uploaded with target dimensions, THE Image_Processor SHALL resize the image proportionally to fit within the target length and breadth while maintaining the original aspect ratio.
2. WHEN resizing the image, THE Image_Processor SHALL determine pixel resolution by mapping millimeters to pixels such that the mesh density is appropriate for STL generation.
3. WHEN the image is resized, THE Image_Processor SHALL convert it to grayscale using standard luminance weighting.
4. WHEN mapping grayscale intensity to thickness, THE Image_Processor SHALL assign a thickness of 2.0mm to pixels with intensity value 0 (darkest) and a thickness of 0.4mm to pixels with intensity value 255 (lightest), using the full 0-255 range regardless of the actual intensity distribution in the image.
5. WHEN mapping grayscale intensity to thickness, THE Image_Processor SHALL linearly interpolate thickness values across the full range from 0.4mm (intensity 255) to 2.0mm (intensity 0) for all intermediate intensity values.
6. IF the thickness mapping process fails or produces incorrect values, THEN THE Image_Processor SHALL halt processing and display an error message to the user.

### Requirement 4: STL Mesh Generation

**User Story:** As a user, I want the application to generate a valid STL file from the thickness map so that I can 3D print the lithophane.

#### Acceptance Criteria

1. WHEN a thickness map is provided, THE STL_Generator SHALL produce a closed, watertight 3D mesh representing the lithophane surface.
2. WHEN generating the mesh, THE STL_Generator SHALL create a top surface where vertex heights correspond to the thickness values in the Thickness_Map.
3. WHEN generating the mesh, THE STL_Generator SHALL create a flat bottom surface at z=0.
4. WHEN generating the mesh, THE STL_Generator SHALL create four side walls connecting the top surface perimeter to the bottom surface.
5. WHEN the mesh is generated, THE STL_Generator SHALL output the result in binary STL format by default, with an option to export in ASCII STL format.

### Requirement 5: Side-by-Side Comparison

**User Story:** As a user, I want to see the original image and a 3D preview side by side so that I can visually compare the source with the resulting lithophane.

#### Acceptance Criteria

1. WHEN an STL mesh is generated, THE Lithophane_Generator SHALL display the original uploaded image and the interactive 3D preview in side-by-side Streamlit columns.
2. WHEN the 3D preview is displayed, THE Preview_Viewer SHALL allow the user to rotate, zoom, and pan the model interactively.
3. WHEN the 3D preview is displayed, THE Preview_Viewer SHALL render the mesh with lighting that highlights the lithophane surface relief.
4. IF the lighting effects fail to load or render properly, THEN THE Preview_Viewer SHALL NOT display the 3D preview until lighting is working correctly.

### Requirement 6: STL Export

**User Story:** As a user, I want to download the generated STL file so that I can send it to my 3D printer.

#### Acceptance Criteria

1. WHEN an STL mesh is generated, THE Lithophane_Generator SHALL provide a download button labeled with the output filename.
2. WHEN the user clicks the download button, THE Lithophane_Generator SHALL serve the STL file in binary format with a .stl extension.
3. WHEN generating the download filename, THE Lithophane_Generator SHALL derive it from the original uploaded image filename with a _lithophane suffix.

### Requirement 7: Application Controls

**User Story:** As a user, I want a shutdown button so that I can gracefully close the application.

#### Acceptance Criteria

1. THE Lithophane_Generator SHALL display a Shutdown App button in the interface.
2. WHEN the user clicks the Shutdown App button, THE Lithophane_Generator SHALL close the browser tab and terminate the application process gracefully using keyboard simulation and process termination.
3. IF the graceful shutdown fails, THEN THE Lithophane_Generator SHALL guarantee the process is terminated by force-exiting.

### Requirement 8: Technical Constraints

**User Story:** As a developer, I want the codebase to follow functional programming style so that the application is maintainable and consistent with project standards.

#### Acceptance Criteria

1. THE Lithophane_Generator SHALL be implemented using strictly process-oriented (functional) programming with no classes or OOP constructs.
2. THE Lithophane_Generator SHALL store all API keys and secrets in a .env file.
3. THE Lithophane_Generator SHALL include a requirements.txt file listing all pip dependencies.
4. THE Lithophane_Generator SHALL include a README.md file at the project root documenting the application.
5. THE Lithophane_Generator SHALL use Streamlit as the UI framework, Pillow for image processing, and a mesh generation library (numpy-stl or trimesh) for STL creation.
