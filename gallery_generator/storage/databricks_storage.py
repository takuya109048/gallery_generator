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
        # Construct the full path including the volume path
        full_volume_path = f"{self.volume_path}/{safe_dir_path}"
        
        # The API endpoint for listing contents of a directory in Unity Catalog Volumes
        # is typically /api/2.0/fs/list or /api/2.0/unity-catalog/volumes/{volume_path}/files
        # Given the current usage of /api/2.0/fs/directories, let's assume it's correct
        # for listing contents, but the response parsing might need adjustment.
        
        # The documentation for GET /api/2.0/fs/directories/{path} returns FileInfo objects
        # which have a 'path' field.
        
        api_url = f"{self.instance}/api/2.0/fs/directories{full_volume_path}"
        response = requests.get(api_url, headers=self.headers)
        
        if response.status_code == 404:
            return [] # Directory not found, return empty list
        
        response.raise_for_status()
        
        # The response for /api/2.0/fs/directories is a list of FileInfo objects.
        # Each FileInfo object has a 'path' field which is the full path.
        # We need to extract just the filename.
        
        # Example response:
        # {
        #   "files": [
        #     {
        #       "path": "/Volumes/catalog/schema/volume/dir/file1.txt",
        #       "is_directory": false,
        #       "file_size": 100,
        #       "modification_time": 1678886400000
        #     },
        #     {
        #       "path": "/Volumes/catalog/schema/volume/dir/subdir",
        #       "is_directory": true
        #     }
        #   ]
        # }
        
        # We only want files, not directories, and only their names.
        files_in_dir = []
        for item in response.json().get('files', []):
            if not item.get('is_directory', False): # Only include files
                # Extract filename from the full path
                filename = os.path.basename(item['path'])
                files_in_dir.append(filename)
        return files_in_dir

    def exists(self, file_path: str) -> bool:
        """
        Checks if a file or directory exists in the Databricks Volume.
        """
        safe_path = file_path.replace("\\", "/")
        
        # Check for file existence
        file_api_url = f"{self.instance}/api/2.0/fs/files{self.volume_path}/{safe_path}"
        file_response = requests.get(file_api_url, headers=self.headers)
        if file_response.status_code == 200:
            return True

        # Check for directory existence
        dir_api_url = f"{self.instance}/api/2.0/fs/directories{self.volume_path}/{safe_path}"
        dir_response = requests.get(dir_api_url, headers=self.headers)
        if dir_response.status_code == 200:
            return True
            
        return False

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
