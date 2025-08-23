import json
import os
from datetime import datetime
import pytz # Import pytz for timezone handling
from gallery_generator.storage.storage import Storage # Import Storage interface
from typing import Dict, Any

class DataManager:
    def __init__(self, base_dir: str, config_manager: Any, storage: Storage):
        self.base_dir = base_dir
        self.config_manager = config_manager
        self.storage = storage
        
        if self.base_dir: # If base_dir is provided (e.g., 'gallery_data' for Databricks)
            self.backup_base_dir = os.path.join(self.base_dir, 'backups')
        else: # If base_dir is empty (e.g., for LocalStorage, where LocalStorage handles the absolute path)
            self.backup_base_dir = 'backups' # Relative to the LocalStorage's base_directory
        # os.makedirs(self.backup_base_dir, exist_ok=True) # Handled by storage implementation

    def _get_gallery_data_path(self, gallery_name: str) -> str:
        gallery_dir = os.path.join(self.base_dir, gallery_name)
        # os.makedirs(gallery_dir, exist_ok=True) # Handled by storage implementation
        return os.path.join(gallery_dir, 'gallery_data.json')

    def _get_backup_dir_for_gallery(self, gallery_name: str) -> str:
        backup_dir = os.path.join(self.backup_base_dir, gallery_name)
        # os.makedirs(backup_dir, exist_ok=True) # Handled by storage implementation
        return backup_dir

    def load_gallery_data(self, gallery_name: str) -> Dict[str, Any]:
        gallery_data_path = self._get_gallery_data_path(gallery_name)
        try:
            if self.storage.exists(gallery_data_path):
                data_bytes = self.storage.load(gallery_data_path)
                return json.loads(data_bytes.decode('utf-8'))
            return {}
        except FileNotFoundError:
            return {} # Return empty if file not found
        except Exception as e:
            # Log the error for debugging
            print(f"Error loading gallery data from {gallery_data_path}: {e}")
            return {}

    def save_gallery_data(self, data: Dict[str, Any], gallery_name: str):
        gallery_data_path = self._get_gallery_data_path(gallery_name)
        backup_dir = self._get_backup_dir_for_gallery(gallery_name)

        # Backup current gallery_data.json before saving new data
        if self.storage.exists(gallery_data_path):
            try:
                old_data_bytes = self.storage.load(gallery_data_path)
                old_data = json.loads(old_data_bytes.decode('utf-8'))
                
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                backup_filename = f"gallery_data_{timestamp}.json"
                backup_filepath = os.path.join(backup_dir, backup_filename)
                
                self.storage.save(backup_filepath, json.dumps(old_data, ensure_ascii=False, indent=4).encode('utf-8'))
            except FileNotFoundError:
                pass # No existing file to backup
            except Exception as e:
                print(f"Error backing up gallery data from {gallery_data_path}: {e}")

        self.storage.save(gallery_data_path, json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))

    def get_backup_versions(self, gallery_name: str) -> list[Dict[str, Any]]:
        backup_files = []
        jst = pytz.timezone('Asia/Tokyo')
        backup_dir = self._get_backup_dir_for_gallery(gallery_name)

        # Ensure the backup directory exists before listing files
        # The storage implementation should handle creating the directory if it doesn't exist
        # when saving, but for listing, we need to check if it's there.
        if not self.storage.exists(backup_dir): # Check if the directory exists
            return [] # Return empty list if backup directory doesn't exist

        for filename in self.storage.list_files(backup_dir):
            if filename.startswith('gallery_data_') and filename.endswith('.json'):
                try:
                    timestamp_str = filename.replace('gallery_data_', '').replace('.json', '')
                    dt_object_utc = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S').replace(tzinfo=pytz.utc)

                    dt_object_jst = dt_object_utc.astimezone(jst)
                    display_timestamp = dt_object_jst.strftime('%Y/%m/%d %H:%M:%S JST')

                    backup_files.append({
                        'filename': filename,
                        'timestamp': dt_object_utc.timestamp(),
                        'display_timestamp': display_timestamp
                    })
                except ValueError:
                    continue
        backup_files.sort(key=lambda x: x['timestamp'], reverse=True)
        return backup_files

    def revert_to_version(self, filename: str, gallery_name: str) -> bool:
        backup_filepath = os.path.join(self._get_backup_dir_for_gallery(gallery_name), filename)
        gallery_data_path = self._get_gallery_data_path(gallery_name)
        
        if self.storage.exists(backup_filepath):
            try:
                data_bytes = self.storage.load(backup_filepath)
                data = json.loads(data_bytes.decode('utf-8'))
                self.storage.save(gallery_data_path, json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))
                return True
            except Exception as e:
                print(f"Error reverting to version {filename}: {e}")
                return False
        return False

    def read_backup(self, filename: str, gallery_name: str) -> Dict[str, Any] | None:
        backup_filepath = os.path.join(self._get_backup_dir_for_gallery(gallery_name), filename)
        if self.storage.exists(backup_filepath):
            try:
                data_bytes = self.storage.load(backup_filepath)
                return json.loads(data_bytes.decode('utf-8'))
            except Exception as e:
                print(f"Error reading backup {filename}: {e}")
                return None
        return None

    def _find_node_by_path(self, data: Dict[str, Any], path_parts: list[str]) -> Dict[str, Any] | None:
        if not path_parts:
            return data

        current_node = data
        for part in path_parts:
            found = False
            if 'children' in current_node:
                for child in current_node['children']:
                    if child['name'] == part:
                        current_node = child
                        found = True
                        break
            if not found:
                return None
        return current_node

    def update_comment(self, path: str, comment: str, gallery_name: str) -> bool:
        gallery_data = self.load_gallery_data(gallery_name)
        if not gallery_data:
            return False

        path_parts = path.strip('/').split('/') if path else []

        node = self._find_node_by_path(gallery_data, path_parts)
        if node:
            node['comment'] = comment
            self.save_gallery_data(gallery_data, gallery_name)
            return True
        return False

    def update_image_status(self, image_paths: list[str], status: str, gallery_name: str) -> bool:
        gallery_data = self.load_gallery_data(gallery_name)
        if not gallery_data:
            return False

        updated = False
        for full_image_path in image_paths:
            parts = full_image_path.strip('/').split('/')
            image_filename = parts[-1]
            dir_path_parts = parts[:-1]

            node = self._find_node_by_path(gallery_data, dir_path_parts)
            if node and 'images' in node:
                for image in node['images']:
                    if image['filename'] == image_filename:
                        image['status'] = status
                        updated = True
                        break
        
        if updated:
            self.save_gallery_data(gallery_data, gallery_name)
            return True
        return False