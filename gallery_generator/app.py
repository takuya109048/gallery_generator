import os
from flask import Flask
from flask_socketio import SocketIO
from gallery_generator.config_manager import config_manager
from gallery_generator.logger_config import setup_logging
from gallery_generator.storage.local_storage import LocalStorage
from gallery_generator.storage.databricks_storage import DatabricksStorage
from gallery_generator.services.data_manager import DataManager

socketio = SocketIO(async_mode='threading') # Define socketio globally

def create_app(environ=None, start_response=None):
    app = Flask(__name__)

    # Setup logging
    setup_logging()

    # Load configuration
    app.config['CONFIG'] = config_manager

    # Initialize storage based on config
    storage_type = config_manager.get('storage_type')
    if storage_type == 'databricks':
        storage = DatabricksStorage()
        data_manager_base_dir = '' # Empty string for Databricks, as volume_path already includes the base
    else: # Default to local
        local_gallery_data_path = os.path.join(os.path.dirname(app.root_path), 'gallery_data')
        storage = LocalStorage(local_gallery_data_path)
        data_manager_base_dir = '' # LocalStorage handles the absolute path
    
    # Make storage and data_manager accessible
    app.storage = storage
    app.data_manager = DataManager(data_manager_base_dir, config_manager, app.storage)

    # Set a secret key for session management
    app.config['SECRET_KEY'] = 'a_very_secret_key_that_should_be_in_env_or_config' # Replace with a strong, random key in production

    # Set max content length for uploads
    app.config['MAX_CONTENT_LENGTH'] = app.config['CONFIG'].get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024) # Default to 16MB

    # Initialize SocketIO
    socketio.init_app(app)
    app.socketio = socketio # Make socketio accessible via app.socketio

    # Import and register blueprints or routes here later
    from gallery_generator.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app # This return statement must be inside the function

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True)

application = create_app()
