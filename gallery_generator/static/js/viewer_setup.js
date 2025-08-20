document.addEventListener('DOMContentLoaded', () => {
    const galleryContainer = document.getElementById('gallery-container');

    // Function to initialize Viewer.js on a given element
    const initializeViewer = (element) => {
        if (element) {
            const viewer = new Viewer(element, {
                inline: false,
                button: true,
                navbar: true,
                title: true,
                toolbar: true,
                tooltip: true,
                movable: true,
                zoomable: true,
                rotatable: true,
                scalable: true,
                transition: true,
                fullscreen: true,
                keyboard: true,
                url: 'data-src', // Use data-src for lazy loaded images
                filter(image) {
                    // Only show images that are not placeholders and are part of the current view
                    return image.classList.contains('lazyload') === false;
                },
            });
            return viewer;
        }
        return null;
    };

    // Re-initialize viewer when gallery content changes (e.g., after upload or filter)
    // This function will be called from gallery.js after rendering the gallery
    window.setupImageViewer = () => {
        // Destroy existing viewer instance if any
        if (galleryContainer.viewer) {
            galleryContainer.viewer.destroy();
        }
        // Initialize new viewer instance
        galleryContainer.viewer = initializeViewer(galleryContainer);
    };

    // Initial setup
    window.setupImageViewer();
});
