# lib/bot_lib/db_connector.py

import yaml
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
import os
from dotenv import load_dotenv


class DatabaseConnector:
    def __init__(self, config_path="config/database.yml", secrets_path="config/secrets.yml"):
        self.engine = None
        self.SessionLocal = None
        self.config = self._load_config(config_path)
        self.secrets = self._load_secrets(secrets_path)
        self._setup_engine()
        self._setup_session()

    def _load_config(self, config_path):
        try:
            project_root = Path(__file__).parent.parent.parent
            filepath = project_root / config_path
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Database config file not found at {filepath}")
            return None
        except yaml.YAMLError as e:
            print(f"Error parsing database config: {e}")
            return None
        except Exception as e:
             print(f"An unexpected error occurred loading config: {e}")
             return None


    def _load_secrets(self, secrets_path):
         try:
             project_root = Path(__file__).parent.parent.parent
             filepath = project_root / secrets_path
             if filepath.exists():
                 with open(filepath, 'r', encoding='utf-8') as f:
                     return yaml.safe_load(f)
             elif (project_root / ".env").exists():
                  load_dotenv(dotenv_path=project_root / ".env")
                  return {
                      'db_password': os.getenv("DB_PASSWORD"),
                      'telegram_bot_token': os.getenv("TELEGRAM_BOT_TOKEN")
                  }
             else:
                 return {}

         except yaml.YAMLError as e:
             print(f"Error parsing secrets file: {e}")
             return {}
         except Exception as e:
             print(f"Failed to load secrets: {e}")
             return {}


    def _setup_engine(self):
        if not self.config or 'adapter' not in self.config:
            print("Database configuration missing or invalid.")
            return

        adapter = self.config.get('adapter')
        database_path = self.config.get('database')

        if adapter == 'sqlite3' and not database_path:
             print("Error: SQLite database path is not specified in config/database.yml")
             return

        username = None
        password = None
        host = None
        port = None

        if adapter == 'postgresql':
            username = self.config.get('username')
            password = self.secrets.get('db_password') if self.secrets else None
            host = self.config.get('host')
            port = self.config.get('port')
            if not username or not password or not host or not port:
                 print("Warning: PostgreSQL connection details (username, password, host, port) missing.")


        db_url = None
        if adapter == 'postgresql':
            db_url = f"postgresql://{username}:{password}@{host}:{port}/{database_path}"
        elif adapter == 'sqlite3':
            project_root = Path(__file__).parent.parent.parent
            abs_database_path = project_root / database_path
            db_url = f"sqlite:///{abs_database_path}"


        engine_args = {}
        encoding = self.config.get('encoding', 'utf-8')
        pool_size = self.config.get('pool', 5)
        timeout_ms = self.config.get('timeout', 5000)


        if adapter == 'postgresql':
            engine_args = {
                'encoding': encoding,
                'pool_size': pool_size,
                'connect_timeout': timeout_ms / 1000
            }

        elif adapter == 'sqlite3':
            engine_args = {
                 'pool_size': pool_size
            }

            db_directory = Path(abs_database_path).parent
            db_directory.mkdir(parents=True, exist_ok=True)


        if db_url:
            try:
                self.engine = create_engine(db_url, **engine_args)

                if adapter != 'sqlite3':
                     with self.engine.connect() as connection:
                         connection.execute(text("SELECT 1"))
                     print(f"Successfully connected to database: {adapter}")
                else:
                     print(f"Database engine created for SQLite: {database_path}")


            except Exception as e:
                print(f"Error connecting to database: {e}")
                self.engine = None

    def _setup_session(self):
        if self.engine:
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        else:
            self.SessionLocal = None
            print("Cannot setup database session, engine not initialized.")


    def get_session(self) -> Session | None:
        if self.SessionLocal:
            try:
                 return self.SessionLocal()
            except Exception as e:
                 print(f"Error getting database session: {e}")
                 return None
        else:
            print("Cannot get database session, SessionLocal not initialized.")
            return None


    def create_tables(self):
        if self.engine:
            try:
                Base.metadata.create_all(bind=self.engine)
                print("Database tables created (if they didn't exist).")
            except Exception as e:
                print(f"Error creating database tables: {e}")
        else:
            print("Cannot create tables, database engine not initialized.")