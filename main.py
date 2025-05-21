import sys
import yaml
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "lib"))

from bot_lib.bot_engine import BotEngine
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    config_files = {
        'database': 'config/database.yml',
        'locales': 'config/locales.yml',
        'secrets': 'config/secrets.yml',
        'questions_dir': 'config/questions',
    }

    try:
        Path(project_root / config_files['questions_dir']).mkdir(parents=True, exist_ok=True)
        try:
             with open(project_root / config_files['database'], 'r', encoding='utf-8') as f:
                 db_config = yaml.safe_load(f)
                 if db_config and db_config.get('adapter') == 'sqlite3':
                     db_file_path_str = db_config.get('database')
                     if db_file_path_str:
                         db_directory = project_root / db_file_path_str
                         db_directory.parent.mkdir(parents=True, exist_ok=True)
                     else:
                         logger.warning("SQLite database path not specified in config.")

        except FileNotFoundError:
             logger.error(f"Database config file not found at {config_files['database']}")
             sys.exit(1)
        except yaml.YAMLError as e:
             logger.error(f"Error parsing database config: {e}")
             sys.exit(1)
        except Exception as e:
            logger.error(f"Error creating database directory: {e}")
            sys.exit(1)


        logger.info("Initializing BotEngine...")
        bot_engine = BotEngine(config_files)
        logger.info("BotEngine initialized. Running...")
        bot_engine.run()

    except Exception as e:
        logger.critical(f"Failed to start the bot: {e}", exc_info=True)
        sys.exit(1)