import os
import zipfile
import hashlib
from datetime import datetime
from ..storage.storage import Storage
import logging

logger = logging.getLogger(__name__)

class UploadService:
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
        gallery_data = {"name": "root", "images": [], "comment": "", "children": []}
        
        try:
            with zipfile.ZipFile(zip_file_stream, 'r') as zip_ref:
                # Get total number of processable files for progress calculation
                file_members = [m for m in zip_ref.infolist() if not m.is_dir() and os.path.splitext(os.path.basename(m.filename))[1].lower() in self.allowed_extensions]
                total_files = len(file_members)
                if total_files == 0:
                    logger.warning("No processable image files found in the zip.")
                    # You might want to return a specific message to the user
                    return gallery_data # or None, depending on desired behavior

                processed_files = 0

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
                        self.storage.save(storage_path, file_content)
                        
                        node = self._get_or_create_node(gallery_data, zip_internal_path)
                        node['images'].append({
                            "filename": hashed_filename,
                            "modification_date": mod_date,
                            "full_path": hashed_filename
                        })

                    processed_files += 1
                    if self.socketio:
                        progress = (processed_files / total_files) * 100
                        self.socketio.emit('upload_progress', {'progress': progress})
                        self.socketio.sleep(0.01) # Allow time for the message to be sent

        except zipfile.BadZipFile:
            logger.error("Uploaded file is not a valid zip file.")
            return None
        except Exception as e:
            logger.error(f"Error processing zip file: {e}")
            return None
        
        if self.socketio:
            self.socketio.emit('upload_progress', {'progress': 100})

        return gallery_data


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