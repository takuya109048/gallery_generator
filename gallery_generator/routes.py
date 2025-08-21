from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory, session, redirect, url_for, send_file
from gallery_generator.services.upload_service import UploadService
from gallery_generator.services.delete_service import DeleteService
from gallery_generator.services.report_service import ReportService
import logging
import io
import os
from mimetypes import guess_type

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

@main.route('/')
def root_redirect():
    return redirect(url_for('main.create_gallery'))

@main.route('/create_gallery', methods=['GET', 'POST'])
def create_gallery():
    if request.method == 'POST':
        gallery_name = request.form.get('gallery_name')
        if gallery_name:
            return redirect(url_for('main.index', gallery_name=gallery_name))
        else:
            return render_template('create_gallery.html', error='Gallery name cannot be empty.')
    return render_template('create_gallery.html')

@main.route('/gallery/<gallery_name>')
def index(gallery_name):
    gallery_data = current_app.data_manager.read_gallery_data(gallery_name)
    return render_template('index.html', gallery_data=gallery_data, gallery_name=gallery_name)

@main.route('/gallery/<gallery_name>/upload', methods=['POST'])
def upload_file(gallery_name):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Read the file content into memory or save to a temporary file
        # so it can be passed to the background task
        file_content = file.read()
        original_filename = file.filename

        # Start background task for processing
        current_app.socketio.start_background_task(
            _process_upload_in_background,
            current_app._get_current_object(), # Pass the app context
            file_content,
            original_filename,
            gallery_name
        )
        return jsonify({'message': 'Upload initiated successfully'}), 202
    return jsonify({'error': 'Something went wrong'}), 500

def _process_upload_in_background(app, file_content, original_filename, gallery_name):
    with app.app_context():
        upload_service = UploadService(app.storage, socketio=app.socketio)
        # Create a BytesIO object from the file_content to simulate a file stream
        import io
        file_stream = io.BytesIO(file_content)
        file_stream.filename = original_filename # Add filename attribute for consistency

        new_gallery_data = upload_service.process_zip_file(file_stream, gallery_name)
        
        if new_gallery_data:
            existing_data = app.data_manager.read_gallery_data(gallery_name)
            
            def merge_data(existing, new):
                existing_image_paths = {img['full_path'] for img in existing.get('images', [])}
                for new_image in new.get('images', []) :
                    if new_image['full_path'] not in existing_image_paths:
                        existing.get('images', []).append(new_image)

                existing_children_map = {child['name']: child for child in existing.get('children', [])}
                for new_child in new.get('children') :
                    if new_child['name'] in existing_children_map:
                        merge_data(existing_children_map[new_child['name']], new_child)
                    else:
                        existing.get('children', []).append(new_child)
            
            if not existing_data or (not existing_data.get('images') and not existing_data.get('children')):
                final_gallery_data = new_gallery_data
            else:
                merge_data(existing_data, new_gallery_data)
                final_gallery_data = existing_data

            app.data_manager._sort_gallery_data(final_gallery_data)
            app.data_manager.write_gallery_data(final_gallery_data, gallery_name)
            app.socketio.emit('gallery_updated', {'message': 'Upload complete and gallery updated!', 'gallery_data': final_gallery_data})
        else:
            # Handle failure in background task
            app.socketio.emit('upload_failed', {'message': 'Failed to process zip file', 'gallery_name': gallery_name})
            logger.error(f"Failed to process zip file for gallery {gallery_name}")


@main.route('/gallery/<gallery_name>/upload_status', methods=['GET'])
def get_upload_status(gallery_name):
    progress = UploadService.get_upload_progress(gallery_name)
    return jsonify({'progress': progress}), 200

@main.route('/gallery/<gallery_name>/delete', methods=['POST'])
def delete_items(gallery_name):
    data = request.get_json()
    paths_to_delete = data.get('paths', [])
    if not paths_to_delete:
        return jsonify({'error': 'No items specified for deletion'}), 400

    delete_service = DeleteService(current_app.storage, current_app.data_manager)
    if delete_service.delete_items(paths_to_delete, gallery_name):
        updated_gallery_data = current_app.data_manager.read_gallery_data(gallery_name)
        current_app.socketio.emit('gallery_updated', updated_gallery_data)
        return jsonify({'message': 'Items deleted successfully'}), 200
    else:
        return jsonify({'error': 'Failed to delete items'}), 500

