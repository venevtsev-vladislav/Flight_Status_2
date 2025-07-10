import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_with_config():
    """Test bot with config import"""
    try:
        # Import config
        from bot.config import BOT_TOKEN, BOT_VERSION
        logger.info(f"Config imported successfully. Bot version: {BOT_VERSION}")
        
        # Test bot initialization
        bot = Bot(token=BOT_TOKEN)
        
        # Use memory storage for FSM
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        logger.info("Bot with config initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_with_config()) 