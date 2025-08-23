import os
import zipfile
import hashlib
from datetime import datetime
from ..storage.storage import Storage
import logging

logger = logging.getLogger(__name__)

class UploadService:
    _upload_progress = {} # Class-level dictionary to store upload progress
    def __init__(self, storage: Storage, socketio=None):
        self.storage = storage
        self.socketio = socketio
        # TODO: Make allowed_extensions configurable
        self.allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']

    def _generate_hashed_filename(self, original_filename, modification_date):
        name, ext = os.path.splitext(original_filename)
        hash_input = f"{original_filename}-{modification_date}".encode('utf-8')
        file_hash = hashlib.md5(hash_input).hexdigest()
        return f"{name}_{file_hash}{ext}"

    def process_zip_file(self, zip_file_stream, gallery_name):
        import concurrent.futures
        import threading

        gallery_data = {"name": "root", "images": [], "comment": "", "children": []}
        UploadService._upload_progress[gallery_name] = 0

        try:
            with zipfile.ZipFile(zip_file_stream, 'r') as zip_ref:
                file_members = [m for m in zip_ref.infolist() if not m.is_dir() and os.path.splitext(os.path.basename(m.filename))[1].lower() in self.allowed_extensions]
                total_files = len(file_members)
                if total_files == 0:
                    logger.warning("No processable image files found in the zip.")
                    UploadService._upload_progress[gallery_name] = 100
                    return gallery_data

                processed_files = 0
                progress_lock = threading.Lock()

                def _update_progress():
                    nonlocal processed_files
                    with progress_lock:
                        processed_files += 1
                        progress = (processed_files / total_files) * 100
                        UploadService._upload_progress[gallery_name] = progress
                        if self.socketio:
                            self.socketio.emit('upload_progress', {'progress': progress})
                            self.socketio.sleep(0.01)

                # Collect all file data first to avoid issues with zip_ref context
                files_to_upload = []
                for member in file_members:
                    original_filename = os.path.basename(member.filename)
                    if not original_filename:
                        continue
                    with zip_ref.open(member) as file_in_zip:
                        file_content = file_in_zip.read()
                    
                    mod_date = datetime(*member.date_time).strftime('%Y-%m-%d')
                    hashed_filename = self._generate_hashed_filename(original_filename, mod_date)
                    zip_internal_path = os.path.dirname(member.filename).replace('\\', '/')
                    storage_path = f"{gallery_name}/{hashed_filename}"

                    files_to_upload.append({
                        'storage_path': storage_path,
                        'file_content': file_content,
                        'zip_internal_path': zip_internal_path,
                        'hashed_filename': hashed_filename,
                        'mod_date': mod_date
                    })

                # Use ThreadPoolExecutor to upload files in parallel
                # Adjust max_workers based on typical API limits and environment capabilities
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    future_to_file = {executor.submit(self.storage.save, file['storage_path'], file['file_content']): file for file in files_to_upload}
                    
                    for future in concurrent.futures.as_completed(future_to_file):
                        file_data = future_to_file[future]
                        try:
                            future.result()  # Raise exception if upload failed
                            # The node manipulation needs to be thread-safe if done here
                            # It's safer to do it after all uploads are complete.
                        except Exception as exc:
                            logger.error(f"Error uploading {file_data['hashed_filename']}: {exc}")
                            # Optionally, handle failed uploads
                        else:
                            _update_progress()

                # Now that all files are uploaded, build the gallery_data structure (this is safer)
                for file_data in files_to_upload:
                    node = self._get_or_create_node(gallery_data, file_data['zip_internal_path'])
                    node['images'].append({
                        "filename": file_data['hashed_filename'],
                        "modification_date": file_data['mod_date'],
                        "full_path": file_data['hashed_filename']
                    })

        except zipfile.BadZipFile:
            logger.error("Uploaded file is not a valid zip file.")
            UploadService._upload_progress[gallery_name] = -1
            return None
        except Exception as e:
            logger.error(f"Error processing zip file: {e}")
            UploadService._upload_progress[gallery_name] = -1
            return None
        
        if self.socketio:
            UploadService._upload_progress[gallery_name] = 100
            self.socketio.emit('upload_progress', {'progress': 100})

        return gallery_data

    @classmethod
    def get_upload_progress(cls, gallery_name):
        return cls._upload_progress.get(gallery_name)


    def _get_or_create_node(self, root_node, path):
        if not path or path == '.':
            return root_node

        parts = path.split('/')
        # Often, zips have a single root folder. We can choose to ignore it.
        if len(parts) > 0 and parts[0] == root_node.get('name'):
             parts = parts[1:]

        node = root_node
        current_path_parts = []
        for part in parts:
            current_path_parts.append(part)
            found = False
            for child in node["children"]:
                if child["name"] == part:
                    node = child
                    found = True
                    break
            if not found:
                new_node = {
                    "name": part, 
                    "full_path": "/".join(current_path_parts),
                    "images": [], 
                    "comment": "", 
                    "children": []
                }
                node["children"].append(new_node)
                node = new_node
        return node