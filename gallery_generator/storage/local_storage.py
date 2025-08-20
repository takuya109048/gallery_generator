import os
from pathlib import Path
from .storage import Storage

class LocalStorage(Storage):
    """
    A storage implementation for handling files on the local filesystem.
    """

    def __init__(self, base_directory: str = 'gallery_data'):
        """
        Initializes the LocalStorage with a base directory for all file operations.

        Args:
            base_directory (str): The root directory for storing files.
        """
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, file_path: str) -> Path:
        """
        Constructs the full, absolute path for a given file path, ensuring it remains
        within the intended base directory.

        Args:
            file_path (str): The relative path of the file.

        Returns:
            Path: The full, resolved path of the file.
        """
        return self.base_directory.joinpath(file_path).resolve()

    def save(self, file_path: str, data: bytes):
        """
        Saves binary data to a file in the local storage directory.

        Args:
            file_path (str): The relative path where the file will be saved.
            data (bytes): The binary data to store.
        """
        full_path = self._get_full_path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(data)

    def load(self, file_path: str) -> bytes:
        """
        Loads binary data from a file in the local storage directory.

        Args:
            file_path (str): The relative path of the file to load.

        Returns:
            bytes: The binary data from the file.
        """
        full_path = self._get_full_path(file_path)
        with open(full_path, 'rb') as f:
            return f.read()

    def delete(self, file_path: str):
        """
        Deletes a file from the local storage directory.

        Args:
            file_path (str): The relative path of the file to delete.
        """
        full_path = self._get_full_path(file_path)
        if full_path.exists() and full_path.is_file():
            os.remove(full_path)

    def list_files(self, directory_path: str) -> list[str]:
        """
        Lists all files in a specified directory within the local storage.

        Args:
            directory_path (str): The relative path of the directory.

        Returns:
            list[str]: A list of filenames in the directory.
        """
        full_path = self._get_full_path(directory_path)
        if full_path.exists() and full_path.is_dir():
            return [f.name for f in full_path.iterdir() if f.is_file()]
        return []

    def exists(self, file_path: str) -> bool:
        """
        Checks if a file exists in the local storage directory.

        Args:
            file_path (str): The relative path of the file.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        full_path = self._get_full_path(file_path)
        return full_path.exists() and full_path.is_file()
