import json
import os
from datetime import datetime
import pytz # Import pytz for timezone handling

class DataManager:
    def __init__(self, base_dir, config_manager):
        self.base_dir = base_dir
        self.config_manager = config_manager
        self.gallery_data_path = os.path.join(base_dir, 'gallery_data.json')
        self.backup_dir = os.path.join(base_dir, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)

    def load_gallery_data(self):
        if os.path.exists(self.gallery_data_path):
            with open(self.gallery_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_gallery_data(self, data):
        # Backup current gallery_data.json before saving new data
        if os.path.exists(self.gallery_data_path):
            # Use UTC for backup timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            backup_filename = f"gallery_data_{timestamp}.json"
            backup_filepath = os.path.join(self.backup_dir, backup_filename)
            with open(self.gallery_data_path, 'r', encoding='utf-8') as f_old:
                old_data = json.load(f_old)
            with open(backup_filepath, 'w', encoding='utf-8') as f_new:
                json.dump(old_data, f_new, ensure_ascii=False, indent=4)

        with open(self.gallery_data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_backup_versions(self):
        backup_files = []
        # Define JST timezone
        jst = pytz.timezone('Asia/Tokyo')

        for filename in os.listdir(self.backup_dir):
            if filename.startswith('gallery_data_') and filename.endswith('.json'):
                try:
                    # Extract timestamp and convert to datetime object, assuming it's UTC
                    timestamp_str = filename.replace('gallery_data_', '').replace('.json', '')
                    dt_object_utc = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S').replace(tzinfo=pytz.utc)

                    # Convert UTC datetime object to JST for display
                    dt_object_jst = dt_object_utc.astimezone(jst)
                    display_timestamp = dt_object_jst.strftime('%Y/%m/%d %H:%M:%S JST')

                    backup_files.append({
                        'filename': filename,
                        'timestamp': dt_object_utc.timestamp(), # Keep UTC timestamp for sorting/internal logic
                        'display_timestamp': display_timestamp # JST for display in frontend
                    })
                except ValueError:
                    # Skip files that do not match the expected timestamp format
                    continue
        # Sort by timestamp, newest first
        backup_files.sort(key=lambda x: x['timestamp'], reverse=True)
        return backup_files

    def revert_to_version(self, filename):
        backup_filepath = os.path.join(self.backup_dir, filename)
        if os.path.exists(backup_filepath):
            with open(backup_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            with open(self.gallery_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        return False

    def read_backup(self, filename):
        backup_filepath = os.path.join(self.backup_dir, filename)
        if os.path.exists(backup_filepath):
            with open(backup_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _find_node_by_path(self, data, path_parts):
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
                return None # Path not found
        return current_node

    def update_comment(self, path, comment):
        gallery_data = self.load_gallery_data()
        if not gallery_data:
            return False

        # Split the path into parts (e.g., 'ParentFolder/SubFolder' -> ['ParentFolder', 'SubFolder'])
        path_parts = path.strip('/').split('/') if path else []

        node = self._find_node_by_path(gallery_data, path_parts)
        if node:
            node['comment'] = comment
            self.save_gallery_data(gallery_data)
            return True
        return False

    def update_image_status(self, image_paths, status):
        gallery_data = self.load_gallery_data()
        if not gallery_data:
            return False

        updated = False
        for full_image_path in image_paths:
            # Assuming full_image_path is like 'ParentFolder/SubFolder/Image.jpg'
            parts = full_image_path.strip('/').split('/')
            image_filename = parts[-1]
            dir_path_parts = parts[:-1]

            node = self._find_node_by_path(gallery_data, dir_path_parts)
            if node and 'images' in node:
                for image in node['images']:
                    if image['filename'] == image_filename:
                        image['status'] = status # Add or update status field
                        updated = True
                        break
        
        if updated:
            self.save_gallery_data(gallery_data)
            return True
        return False
