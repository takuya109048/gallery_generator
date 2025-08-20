Developer: # Requirements Definition: Photo Gallery Generator

## 1. Overview
A tool that reads photo folders organized in a directory hierarchy and automatically generates an HTML-based photo gallery that reflects the folder structure.

---

## 2. Frontend Requirements

### 2.1. User Interface
- **Photo Gallery**:
  - Dynamically display headings (as full paths) and image previews based on the hierarchical structure defined in a JSON file.
  - Headings should only be displayed if images exist directly within that directory. Ancestor headings without direct images will be hidden, but their descendant images will still be displayed.
  - Images and placeholder images should have a basic aspect ratio of 4:3.
  - The image layout should be a **variable column** format, where the preview size and number of columns automatically adjust based on the screen width.
  - The gallery should implement **lazy loading** for performance enhancement.
    - Only load images that are within the viewport; images outside the viewport will be queued for loading.
    - Display placeholder images for unloaded images.
    - This prevents the overall gallery volume from changing before and after image loading.
  - Clicking an image preview should open a modal image viewer using viewer.js.
  - A checkbox or icon should be placed on each image preview to indicate its selected/unselected state.
  - Implement smooth single selection and multiple selection (e.g., using the Shift key).
  - Ensure that the viewer.js modal display operation and the image selection function do not interfere with each other.
- **Sidebar**:
  - Display a fixed **Table of Contents (TOC)** listing all headings as full paths, without indentation.
  - Provide a date selection dropdown.
    - The dropdown options should be a unique list of all image modification dates.
    - Selecting a date should filter the TOC and photo gallery to display only headings containing images with that specific modification date.
  - Clicking an item should smoothly scroll to the corresponding heading position. TOC jump links should be robust and reliable.
- **Upload Form**:
  - Provide a form for uploading a zip file.
  - Offer two methods for file selection:
    1. A drag-and-drop area.
    2. A button to browse the file path.
- **Comment Form**:
  - Place a text area and a submit button for comments directly below each heading.
  - This form should not be displayed if no photos exist in the corresponding directory.
- **Report Export Button**:
  - [x] Provide a button to export a gallery report.
  - [x] This button should generate a report of the currently displayed gallery content (the entire gallery or the date-filtered one).
  - [x] The export format should be selectable from HTML and Markdown.
- **Version History Navigation**:
  - Provide an interface in the sidebar to select a backed-up JSON version.
  - Selecting a version should preview the gallery based on that JSON file.
  - A "Revert to Version" button should be available to restore the selected version to the active state.
- **Deletion Mode**:
  - Place a "Deletion Mode" toggle button on the main screen.
  - In deletion mode, each image preview and heading should have a selection/deselection function for deletion.
  - Image previews should allow for smooth single and multiple selection (e.g., using the Shift key).
  - Selecting a heading should select all images within that heading and its subheadings for deletion.
  - Provide a "Confirm Deletion" button to execute the deletion of selected items.

### 2.2. Browser Compatibility
- Must display and function correctly on major modern browsers (Chrome, Firefox, Safari, etc.).
- Use WebSockets or a similar technology (e.g., Server-Sent Events) to reflect backend data updates in real-time.

---

## 3. Backend Requirements

### 3.1. File Upload and Data Management
- **Upload Processing**:
  - Securely accept zip files submitted via the web form.
- **Data Processing**:
  - Unzip the file and consolidate all internal image files into a single storage folder.
  - Append a hash value to the end of the original filename when saving to storage.
  - The hash value should be generated from the original filename and modification date.
  - Retrieve the image file's modification date and include this information in the JSON file.
  - Record and save the original directory hierarchy and comments for each heading in a JSON file (e.g., `gallery_data.json`).
- **Storage Abstraction**:
  - Abstract image data read/write operations to be independent of cloud or local storage.
  - Create a dedicated module, such as `storage.py`, to implement class-based logic for storage operations.
  - The cloud storage pattern will be defined as an **empty class to be implemented** in **`cloud_storage_manager.py`**. The local storage pattern will be implemented in `local_storage_manager.py`.
  - For both patterns, read/write operations should not be performed directly; instead, a temporary file (temp) should be created inside the `flask/static/temp` folder, and operations should be performed on that file.
- **Version Control**:
  - Each time `gallery_data.json` is updated, save the previous version with a timestamped filename (e.g., `gallery_data_20250815231800.json`) to a backup folder.
  - Read the backed-up JSON files and serve them upon a request from the frontend.
  - Upon receiving a "Revert to Version" request, overwrite the active `gallery_data.json` with the selected backup file.

