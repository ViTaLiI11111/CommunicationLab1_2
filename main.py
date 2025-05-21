import sys
import yaml
import os
from pathlib import Path
import logging

project_root = Path(file).parent
# Вставляємо шлях до lib на початок sys.path
sys.path.insert(0, str(project_root / "lib"))

# Імпортуємо BotEngine (тепер він має бути знайдений)
from bot_lib.bot_engine import BotEngine
# Імпортуємо QuizSingleton для конфігурації
from lib.quiz_lib.quiz import QuizSingleton


# Налаштування логування для головного скрипта
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name)


if name == "main":
    config_files = {
        'database': 'config/database.yml',
        'locales': 'config/locales.yml',
        'secrets': 'config/secrets.yml',
        'questions_dir': 'config/questions',
        # !!! Додано шлях для log_dir !!!
        'log_dir': 'log',
        # !!! Додано шлях для answers_dir !!!
        'answers_dir': 'quiz_answers',
        # Можна додати інші опції Singleton, якщо потрібно
        # 'questions_ext': 'yml',
    }

    try:
        # --- Створюємо необхідні директорії ---
        Path(project_root / config_files['questions_dir']).mkdir(parents=True, exist_ok=True)
        Path(project_root / config_files['log_dir']).mkdir(parents=True, exist_ok=True) # Створюємо log директорію
        Path(project_root / config_files['answers_dir']).mkdir(parents=True, exist_ok=True) # Створюємо quiz_answers директорію

        # ... (логіка створення директорії для SQLite бази даних) ...
        try:
             db_config_path = project_root / config_files['database']
             if db_config_path.exists():
                 with open(db_config_path, 'r', encoding='utf-8') as f:
                     db_config = yaml.safe_load(f)
                     if db_config and db_config.get('adapter') == 'sqlite3':
                         db_file_path_str = db_config.get('database')
                         if db_file_path_str:
                             db_directory = project_root / db_file_path_str # Шлях до файлу
                             db_directory.parent.mkdir(parents=True, exist_ok=True) # Створюємо батьківську директорію
                         else:
                             logger.warning("SQLite database path not specified in config.")
             else:
                 logger.warning(f"Database config file not found at {db_config_path}. Cannot ensure SQLite directory exists.")

        except FileNotFoundError:
             logger.error(f"Database config file not found at {config_files['database']}")
             sys.exit(1)
        except yaml.YAMLError as e:
             logger.error(f"Error parsing database config: {e}")
             sys.exit(1)
        except Exception as e:
            logger.error(f"Error creating database directory: {e}")
            sys.exit(1)


        # --- Конфігуруємо Singleton перед використанням ---
        # Використовуємо екземпляр для налаштування, як в BotEngine
        quiz_singleton_cfg = QuizSingleton()
        quiz_singleton_cfg.yaml_dir = config_files['questions_dir']
        quiz_singleton_cfg.answers_dir = config_files['answers_dir']
        quiz_singleton_cfg.log_dir = config_files['log_dir']
        # quiz_singleton_cfg.in_ext = config_files.get('questions_ext', quiz_singleton_cfg.in_ext)


        logger.info("Initializing BotEngine...")
        bot_engine = BotEngine(config_files) # Передаємо словник зі шляхами
        logger.info("BotEngine initialized. Running...")
        bot_engine.run() # Запускаємо бота

    except Exception as e:
        logger.critical(f"Failed to start the bot: {e}", exc_info=True)
        sys.exit(1)