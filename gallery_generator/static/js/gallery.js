document.addEventListener('DOMContentLoaded', () => {
    const galleryContainer = document.getElementById('gallery-container');
    const tocContainer = document.getElementById('toc-container');
    const dateFilter = document.getElementById('date-filter');
    const fileElem = document.getElementById('fileElem');
    const confirmDeletionBtn = document.getElementById('confirm-deletion');
    const versionHistorySelect = document.getElementById('version-history-select');
    const revertVersionBtn = document.getElementById('revert-version-btn');
    const exportReportBtn = document.getElementById('export-report-btn');
    const menuToggle = document.getElementById('menu-toggle');
    const menuSidebar = document.getElementById('menu-sidebar');
    const closeMenuBtn = document.getElementById('close-menu-btn');

    // New status buttons
    const statusGoodBtn = document.getElementById('status-good-btn');
    const statusBadBtn = document.getElementById('status-bad-btn');
    const statusNeutralBtn = document.getElementById('status-neutral-btn');

    // Get gallery name from the body's data attribute
    const galleryName = document.body.dataset.galleryName;
    if (!galleryName) {
        console.error("Gallery name not found. Redirecting to gallery creation.");
        window.location.href = '/create_gallery'; // Redirect if galleryName is not set
        return; // Stop further execution
    }

    let currentGalleryData = {};
    let selectedImages = new Set();
    let lastSelectedImage = null;

    // Menu sidebar toggle
    menuToggle.addEventListener('click', (event) => {
        event.stopPropagation(); // Prevent this click from immediately closing the sidebar via the document listener
        menuSidebar.classList.toggle('menu-open');
    });

    closeMenuBtn.addEventListener('click', (event) => {
        event.preventDefault();
        menuSidebar.classList.remove('menu-open');
    });

    // Close menu sidebar when clicking outside
    document.addEventListener('click', (event) => {
        // Check if the menu sidebar is open and the click is outside the sidebar and not on the menu toggle button
        if (menuSidebar.classList.contains('menu-open') &&
            !menuSidebar.contains(event.target) &&
            !menuToggle.contains(event.target)) {
            menuSidebar.classList.remove('menu-open');
        }
    });

    // Function to display non-blocking messages (toast notifications)
    const showMessage = (message, type = 'info') => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('toast-message', `toast-${type}`);
        messageDiv.textContent = message;
        document.body.appendChild(messageDiv);

        // Trigger reflow to enable CSS transition
        messageDiv.offsetHeight;
        messageDiv.classList.add('show');

        setTimeout(() => {
            messageDiv.classList.remove('show');
            messageDiv.addEventListener('transitionend', () => messageDiv.remove());
        }, 3000); // Message disappears after 3 seconds
    };

    let progressBarToast = null; // To keep track of the toast element
    let progressBarInner = null; // To keep track of the inner progress bar element

    const showProgressBarToast = (progress) => {
        if (!progressBarToast) {
            progressBarToast = document.createElement('div');
            progressBarToast.classList.add('toast-message', 'toast-info', 'progress-toast');
            document.body.appendChild(progressBarToast);

            // Create inner progress bar element
            progressBarInner = document.createElement('div');
            progressBarInner.classList.add('progress-bar-inner'); // Add a class for styling
            progressBarToast.appendChild(progressBarInner);

            const textSpan = document.createElement('span');
            textSpan.classList.add('progress-text');
            progressBarToast.appendChild(textSpan);
        }

        const percentage = Math.round(progress);
        progressBarInner.style.width = `${percentage}%`;
        progressBarToast.querySelector('.progress-text').textContent = `Uploading: ${percentage}%`;

        progressBarToast.offsetHeight; // Trigger reflow
        progressBarToast.classList.add('show');

        if (percentage >= 100) {
            setTimeout(() => {
                progressBarToast.classList.remove('show');
                progressBarToast.addEventListener('transitionend', () => {
                    if (progressBarToast && progressBarToast.parentNode) {
                        progressBarToast.parentNode.removeChild(progressBarToast);
                    }
                    progressBarToast = null;
                    progressBarInner = null; // Reset inner bar as well
                }, { once: true });
            }, 500);
        }
    };

    const checkUploadStatusAndDisplayProgressBar = async () => {
        const galleryName = document.body.dataset.galleryName;
        if (!galleryName) return;

        try {
            const response = await fetch(`/gallery/${galleryName}/upload_status`);
            if (response.ok) {
                const data = await response.json();
                const progress = data.progress;

                if (progress === null || typeof progress === 'undefined') {
                    // No upload in progress or no previous upload status found, do nothing
                    return;
                }

                if (progress >= 0 && progress < 100) {
                    showProgressBarToast(progress);
                } else if (progress === 100) {
                    // If upload is complete, ensure progress bar is hidden
                    if (progressBarToast) {
                        progressBarToast.classList.remove('show');
                        progressBarToast.parentNode.removeChild(progressBarToast);
                        progressBarToast = null;
                        progressBarInner = null;
                    }
                }
            } else if (progress === -1) {
                    // Handle error state
                    showMessage('Previous upload failed. Please try again.', 'error');
                    if (progressBarToast) {
                        progressBarToast.classList.remove('show');
                        progressBarToast.parentNode.removeChild(progressBarToast);
                        progressBarToast = null;
                        progressBarInner = null;
                    }
                }
            }
         catch (error) {
            console.error('Error checking upload status:', error);
            // Do not show error message to user, as it might be a transient network issue
        }
    };

    // Simple hash function for generating unique IDs
    const simpleHash = (str) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash |= 0; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(16); // Convert to hex string
    };

    // Function to fetch and render gallery data
    const fetchAndRenderGallery = async () => {
        try {
            const dataResponse = await fetch(`/gallery/${galleryName}/api/gallery_data`);
            if (dataResponse.ok) {
                currentGalleryData = await dataResponse.json();
                renderGallery(currentGalleryData);
                populateDateFilter(currentGalleryData);
                populateVersionHistory();
            } else {
                console.error('Failed to fetch initial gallery data:', dataResponse.statusText);
                // If gallery data not found, it might be a new gallery, so initialize with empty data
                currentGalleryData = {"name": "root", "images": [], "comment": "", "children": []};
                renderGallery(currentGalleryData);
                populateDateFilter(currentGalleryData);
                populateVersionHistory();
            }
        }
        catch (error) {
            console.error('Error fetching gallery data:', error);
            // If there's an error, initialize with empty data
            currentGalleryData = {"name": "root", "images": [], "comment": "", "children": []};
            renderGallery(currentGalleryData);
            populateDateFilter(currentGalleryData);
            populateVersionHistory();
        }
    };

    // Function to render the gallery based on data
    const renderGallery = (data, filterDate = 'all') => {
        galleryContainer.innerHTML = '';
        tocContainer.innerHTML = '';
        let galleryHtml = '';
        let tocHtmlAccumulator = '';

        const renderNode = (node, level, currentPath = '') => {
            let currentSectionHtml = ''; // HTML for this node's heading and direct images
            let nodeTocHtml = '';
            let shouldRenderThisNodeHeading = false; // Flag to determine if this node's heading should be rendered

            // Check if this node directly has images
            const hasDirectImages = (node.images && node.images.length > 0);

            // Recursively render children and collect their HTML and TOC entries
            let childrenAccumulatedHtml = ''; // HTML from all rendered children (including their descendants)
            let childrenAccumulatedTocHtml = ''; // TOC entries from all rendered children

            if (node.children && node.children.length > 0) {
                const newFullPath = currentPath ? `${currentPath}/${node.name}` : node.name;
                node.children.forEach(child => {
                    const childRenderResult = renderNode(child, level + 1, newFullPath);
                    // Children's HTML is always collected, regardless of whether their parent's heading is displayed
                    childrenAccumulatedHtml += childRenderResult.sectionHtml; // This now includes child's own section and its children
                    childrenAccumulatedTocHtml += childRenderResult.nodeTocHtml;
                });
            }

            // Determine if this node's heading should be rendered
            shouldRenderThisNodeHeading = hasDirectImages;

            if (shouldRenderThisNodeHeading && node.name !== 'root') { // Don't create a section for the invisible root
                const headingText = currentPath ? `${currentPath}/${node.name}` : node.name;
                const sanitizedHeadingText = encodeURIComponent(headingText).replace(/%[0-9A-Fa-f]{2}/g, '-').replace(/[^a-zA-Z0-9_-]+/g, '');
                const uniqueHash = simpleHash(headingText); // Hash the original headingText (full path)
                const headingId = `heading-${sanitizedHeadingText}-${uniqueHash}-${level}`;

                currentSectionHtml += `<div class="gallery-section" id="${headingId}">`;
                currentSectionHtml += `<h${level + 1}><input type="checkbox" class="heading-checkbox" data-heading-id="${headingId}"> ${headingText}</h${level + 1}>`;

                // Comment form - only display if there are direct images in this node
                if (hasDirectImages) {
                    currentSectionHtml += `<div class="comment-form">
                                        <textarea placeholder="Add a comment...">${node.comment || ''}</textarea>
                                        <button data-path="${node.full_path}">Save Comment</button>
                                    </div>`;
                }

                currentSectionHtml += `<div class="image-grid">
`;
                const filteredImages = node.images.filter(img => {
                    return filterDate === 'all' || img.modification_date === filterDate;
                });

                filteredImages.forEach(image => {
                    const imageUrl = `/images/${galleryName}/${image.full_path}`;
                    const placeholderUrl = `/static/images/placeholder.jpg`;
                    const displayName = image.filename.substring(0, image.filename.lastIndexOf('_'));
                    const imageStatusClass = image.status === 'good' ? 'good-image' : (image.status === 'bad' ? 'bad-image' : '');

                    currentSectionHtml += `
                        <div class="image-item ${imageStatusClass}" data-full-path="${image.full_path}" data-status="${image.status}">
                            <input type="checkbox" class="checkbox" ${selectedImages.has(image.full_path) ? 'checked' : ''}>
                            <img src="${placeholderUrl}" data-src="${imageUrl}" alt="${image.filename}" class="lazyload">
                            <p>${displayName}</p>
                        </div>
                    `;
                });
                currentSectionHtml += `</div>`;
                currentSectionHtml += `</div>`;

                nodeTocHtml += `<li class="level-${level}"><a href="#${headingId}">${headingText}</a>`;
                // TOC for children should still be nested under the parent's TOC if the parent's heading is displayed
                if (childrenAccumulatedTocHtml) {
                    nodeTocHtml += `<ul>${childrenAccumulatedTocHtml}</ul>`;
                }
                nodeTocHtml += `</li>`;
            } else {
                // If this node's heading is not rendered, its children's TOC entries should still be passed up
                nodeTocHtml += childrenAccumulatedTocHtml;
            }

            // The total section HTML returned includes this node's section (if rendered) and all its children's HTML
            const totalSectionHtml = currentSectionHtml + childrenAccumulatedHtml;

            return {
                sectionHtml: totalSectionHtml,
                nodeTocHtml: nodeTocHtml,
                // We still need a flag to tell the parent if *any* content (either this node's or its children's) was rendered
                // This is important for the initial call in renderGallery to decide what to append to galleryHtml
                hasRenderedContent: shouldRenderThisNodeHeading || (childrenAccumulatedHtml !== '')
            };
        };

        // Start rendering from the root node's children if it's the initial call
        if (data.children) {
            data.children.forEach(child => {
                const renderResult = renderNode(child, 1);
                if (renderResult.hasRenderedContent) { // Check if any content was rendered
                    galleryHtml += renderResult.sectionHtml;
                    tocHtmlAccumulator += renderResult.nodeTocHtml;
                }
            });
        }
        galleryContainer.innerHTML = galleryHtml;
        tocContainer.innerHTML = `<ul>${tocHtmlAccumulator}</ul>`;

        // Add smooth scrolling to TOC links
        tocContainer.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();

                const targetElement = document.querySelector(this.getAttribute('href'));
                if (targetElement) {
                    const headerHeight = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-height'));
                    const extraOffset = 20; // Add a little extra margin
                    const elementPosition = targetElement.getBoundingClientRect().top + window.pageYOffset;
                    window.scrollTo({
                        top: elementPosition - headerHeight - extraOffset,
                        behavior: 'auto' // Ensure instant scroll
                    });
                }
            });
        });

        // Apply lazy loading
        applyLazyLoading();
        // Add event listeners for image selection
        addImageSelectionListeners();
        // Add event listeners for comment forms
        addCommentFormListeners();
        // Initialize image viewer
        window.setupImageViewer();
    };

    // Lazy loading implementation
    const applyLazyLoading = () => {
        const lazyImages = document.querySelectorAll('img.lazyload');
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazyload');
                    observer.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => {
            observer.observe(img);
        });
    };

    // Populate date filter dropdown
    const populateDateFilter = (data) => {
        const dates = new Set();
        const extractDates = (node) => {
            if (node.images) {
                node.images.forEach(img => dates.add(img.modification_date));
            }
            if (node.children) {
                node.children.forEach(child => extractDates(child));
            }
        };
        extractDates(data);

        dateFilter.innerHTML = '<option value="all">All Dates</option>';
        Array.from(dates).sort().forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = date;
            dateFilter.appendChild(option);
        });
    };

    dateFilter.addEventListener('change', (event) => {
        renderGallery(currentGalleryData, event.target.value);
    });

    // Upload functionality
    fileElem.addEventListener('change', (e) => handleFiles(e.target.files), false);

    

    const handleFiles = async (files) => {
        if (files.length === 0) return;
        const file = files[0];

        if (file.type !== 'application/x-zip-compressed' && file.type !== 'application/zip') {
            showMessage('Please upload a zip file.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // Show progress bar toast
        showProgressBarToast(0); // Initialize with 0%

        try {
            const response = await fetch(`/gallery/${galleryName}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                showMessage(`Upload failed: ${error.error}`, 'error');
                // Hide progress bar toast on failure
                if (progressBarToast) {
                    progressBarToast.classList.remove('show');
                    progressBarToast.parentNode.removeChild(progressBarToast);
                    progressBarToast = null;
                }
            }
             // On success, we don't need to do anything here.
             // The 'gallery_updated' socket event will handle the UI update.

        } catch (error) {
            console.error('Error uploading file:', error);
            showMessage('An error occurred during upload.', 'error');
            // Hide progress bar toast on error
            if (progressBarToast) {
                progressBarToast.classList.remove('show');
                progressBarToast.parentNode.removeChild(progressBarToast);
                progressBarToast = null;
            }
        } finally {
            // Clear the file input value to allow re-uploading the same file
            fileElem.value = '';
        }
    };

    // Image selection for deletion mode
    const addImageSelectionListeners = () => {
        document.querySelectorAll('.image-item .checkbox').forEach(checkbox => {
            checkbox.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent viewer.js from opening
                const imageItem = e.target.closest('.image-item');
                const fullPath = imageItem.dataset.fullPath;

                if (e.shiftKey && lastSelectedImage) {
                    const allImages = Array.from(document.querySelectorAll('.image-item'));
                    const startIndex = allImages.findIndex(item => item.dataset.fullPath === lastSelectedImage);
                    const endIndex = allImages.findIndex(item => item.dataset.fullPath === fullPath);

                    const [start, end] = [Math.min(startIndex, endIndex), Math.max(startIndex, endIndex)];

                    for (let i = start; i <= end; i++) {
                        const imgPath = allImages[i].dataset.fullPath;
                        const imgCheckbox = allImages[i].querySelector('.checkbox');
                        if (e.target.checked) {
                            selectedImages.add(imgPath);
                            imgCheckbox.checked = true;
                        } else {
                            selectedImages.delete(imgPath);
                            imgCheckbox.checked = false;
                        }
                    }
                } else {
                    if (e.target.checked) {
                        selectedImages.add(fullPath);
                    } else {
                        selectedImages.delete(fullPath);
                    }
                }
                lastSelectedImage = fullPath;
                
                // Update parent heading checkbox state
                const parentSection = imageItem.closest('.gallery-section');
                if (parentSection) {
                    const headingCheckbox = parentSection.querySelector('.heading-checkbox');
                    if (headingCheckbox) {
                        const allImagesInParentSection = parentSection.querySelectorAll('.image-item .checkbox');
                        const allCheckedInParentSection = Array.from(allImagesInParentSection).every(cb => cb.checked);
                        headingCheckbox.checked = allCheckedInParentSection;
                    }
                }
                updateConfirmDeletionButtonState();
                updateStatusButtonsState(); // Update status buttons when selection changes
            });
        });

        // Heading checkbox selection
        document.querySelectorAll('.heading-checkbox').forEach(headingCheckbox => {
            headingCheckbox.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent heading click event if any
                const section = e.target.closest('.gallery-section');
                const isChecked = e.target.checked;

                // Get all image checkboxes within this section and its child sections
                const imageCheckboxes = section.querySelectorAll('.image-item .checkbox');

                imageCheckboxes.forEach(checkbox => {
                    const fullPath = checkbox.closest('.image-item').dataset.fullPath;
                    checkbox.checked = isChecked;
                    if (isChecked) {
                        selectedImages.add(fullPath);
                    } else {
                        selectedImages.delete(fullPath);
                    }
                });
                updateConfirmDeletionButtonState();
                updateStatusButtonsState(); // Update status buttons when selection changes
            });
        });

        // Existing heading click listener (now only for smooth scrolling if checkbox is not clicked)
        document.querySelectorAll('.gallery-section h2, .gallery-section h3, .gallery-section h4, .gallery-section h5, .gallery-section h6').forEach(heading => {
            heading.style.cursor = 'pointer'; // Indicate it's clickable
            heading.addEventListener('click', (e) => {
                // If the click was on the checkbox, do nothing here as it's handled by the checkbox listener
                if (e.target.classList.contains('heading-checkbox')) {
                    return;
                }

                // Original logic for heading click (e.g., smooth scrolling, if implemented)
                // For now, this part is effectively a no-op unless specific heading click behavior is desired.
                // The previous logic for selecting all images under a heading is now moved to the heading-checkbox listener.
            });
        });
    };

    const updateConfirmDeletionButtonState = () => {
        confirmDeletionBtn.disabled = selectedImages.size === 0;
    };

    const updateStatusButtonsState = () => {
        const isDisabled = selectedImages.size === 0;
        statusGoodBtn.disabled = isDisabled;
        statusBadBtn.disabled = isDisabled;
        statusNeutralBtn.disabled = isDisabled;
    };

    // Event listeners for status buttons
    statusGoodBtn.addEventListener('click', () => updateImageStatus('good'));
    statusBadBtn.addEventListener('click', () => updateImageStatus('bad'));
    statusNeutralBtn.addEventListener('click', () => updateImageStatus('neutral'));

    const updateImageStatus = async (status) => {
        if (selectedImages.size === 0) {
            showMessage('No images selected to update status.', 'info');
            return;
        }

        try {
            const response = await fetch(`/gallery/${galleryName}/update_status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image_paths: Array.from(selectedImages), status: status }),
            });

            if (response.ok) {
                const result = await response.json();
                showMessage(result.message, 'success');

                // Uncheck all currently selected images and clear the selection
                selectedImages.forEach(fullPath => {
                    const imageItem = document.querySelector(`.image-item[data-full-path="${fullPath}"]`);
                    if (imageItem) {
                        const checkbox = imageItem.querySelector('.checkbox');
                        if (checkbox) {
                            checkbox.checked = false;
                        }
                    }
                });
                selectedImages.clear();
                lastSelectedImage = null; // Reset last selected image
                updateConfirmDeletionButtonState(); // Update button states after clearing selection
                updateStatusButtonsState(); // Update status buttons after clearing selection

                // Re-fetch and render gallery to reflect the new status visually
                fetchAndRenderGallery();
            } else {
                const error = await response.json();
                showMessage(`Failed to update image status: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error updating image status:', error);
            showMessage('An error occurred while updating image status.', 'error');
        }
    };


    confirmDeletionBtn.addEventListener('click', async () => {
        if (confirmDeletionBtn.disabled) return;
        if (selectedImages.size === 0) {
            showMessage('No images selected for deletion.', 'info');
            return;
        }

        if (!confirm(`Are you sure you want to delete ${selectedImages.size} selected items?`)) {
            return;
        }

        try {
            const response = await fetch(`/gallery/${galleryName}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ paths: Array.from(selectedImages) }),
            });

            if (response.ok) {
                const result = await response.json();
                showMessage(result.message, 'success');
                selectedImages.clear();
                fetchAndRenderGallery(); // Re-render gallery
            } else {
                const error = await response.json();
                showMessage(`Deletion failed: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error during deletion:', error);
            showMessage('An error occurred during deletion.', 'error');
        }
    });

    // Comment form functionality
    const addCommentFormListeners = () => {
        document.querySelectorAll('.comment-form button').forEach(button => {
            button.addEventListener('click', async (e) => {
                const textarea = e.target.previousElementSibling;
                const comment = textarea.value;
                const path = e.target.dataset.path; // This path needs to uniquely identify the heading/directory

                try {
                    const response = await fetch(`/gallery/${galleryName}/update_comment`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ path: path, comment: comment }),
                    });

                    if (response.ok) {
                        const result = await response.json();
                        showMessage(result.message, 'success');
                        // Optionally, update the currentGalleryData in memory if needed
                    } else {
                        const error = await response.json();
                        showMessage(`Failed to save comment: ${error.error}`, 'error');
                    }
                } catch (error) {
                    console.error('Error saving comment:', error);
                    showMessage('An error occurred while saving comment.', 'error');
                }
            });
        });
    };

    // Version History
    const populateVersionHistory = async () => {
        try {
            const response = await fetch(`/gallery/${galleryName}/api/versions`);
            if (response.ok) {
                const versions = await response.json();
                versionHistorySelect.innerHTML = '<option value="current">Current Version</option>';
                versions.forEach(version => {
                    const option = document.createElement('option');
                    option.value = version.filename;
                    option.textContent = `${version.filename} (${new Date(version.timestamp * 1000).toLocaleString()})`;
                    versionHistorySelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error fetching version history:', error);
        }
    };

    versionHistorySelect.addEventListener('change', async (e) => {
        const selectedVersion = e.target.value;
        if (selectedVersion === 'current') {
            fetchAndRenderGallery(); // Revert to current active data
            return;
        }
        try {
            const response = await fetch(`/gallery/${galleryName}/api/version/${selectedVersion}`);
            if (response.ok) {
                const versionData = await response.json();
                renderGallery(versionData); // Preview the selected version
            } else {
                showMessage('Failed to load version data.', 'error');
            }
        } catch (error) {
            console.error('Error loading version data:', error);
        }
    });

    revertVersionBtn.addEventListener('click', async () => {
        const selectedVersion = versionHistorySelect.value;
        if (selectedVersion === 'current') {
            showMessage('Current version is already active.', 'info');
            return;
        }
        if (!confirm(`Are you sure you want to revert to version ${selectedVersion}? This will overwrite current data.`)) {
            return;
        }

        try {
            const response = await fetch(`/gallery/${galleryName}/revert_version`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename: selectedVersion }),
            });

            if (response.ok) {
                const result = await response.json();
                showMessage(result.message, 'success');
                fetchAndRenderGallery(); // Re-fetch and render current (now reverted) gallery
            } else {
                const error = await response.json();
                showMessage(`Revert failed: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error reverting version:', error);
            showMessage('An error occurred during version reversion.', 'error');
        }
    });

    // Export Report
    exportReportBtn.addEventListener('click', async () => {
        const format = prompt("Enter export format (html, markdown, pdf):");
        if (!format) return;

        if (!['html', 'markdown', 'pdf'].includes(format.toLowerCase())) {
            showMessage("Invalid format. Please choose html, markdown, or pdf.", 'error');
            return;
        }

        try {
            const response = await fetch(`/gallery/${galleryName}/export_report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ format: format.toLowerCase(), gallery_data: currentGalleryData }),
            });

            if (response.ok) {
                const blob = await response.blob();
                const disposition = response.headers.get('Content-Disposition');
                let filename = 'report';
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    const filenameRegex = /filename[^;=\n]*=((['"])(.*?)\2|[^;\n]*)/;
                    const matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[3]) {
                        filename = matches[3];
                    }
                }
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                showMessage('Report exported successfully!', 'success');
            } else {
                const error = await response.json();
                showMessage(`Report export failed: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error exporting report:', error);
            showMessage('An error occurred during report export.', 'error');
        }
    });

    // Initialize Socket.IO
    const socket = io({ transports: ['polling', 'websocket'] }); // Databricks環境での安定性向上のため、ポーリングを優先

    socket.on('connect', () => {
        console.log('Connected to WebSocket');
    });

    socket.on('upload_progress', (data) => {
        showProgressBarToast(data.progress);
    });

    socket.on('gallery_updated', (data) => {
        console.log('Gallery updated via WebSocket:', data.message);

        // showProgressBarToast(100) will handle hiding the toast
        showMessage(data.message, 'success');
        fetchAndRenderGallery(); // Re-fetch all data and re-render the gallery
    });

    socket.on('upload_failed', (data) => {
        console.error('Upload failed via WebSocket:', data.message);
        showMessage(`Upload failed: ${data.message}`, 'error');
        // Hide progress bar toast on failure
        if (progressBarToast) {
            progressBarToast.classList.remove('show');
            progressBarToast.parentNode.removeChild(progressBarToast);
            progressBarToast = null;
            progressBarInner = null;
        }
    });

    // Initial fetch and render
    fetchAndRenderGallery();
    updateConfirmDeletionButtonState();
    updateStatusButtonsState(); // Initialize status button states
    checkUploadStatusAndDisplayProgressBar();

    // Modify fetchAndRenderGallery to not rely on parsing HTML for data
    // Instead, it should fetch data from a dedicated API endpoint
    // For now, we'll keep the existing logic but note this for future refinement.
    // A better approach would be to have a /api/gallery_data endpoint.
    // The initial render from Flask will still embed the data.
    // When a WebSocket update comes, it will provide the new data directly.
});