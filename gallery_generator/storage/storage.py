from abc import ABC, abstractmethod

class Storage(ABC):
    """
    A storage interface for managing files, providing a common structure
    for different storage backends like local or cloud-based systems.
    """

    @abstractmethod
    def save(self, file_path: str, data: bytes):
        """
        Saves data to a specified file path.

        Args:
            file_path (str): The path where the file will be saved.
            data (bytes): The binary data to be stored.
        """
        pass

    @abstractmethod
    def load(self, file_path: str) -> bytes:
        """
        Loads data from a specified file path.

        Args:
            file_path (str): The path of the file to be loaded.

        Returns:
            bytes: The binary data from the file.
        """
        pass

    @abstractmethod
    def delete(self, file_path: str):
        """
        Deletes a file from a specified path.

        Args:
            file_path (str): The path of the file to be deleted.
        """
        pass

    @abstractmethod
    def list_files(self, directory_path: str) -> list[str]:
        """
        Lists all files in a specified directory.

        Args:
            directory_path (str): The path of the directory to be listed.

        Returns:
            list[str]: A list of filenames in the directory.
        """
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        Checks if a file exists at a specified path.

        Args:
            file_path (str): The path of the file to be checked.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        pass