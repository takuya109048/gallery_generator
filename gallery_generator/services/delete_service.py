import logging
from ..storage.storage import Storage
from .data_manager import DataManager

logger = logging.getLogger(__name__)

class DeleteService:
    def __init__(self, storage: Storage, data_manager: DataManager):
        """
        Initializes the DeleteService with storage and data_manager objects.
        """
        self.storage = storage
        self.data_manager = data_manager

    def _collect_all_images_in_node(self, node, images_to_delete_in_storage):
        for img in node.get('images', []):
            images_to_delete_in_storage.add(img.get('filename'))
        for child in node.get('children', []):
            self._collect_all_images_in_node(child, images_to_delete_in_storage)

    def delete_items(self, paths_to_delete: list[str], gallery_name: str) -> bool:
        """
        Deletes specified items (images or directories) from the gallery.

        Args:
            paths_to_delete (list[str]): A list of full paths for items to delete.
            gallery_name (str): The name of the gallery.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        current_gallery_data = self.data_manager.load_gallery_data(gallery_name)
        if not current_gallery_data:
            logger.error("No gallery data found for deletion.")
            return False

        images_to_delete_in_storage = set()
        paths_set = set(paths_to_delete)

        def find_and_collect_images(node, paths_to_delete_set):
            # Collect images directly specified for deletion
            for img in node.get('images', []):
                if img.get('full_path') in paths_to_delete_set:
                    images_to_delete_in_storage.add(img.get('filename'))

            # If a directory is marked for deletion, collect all images within it
            if node.get('full_path') in paths_to_delete_set:
                self._collect_all_images_in_node(node, images_to_delete_in_storage)

            for child in node.get('children', []):
                find_and_collect_images(child, paths_to_delete_set)

        find_and_collect_images(current_gallery_data, paths_set)
        
        # Delete image files from storage
        for img_filename in images_to_delete_in_storage:
            try:
                storage_path = f"{gallery_name}/{img_filename}"
                self.storage.delete(storage_path)
                logger.info(f"Deleted from storage: {storage_path}")
            except Exception as e:
                logger.error(f"Error deleting {storage_path} from storage: {e}")

        # This recursive function will remove items from the JSON structure
        def remove_from_json(node, paths_to_delete_set):
            node['images'] = [img for img in node.get('images', []) if img.get('full_path') not in paths_to_delete_set]
            
            new_children = []
            for child in node.get('children', []):
                if child.get('full_path') not in paths_to_delete_set:
                    new_children.append(remove_from_json(child, paths_to_delete_set))
            
            node['children'] = [child for child in new_children if child.get('images') or child.get('children')]
            return node

        # Update the JSON data structure
        updated_gallery_data = remove_from_json(current_gallery_data, paths_set)
        
        return self.data_manager.save_gallery_data(updated_gallery_data, gallery_name)
