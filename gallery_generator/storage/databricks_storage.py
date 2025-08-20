import os
import requests
from dotenv import load_dotenv
from .storage import Storage

load_dotenv()

class DatabricksStorage(Storage):
    """
    Storage implementation for interacting with Databricks Volumes via the REST API.
    """

    def __init__(self):
        self.instance = os.getenv("DATABRICKS_INSTANCE", "").rstrip('/')
        self.token = os.getenv("DATABRICKS_TOKEN")
        self.volume_path = f"/Volumes/{os.getenv('DATABRICKS_CATALOG')}/{os.getenv('DATABRICKS_SCHEMA')}/{os.getenv('DATABRICKS_VOLUME')}"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def _get_api_url(self, file_path: str) -> str:
        """Constructs the full API URL for a given file path."""
        # Normalize path separators for URL
        safe_path = file_path.replace("\\", "/")
        return f"{self.instance}/api/2.0/fs/files{self.volume_path}/{safe_path}"

    def save(self, file_path: str, data: bytes):
        """
        Saves data to a file in the Databricks Volume.
        """
        # Create parent directories first
        self.create_directories(os.path.dirname(file_path))
        
        api_url = self._get_api_url(file_path)
        response = requests.put(
            api_url,
            headers=self.headers,
            data=data,
            params={"overwrite": "true"}
        )
        response.raise_for_status()

    def load(self, file_path: str) -> bytes:
        """
        Loads data from a file in the Databricks Volume.
        """
        api_url = self._get_api_url(file_path)
        response = requests.get(api_url, headers=self.headers)
        response.raise_for_status()
        return response.content

    def delete(self, file_path: str):
        """
        Deletes a file from the Databricks Volume.
        """
        api_url = self._get_api_url(file_path)
        response = requests.delete(api_url, headers=self.headers)
        # Ignore 404 errors on deletion, as the file might already be gone
        if response.status_code != 404:
            response.raise_for_status()

    def list_files(self, directory_path: str) -> list[str]:
        """
        Lists files in a directory within the Databricks Volume.
        """
        safe_dir_path = directory_path.replace("\\", "/")
        api_url = f"{self.instance}/api/2.0/fs/directories{self.volume_path}/{safe_dir_path}"
        response = requests.get(api_url, headers=self.headers)
        if response.status_code == 404:
            return [] # Directory not found, return empty list
        response.raise_for_status()
        return [item['path'].split('/')[-1] for item in response.json().get('files', [])]

    def exists(self, file_path: str) -> bool:
        """
        Checks if a file exists in the Databricks Volume.
        """
        api_url = self._get_api_url(file_path)
        response = requests.get(api_url, headers=self.headers)
        return response.status_code == 200

    def create_directories(self, directory_path: str):
        """
        Recursively creates directories in the Databricks Volume.
        """
        if not directory_path:
            return

        # Correctly handle backslashes from Windows paths and split
        parts = directory_path.replace("\\", "/").split('/')
        current_path = ""
        for part in parts:
            if not part:
                continue
            current_path = f"{current_path}/{part}" if current_path else part
            dir_api_url = f"{self.instance}/api/2.0/fs/directories{self.volume_path}/{current_path}"
            
            # Check if directory exists before creating
            check_response = requests.get(dir_api_url, headers=self.headers)
            if check_response.status_code == 404:
                try:
                    response = requests.put(dir_api_url, headers=self.headers)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    # Ignore conflict errors if the directory was created by another process
                    # between our check and our put call (race condition).
                    if e.response.status_code != 409:
                        raise
