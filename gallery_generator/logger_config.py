import logging
import os
from gallery_generator.config_manager import ConfigManager

def setup_logging():
    config = ConfigManager()
    log_file = config.get('LOG_FILE', 'app.log')

    # Ensure the log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Example usage:
    # logger = logging.getLogger(__name__)
    # logger.info("Logging setup complete.")
