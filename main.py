import sys
import yaml
import os
from pathlib import Path
import logging

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "lib"))

from bot_lib.bot_engine import BotEngine
from lib.quiz_lib.quiz import QuizSingleton


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


if __name__ == "__main__":

    config_files = {
        'database': 'config/database.yml',
        'locales': 'config/locales.yml',
        'secrets': 'config/secrets.yml',
        'questions_dir': 'config/questions',
        'log_dir': 'log',
        'answers_dir': 'quiz_answers',
    }

    try:
        Path(project_root / config_files['questions_dir']).mkdir(parents=True, exist_ok=True)
        Path(project_root / config_files['log_dir']).mkdir(parents=True, exist_ok=True)
        Path(project_root / config_files['answers_dir']).mkdir(parents=True, exist_ok=True)

        try:
             db_config_path = project_root / config_files['database']
             if db_config_path.exists():
                 with open(db_config_path, 'r', encoding='utf-8') as f:
                     db_config = yaml.safe_load(f)
                     if db_config and db_config.get('adapter') == 'sqlite3':
                         db_file_path_str = db_config.get('database')
                         if db_file_path_str:
                             db_directory = project_root / Path(db_file_path_str).parent
                             db_directory.mkdir(parents=True, exist_ok=True)
                         else:
                             logger.warning("SQLite database path not specified in config/database.yml")
             else:
                 logger.warning(f"Database config file not found at {db_config_path}. Cannot ensure SQLite directory exists based on config.")

        except FileNotFoundError:
             logger.error(f"Database config file not found at {config_files['database']}")
             sys.exit(1)
        except yaml.YAMLError as e:
             logger.error(f"Error parsing database config: {e}")
             sys.exit(1)
        except Exception as e:
            logger.error(f"Error ensuring database directory exists: {e}")
            sys.exit(1)

        logger.info("Configuring QuizSingleton...")
        quiz_singleton_cfg = QuizSingleton()
        quiz_singleton_cfg.yaml_dir = config_files['questions_dir']
        quiz_singleton_cfg.answers_dir = config_files['answers_dir']
        quiz_singleton_cfg.log_dir = config_files['log_dir']
        quiz_singleton_cfg.in_ext = config_files.get('questions_ext', 'yml')

        if not quiz_singleton_cfg.is_configured():
             logger.critical("QuizSingleton was not properly configured.")
             sys.exit(1)

        logger.info(f"QuizSingleton configured: {quiz_singleton_cfg}")

        logger.info("Initializing BotEngine...")
        bot_engine = BotEngine(config_files)
        logger.info("BotEngine initialized. Running...")
        bot_engine.run()

    except Exception as e:
        logger.critical(f"Failed to start the bot: {e}", exc_info=True)
        sys.exit(1)