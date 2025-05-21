import asyncio
from telegram import Bot
import logging
import yaml
from pathlib import Path
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_bot_token():
    project_root = Path(__file__).parent
    secrets_path = project_root / "config" / "secrets.yml"

    try:
        if secrets_path.exists():
            with open(secrets_path, 'r', encoding='utf-8') as f:
                secrets = yaml.safe_load(f)
                token = secrets.get('telegram_bot_token')
        elif (project_root / ".env").exists():
             load_dotenv(dotenv_path=project_root / ".env")
             token = os.getenv("TELEGRAM_BOT_TOKEN")
        else:
             token = None
             logger.error("Secrets file not found and no .env file.")

        if not token:
            logger.critical("Telegram bot token not found.")
            raise ValueError("Telegram bot token is missing.")
        return token

    except Exception as e:
        logger.critical(f"Failed to load bot token: {e}", exc_info=True)
        raise

async def main():
    token = load_bot_token()
    if not token:
        return

    bot = Bot(token)

    try:
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Current webhook info: {webhook_info}")

        if webhook_info.url:
            logger.info("Webhook is set. Attempting to delete...")
            is_deleted = await bot.delete_webhook()
            if is_deleted:
                logger.info("Webhook deleted successfully.")
            else:
                logger.warning("Failed to delete webhook.")
        else:
            logger.info("No webhook is currently set.")

    except Exception as e:
         logger.error(f"An error occurred while checking/deleting webhook: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
         logger.critical(f"Script failed: {e}", exc_info=True)