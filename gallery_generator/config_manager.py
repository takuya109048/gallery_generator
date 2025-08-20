import json

class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, config_path='config/config.json'):
        if not hasattr(self, 'config'):  # Avoid re-initialization
            with open(config_path, 'r') as f:
                self.config = json.load(f)

    def get(self, key, default=None):
        return self.config.get(key, default)

# Initialize a singleton instance for global access
config_manager = ConfigManager()