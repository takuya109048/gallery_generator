import json
import logging
from datetime import datetime
from ..storage.storage import Storage # Import the abstract base class

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, storage: Storage):
        """
        Initializes the DataManager with a storage backend.

        Args:
            storage (Storage): An object that implements the Storage interface.
        """
        self.storage = storage
        self.gallery_data_filename = 'gallery_data.json'
        self.backups_dirname = 'backups'

    def _get_gallery_path(self, gallery_name: str) -> str:
        return f"{gallery_name}/{self.gallery_data_filename}"

    def _get_backup_dir_path(self, gallery_name: str) -> str:
        return f"{self.backups_dirname}/{gallery_name}"

    def read_gallery_data(self, gallery_name: str) -> dict:
        gallery_path = self._get_gallery_path(gallery_name)
        if self.storage.exists(gallery_path):
            try:
                data = self.storage.load(gallery_path)
                gallery_data = json.loads(data.decode('utf-8'))
                self._ensure_image_status(gallery_data) # Ensure all images have a status
                self._sort_gallery_data(gallery_data)
                return gallery_data
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Error decoding JSON from {gallery_path}: {e}")
                return None
        # Initialize with default status for new galleries
        return {"name": "root", "images": [], "comment": "", "children": []}

    def _ensure_image_status(self, node: dict):
        """Recursively ensures all images have a 'status' field, defaulting to 'neutral'."""
        if 'images' in node and isinstance(node['images'], list):
            for image in node['images']:
                if 'status' not in image:
                    image['status'] = 'neutral'
        if 'children' in node and isinstance(node['children'], list):
            for child in node['children']:
                self._ensure_image_status(child)

    def _sort_gallery_data(self, node: dict):
        if 'images' in node and isinstance(node['images'], list):
            node['images'].sort(key=lambda x: x.get('filename', '').lower())
        if 'children' in node and isinstance(node['children'], list):
            node['children'].sort(key=lambda x: x.get('name', '').lower())
            for child in node['children']:
                self._sort_gallery_data(child)

    def write_gallery_data(self, data: dict, gallery_name: str) -> bool:
        gallery_path = self._get_gallery_path(gallery_name)
        self._create_backup(gallery_name)
        try:
            json_data = json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')
            self.storage.save(gallery_path, json_data)
            logger.info(f"Successfully wrote gallery data to {gallery_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing gallery data to {gallery_path}: {e}")
            return False

    def _create_backup(self, gallery_name: str):
        gallery_path = self._get_gallery_path(gallery_name)
        if self.storage.exists(gallery_path):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_filename = f"gallery_data_{timestamp}.json"
            backup_path = f"{self._get_backup_dir_path(gallery_name)}/{backup_filename}"
            try:
                data_to_backup = self.storage.load(gallery_path)
                self.storage.save(backup_path, data_to_backup)
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.error(f"Error creating backup for {gallery_path}: {e}")

    def list_backups(self, gallery_name: str) -> list:
        backup_dir = self._get_backup_dir_path(gallery_name)
        try:
            backup_files = self.storage.list_files(backup_dir)
        except Exception as e:
            logger.warning(f"Could not list backups for {gallery_name}, directory may not exist. Error: {e}")
            return []

        backups = []
        for filename in backup_files:
            if filename.startswith('gallery_data_') and filename.endswith('.json'):
                try:
                    timestamp_str = filename.replace('gallery_data_', '').replace('.json', '')
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                    backups.append({'filename': filename, 'timestamp': timestamp})
                except ValueError:
                    logger.warning(f"Could not parse timestamp from backup file: {filename}")
        
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups

    def read_backup(self, filename: str, gallery_name: str) -> dict | None:
        backup_path = f"{self._get_backup_dir_path(gallery_name)}/{filename}"
        if self.storage.exists(backup_path):
            try:
                data = self.storage.load(backup_path)
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Error decoding JSON from backup {backup_path}: {e}")
                return None
        return None

    def revert_to_version(self, filename: str, gallery_name: str) -> bool:
        backup_path = f"{self._get_backup_dir_path(gallery_name)}/{filename}"
        gallery_path = self._get_gallery_path(gallery_name)
        if self.storage.exists(backup_path):
            try:
                data_to_revert = self.storage.load(backup_path)
                self.storage.save(gallery_path, data_to_revert)
                logger.info(f"Reverted gallery data to version: {filename}")
                return True
            except Exception as e:
                logger.error(f"Error reverting to version {filename}: {e}")
                return False
        logger.warning(f"Backup file not found for reversion: {filename}")
        return False

    def update_comment(self, path: str, comment: str, gallery_name: str) -> bool:
        gallery_data = self.read_gallery_data(gallery_name)
        if not gallery_data:
            logger.error("Failed to read gallery data for comment update.")
            return False

        node = self._find_node_by_path(gallery_data, path)

        if node:
            node['comment'] = comment
            return self.write_gallery_data(gallery_data, gallery_name)
        else:
            logger.error(f"Node not found for path: {path}")
            return False

    def update_image_status(self, image_paths: list[str], status: str, gallery_name: str) -> bool:
        gallery_data = self.read_gallery_data(gallery_name)
        if not gallery_data:
            logger.error("Failed to read gallery data for image status update.")
            return False

        updated = False
        def _traverse_and_update(node):
            nonlocal updated
            if 'images' in node and isinstance(node['images'], list):
                for image in node['images']:
                    if image.get('full_path') in image_paths:
                        image['status'] = status
                        updated = True
            if 'children' in node and isinstance(node['children'], list):
                for child in node['children']:
                    _traverse_and_update(child)

        _traverse_and_update(gallery_data)

        if updated:
            return self.write_gallery_data(gallery_data, gallery_name)
        else:
            logger.warning("No images found matching the provided paths for status update.")
            return False

    def _find_node_by_path(self, current_node: dict, path: str) -> dict | None:
        path_parts = path.split('/') if path else []

        def find(node, parts):
            if not parts:
                return node
            
            head, *tail = parts
            for child in node.get('children', []):
                if child.get('name') == head:
                    return find(child, tail)
            return None

        if not path_parts:
            return current_node
        return find(current_node, path_parts)
