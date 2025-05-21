import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(project_root))

from lib.bot_lib.db_connector import DatabaseConnector
from lib.bot_lib.models import Base

DATABASE_CONFIG_PATH = project_root / "config" / "database.yml"

def apply_migration():
    print("Applying migration: Create Users table...")
    db_connector = DatabaseConnector(config_path=str(DATABASE_CONFIG_PATH))

    if db_connector.engine:
        try:
            Base.metadata.create_all(bind=db_connector.engine)
            print("Migration 001_create_users applied successfully.")
        except Exception as e:
            print(f"Error applying migration: {e}")
    else:
        print("Database connection failed. Cannot apply migration.")

if __name__ == "__main__":
    apply_migration()