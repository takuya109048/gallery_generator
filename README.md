# Photo Gallery Generator

This project implements a web-based photo gallery generator that organizes images based on their folder structure and provides various features like image viewing, uploading, deletion, commenting, version control, and report generation. It's built with Flask for the backend and a modern JavaScript frontend.

## Features

-   **Dynamic Photo Gallery**: Displays images hierarchically with full path headings. Headings are only displayed if they directly contain images. The layout is a **variable column** format, adjusting preview size and columns based on screen width.
-   **Lazy Loading**: Improves performance by loading images only when they are in the viewport.
-   **Image Viewer**: Integrated `viewer.js` for a modal image viewing experience, ensuring no interference with image selection.
-   **Image Selection**: Allows smooth single and multiple selection (e.g., using the Shift key) of images and entire headings for deletion.
-   **Deletion Mode**: A dedicated mode to select and confirm deletion of images and their associated data. The "Confirm Deletion" button is always visible but enabled only when images are selected in deletion mode.
-   **File Upload**: Supports secure uploading of zip files containing images. Images are processed, hashed, and stored, maintaining the original directory hierarchy.
-   **Commenting**: Add and save comments for each gallery heading.
-   **Date Filtering**: Filter gallery content by image modification dates.
-   **Version History**: Browse and revert to previous versions of the gallery data, with timestamped backups.
-   **Report Export**: Generate and download reports of the displayed gallery content in HTML and Markdown formats.
-   **Real-time Updates**: Utilizes WebSockets to reflect backend data changes instantly on the frontend.
-   **Robust Configuration**: Dynamic configuration values are managed externally via `config.json`.
-   **Centralized Logging**: Implemented using Python's standard `logging` module.

## Project Structure

```
.
├── gallery_generator/
│   ├── __init__.py           # Flask application initialization
│   ├── app.py                # Application entry point
│   ├── config_manager.py     # Configuration file loading and management class
│   ├── logger_config.py      # Centralized logging configuration
│   ├── routes.py             # API endpoint and routing definitions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── upload_service.py # Upload processing logic
│   │   ├── delete_service.py # Deletion processing logic
│   │   ├── report_service.py # Report generation logic
│   │   └── data_manager.py   # JSON data read/write and version control
│   ├── storage/
│   │   ├── __init__.py
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
```

## Setup and Running

1.  **Clone the repository** (if applicable).

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the application**:

    Edit `config/config.json` to set up paths and other configurations. Ensure `GALLERY_ROOT`, `BACKUP_DIR`, `STATIC_DIR`, and `TEMP_DIR` are correctly set to absolute paths on your system.

4.  **Run the application**:

    ```bash
    python gallery_generator/app.py
    ```

    The application will typically run on `http://127.0.0.1:5000/`.

## Testing

To run the tests, navigate to the project root directory and execute:

```bash
pytest
```

## Future Improvements

-   Implement cloud storage integration.
-   Add user authentication and authorization.
-   Improve error handling and user feedback.
-   Implement `.env` file for environment variables.
-   Add more comprehensive unit and integration tests.
-   Optimize performance for very large galleries.
-   Extend scalability to support video files and other media formats.
