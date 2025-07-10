import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot():
    """Test bot initialization"""
    try:
        # Test with a dummy token
        bot = Bot(token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
        
        # Use memory storage for FSM
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        logger.info("Bot initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot()) 