@main.route('/gallery/<gallery_name>/update_comment', methods=['POST'])
def update_comment(gallery_name):
    data = request.get_json()
    path = data.get('path')
    comment = data.get('comment')

    if path is None:
        return jsonify({'error': 'Path not specified for comment update'}), 400

    if current_app.data_manager.update_comment(path, comment, gallery_name):
        updated_gallery_data = current_app.data_manager.read_gallery_data(gallery_name)
        current_app.socketio.emit('gallery_updated', updated_gallery_data)
        return jsonify({'message': 'Comment updated successfully'}), 200
    else:
        return jsonify({'error': 'Failed to update comment'}), 500

@main.route('/gallery/<gallery_name>/update_status', methods=['POST'])
def update_image_status(gallery_name):
    data = request.get_json()
    image_paths = data.get('image_paths')
    status = data.get('status')

    if not image_paths or not status:
        return jsonify({'error': 'Missing image_paths or status'}), 400

    if status not in ['good', 'bad', 'neutral']:
        return jsonify({'error': 'Invalid status'}), 400

    if current_app.data_manager.update_image_status(image_paths, status, gallery_name):
        updated_gallery_data = current_app.data_manager.read_gallery_data(gallery_name)
        current_app.socketio.emit('gallery_updated', {'message': f'Image status updated to {status}', 'gallery_data': updated_gallery_data})
        return jsonify({'message': 'Image status updated successfully'}), 200
    else:
        return jsonify({'error': 'Failed to update image status'}), 500

@main.route('/images/<gallery_name>/<path:image_path>')
def serve_image(gallery_name, image_path):
    storage = current_app.storage
    full_image_path = f"{gallery_name}/{image_path}"
    
    if storage.exists(full_image_path):
        try:
            image_data = storage.load(full_image_path)
            mimetype = guess_type(image_path)[0] or 'application/octet-stream'
            return send_file(io.BytesIO(image_data), mimetype=mimetype)
        except Exception as e:
            logger.error(f"Error serving image {full_image_path}: {e}")
            return jsonify({'error': 'Failed to serve image'}), 500
    else:
        logger.warning(f"Image not found: {full_image_path}")
        return jsonify({'error': 'Image not found'}), 404

@main.route('/gallery/<gallery_name>/api/gallery_data')
def get_gallery_data(gallery_name):
    gallery_data = current_app.data_manager.read_gallery_data(gallery_name)
    if gallery_data:
        return jsonify(gallery_data)
    return jsonify({'error': 'Gallery data not found'}), 404

@main.route('/gallery/<gallery_name>/api/versions')
def list_versions(gallery_name):
    versions = current_app.data_manager.list_backups(gallery_name)
    # Timestamps need to be serializable
    for version in versions:
        if version.get('timestamp'):
            version['timestamp'] = version['timestamp'].isoformat()
    return jsonify(versions)

@main.route('/gallery/<gallery_name>/api/version/<filename>')
def get_version(gallery_name, filename):
    version_data = current_app.data_manager.read_backup(filename, gallery_name)
    if version_data:
        return jsonify(version_data)
    return jsonify({'error': 'Version not found'}), 404

@main.route('/gallery/<gallery_name>/revert_version', methods=['POST'])
def revert_version(gallery_name):
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename not specified'}), 400

    if current_app.data_manager.revert_to_version(filename, gallery_name):
        updated_gallery_data = current_app.data_manager.read_gallery_data(gallery_name)
        current_app.socketio.emit('gallery_updated', updated_gallery_data)
        return jsonify({'message': 'Successfully reverted'}), 200
    else:
        return jsonify({'error': 'Failed to revert version'}), 500

@main.route('/gallery/<gallery_name>/export_report', methods=['POST'])
def export_report(gallery_name):
    data = request.get_json()
    report_format = data.get('format')
    gallery_data = data.get('gallery_data')

    if not report_format or not gallery_data:
        return jsonify({'error': 'Missing format or gallery data'}), 400

    report_service = ReportService(current_app.storage)
    
    try:
        base_url = request.url_root.rstrip('/')

        if report_format == 'html':
            report_content = report_service.generate_html_report(gallery_data, gallery_name)
            mimetype = 'text/html'
            download_name = 'report.html'
        elif report_format == 'markdown':
            report_content = report_service.generate_markdown_report(gallery_data, gallery_name, base_url)
            mimetype = 'text/markdown'
            download_name = 'report.md'
        else:
            return jsonify({'error': 'Invalid format specified'}), 400

        return send_file(
            io.BytesIO(report_content.encode('utf-8')),
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': 'Failed to generate report'}), 500
