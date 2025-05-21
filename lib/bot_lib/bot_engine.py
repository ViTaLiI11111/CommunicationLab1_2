from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv
import os

from .message_handler import start_command, stop_command, command_c, handle_answer_callback, HandlerDependencies
from .db_connector import DatabaseConnector
from .localization import Localization
from lib.quiz_lib.question_data import QuestionData
from lib.quiz_lib.quiz import QuizSingleton 


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotEngine:
    def __init__(self, config_paths):
        self.config_paths = config_paths

        self._configure_quiz_singleton()

        self._load_config() 
        self._setup_dependencies()
        self._setup_application()
        self._register_handlers()


    def _configure_quiz_singleton(self):
        """Налаштовує Singleton конфігурації quiz_lib."""
        quiz_cfg = QuizSingleton()
        quiz_cfg.yaml_dir = self.config_paths.get('questions_dir', quiz_cfg.yaml_dir)
        quiz_cfg.answers_dir = self.config_paths.get('answers_dir', quiz_cfg.answers_dir)
        quiz_cfg.in_ext = self.config_paths.get('questions_ext', quiz_cfg.in_ext)
        quiz_cfg.log_dir = self.config_paths.get('log_dir', quiz_cfg.log_dir)
       
    def _load_config(self):
        """Завантажує конфігурації, включаючи токен бота."""
        try:
            project_root = Path(__file__).parent.parent.parent
            secrets_path = project_root / self.config_paths.get('secrets', 'config/secrets.yml')
            secrets_data = self._load_secrets_from_path(secrets_path)
            self.token = secrets_data.get('telegram_bot_token')


            if not self.token:
                logger.critical("Telegram bot token not found in secrets.yml or .env")
                raise ValueError("Telegram bot token is missing.")

        except Exception as e:
             logger.critical(f"Failed to load bot token: {e}", exc_info=True)
             raise
            
    def _load_secrets_from_path(self, secrets_path):
         """Внутрішній метод для завантаження секретів."""
         try:
             project_root = Path(__file__).parent.parent.parent
             filepath = project_root / secrets_path
             if filepath.exists():
                 with open(filepath, 'r', encoding='utf-8') as f:
                     return yaml.safe_load(f)
             elif (filepath.parent / ".env").exists():
                  load_dotenv(dotenv_path=filepath.parent / ".env")
                  return {
                      'db_password': os.getenv("DB_PASSWORD"),
                      'telegram_bot_token': os.getenv("TELEGRAM_BOT_TOKEN")
                  }
             else:
                 return {}

         except yaml.YAMLError as e:
             logger.error(f"Error parsing secrets file: {e}")
             return {} 
         except Exception as e:
             logger.error(f"Failed to load secrets from {secrets_path}: {e}")
             return {} 


    def _setup_dependencies(self):
        """Ініціалізує залежності (БД, локалізація, дані питань)."""
        db_config_path = self.config_paths.get('database', 'config/database.yml')
        secrets_config_path = self.config_paths.get('secrets', 'config/secrets.yml')
        self.db_connector = DatabaseConnector(config_path=db_config_path, secrets_path=secrets_config_path)

        self.db_connector.create_tables()

        locales_config_path = self.config_paths.get('locales', 'config/locales.yml')
        self.localization = Localization(locales_path=locales_config_path)

        self.question_data = QuestionData()
        if not self.question_data.collection:
             logger.critical("No questions loaded. Quiz will not function.")
             raise SystemExit("No questions loaded.")

        try:
            self.question_data.save_to_json()
            logger.info(f"Questions data saved to {QuizSingleton().log_dir}/testing.json")
        except Exception as e:
            logger.error(f"Failed to save questions data to JSON: {e}", exc_info=True)

        try:
            self.question_data.save_to_yaml()
            logger.info(f"Questions data saved to {QuizSingleton().log_dir}/testing.yml")
        except Exception as e:
            logger.error(f"Failed to save questions data to YAML: {e}", exc_info=True)


        self.handler_deps = HandlerDependencies(
             db_connector=self.db_connector,
             question_data=self.question_data,
             localization=self.localization
        )


    def _setup_application(self):
       if not self.token:
            raise ValueError("Bot token is not available.")
       self.application = Application.builder().token(self.token).build()
       logger.info("Telegram bot application built.")


    def _register_handlers(self):
        if not self.application or not self.handler_deps:
             logger.error("Cannot register handlers, application or dependencies missing.")
             return

        self.application.add_handler(CommandHandler("start", lambda update, context: start_command(update, context, self.handler_deps)))
        self.application.add_handler(CommandHandler("stop", lambda update, context: stop_command(update, context, self.handler_deps)))
        self.application.add_handler(CommandHandler("c", lambda update, context: command_c(update, context, self.handler_deps)))

        self.application.add_handler(CallbackQueryHandler(lambda update, context: handle_answer_callback(update, context, self.handler_deps)))

        logger.info("Bot handlers registered.")


    def run(self):
        if not self.application:
             logger.critical("Bot application not initialized. Cannot start polling.")
             return

        logger.info("Starting bot polling...")
        self.application.run_polling(poll_interval=3)
        logger.info("Bot polling stopped.")
