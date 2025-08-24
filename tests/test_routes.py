import pytest
import shutil
from gallery_generator.app import create_app
from gallery_generator.services.data_manager import DataManager
import os
import json

@pytest.fixture
def client(tmp_path):
    # Reset the ConfigManager singleton before each test
    from gallery_generator.config_manager import ConfigManager
    ConfigManager._reset_instance()

    gallery_root = tmp_path / "gallery_data"
    gallery_root.mkdir()
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    gallery_data_path = gallery_root / "gallery_data.json"

    # Create a ConfigManager instance for the test
    test_config_manager = ConfigManager()
    test_config_manager.config['GALLERY_ROOT'] = str(gallery_root)
    test_config_manager.config['BACKUP_DIR'] = str(backup_dir)
    test_config_manager.config['GALLERY_DATA_FILE'] = str(gallery_data_path)

    app = create_app(config_manager_instance=test_config_manager)
    app.config['TESTING'] = True

    # Create a dummy gallery_data.json for testing
    dummy_data = {
        "name": "root",
        "images": [],
        "comment": "",
        "children": [
            {
                "name": "TestFolder",
                "images": [
                    {
                        "filename": "test_image.jpg",
                        "modification_date": "2023-01-01"
                    }
                ],
                "comment": "A test comment",
                "children": []
            }
        ]
    }
    with open(gallery_data_path, 'w', encoding='utf-8') as f:
        json.dump(dummy_data, f, indent=4)

    # Create a dummy image file
    test_folder = gallery_root / "TestFolder"
    test_folder.mkdir()
    with open(test_folder / "test_image.jpg", "w") as f:
        f.write("dummy image data")

    with app.test_client() as client:
        yield client

def test_index_page(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"Photo Gallery" in rv.data

    # Now test the API endpoint that gallery.js would call
    api_rv = client.get('/api/gallery_data')
    assert api_rv.status_code == 200
    data = json.loads(api_rv.data)
    
    assert data['children'][0]['name'] == 'TestFolder'
    assert data['children'][0]['images'][0]['filename'] == 'test_image.jpg'

# You would add more tests here for other routes (upload, delete, comments, versions)

def test_export_report(client):
    # Test HTML export
    rv = client.post('/export_report', json={'format': 'html', 'gallery_data': {'name': 'root', 'children': []}} )
    assert rv.status_code == 200
    assert rv.mimetype == 'text/html'
    assert 'attachment; filename=report.html' in rv.headers['Content-Disposition']

    # Test Markdown export
    rv = client.post('/export_report', json={'format': 'markdown', 'gallery_data': {'name': 'root', 'children': []}} )
    assert rv.status_code == 200
    assert rv.mimetype == 'text/markdown'
    assert 'attachment; filename=report.md' in rv.headers['Content-Disposition']

    # Test invalid format
    rv = client.post('/export_report', json={'format': 'invalid', 'gallery_data': {'name': 'root', 'children': []}} )
    assert rv.status_code == 400
    assert b'Invalid format specified' in rv.data