### 3.2. JSON Data Structure Definition
- **Structure**:
  - A hierarchical object representing the nested directory structure.
  - Each directory node should contain the following information:
    - `name`: Folder name (used as the heading).
    - `images`: A list of image files belonging to that directory.
      - Each image file should be defined as an object containing the filename, modification date, and a full path including parent headings (e.g., `ParentFolder/SubFolder/Image.jpg`).
    - `comment`: The comment associated with that directory (heading).
    - `children`: A list of subdirectories (a recursive structure).

### 3.3. Web Server Functionality
- **Framework**: Use Flask.
- **Routing**:
  - Gallery display route (e.g., `/`): Reads the JSON file and renders an HTML template.
  - Upload processing route (e.g., `/upload`): Accepts a zip file, performs decompression, and generates the JSON file.
  - Report export route (e.g., `/report`): Generates and allows the download of an HTML, Markdown, or PDF report containing only the selected images, based on the request.
  - Deletion processing route (e.g., `/delete`): Accepts the names of image files and heading paths to be deleted and executes the deletion process.
- **Asynchronous Processing**:
  - All Flask operations should be executed asynchronously. This allows users to continue other operations without waiting for long-running processes (e.g., zip file decompression).
  - When a data update is complete (e.g., comment saved, image upload complete, deletion complete), notify the frontend in real-time to update the display.

### 3.4. Non-Functional Requirements
- **Operating Environment**: A Python-enabled environment.
- **Performance**: The HTML should be generated at an acceptable speed, even with a large number of image files.
- **Scalability**: The design should allow for future support of video files and other file formats.
- **Logging**:
  - Logging should be implemented using Python's standard `logging` module.
  - Logger settings should be managed centrally in a single Python file (e.g., `logger_config.py`).
- **Configuration**:
  - Dynamic configuration values such as paths, loading/saving methods, logging settings, and REST API information should not be hard-coded. They should be managed in an external configuration file (e.g., `config.json` or `.ini` file).
  - A dedicated manager class for reading and managing these settings should be implemented in `config_manager.py` or similar.

### 3.5. Report Export Details
- **HTML Report**:
  - Output as a static HTML file with a TOC sidebar.
  - The TOC should have a heading hierarchy and anchor links, similar to the gallery's TOC.
  - The content of the report should include headings, comments, and selected image previews (variable column layout).

---

## 4. Project Directory Structure 📁

The final project directory will be based on the following structure:

.
├── gallery_generator/
│   ├── **init**.py           # Flask application initialization
│   ├── app.py                # Application entry point
│   ├── config_manager.py     # Configuration file loading and management class
│   ├── logger_config.py      # Centralized logging configuration
│   ├── routes.py             # API endpoint and routing definitions
│   ├── services/
│   │   ├── **init**.py
│   │   ├── upload_service.py # Upload processing logic
│   │   ├── delete_service.py # Deletion processing logic
│   │   ├── report_service.py # Report generation logic
│   │   └── data_manager.py   # JSON data read/write and version control
│   ├── storage/
│   │   ├── **init**.py
│   │   ├── storage.py        # Storage abstract base class
│   │   ├── local_storage.py  # Local storage implementation
│   │   └── cloud_storage.py  # Cloud storage empty class (to be implemented)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     # Gallery stylesheet
│   │   ├── js/
│   │   │   ├── gallery.js        # Frontend main logic
│   │   │   └── viewer_setup.js   # viewer.js initialization and setup
│   │   ├── images/
│   │   │   └── placeholder.jpg # Placeholder image
│   │   └── temp/             # Temporary files folder
│   └── templates/
│       └── index.html        # Gallery page HTML template
├── tests/                  # Test directory
│   ├── test_routes.py
│   └── test_services.py
├── backups/                # JSON version backup folder
├── config/
│   └── config.json         # Configuration file
├── .env                    # Environment variables
├── requirements.txt        # List of dependencies
└── README.md

#### Directory and File Roles
- **`gallery_generator/`**: The main application package.
  - **`app.py`**: Creates the Flask application instance and performs initial setup.
  - **`routes.py`**: Defines API endpoint routing and corresponding functions.
  - **`services/`**: Contains the **business logic** for each function. This keeps routing files simple and enhances logic reusability.
  - **`storage/`**: Separates storage-related abstraction and implementation.
  - **`static/`**: Holds static files like CSS, JavaScript, and images.
  - **`templates/`**: Holds HTML files rendered by the Jinja2 template engine.
- **`tests/`**: The location for writing test code to maintain project quality.
- **`backups/`**: Stores timestamped backup JSON files.
- **`config/`**: Manages dynamic configuration values like paths and API keys in external files.
- **`requirements.txt`**: Specifies the project's dependencies.

---