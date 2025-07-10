import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_with_services():
    """Test bot with services import"""
    try:
        # Import config
        from bot.config import BOT_TOKEN, BOT_VERSION
        logger.info(f"Config imported successfully. Bot version: {BOT_VERSION}")
        
        # Import services
        from bot.services.database import DatabaseService
        from bot.services.flight_service import FlightService
        logger.info("Services imported successfully")
        
        # Test bot initialization
        bot = Bot(token=BOT_TOKEN)
        
        # Use memory storage for FSM
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Initialize services
        db_service = DatabaseService()
        flight_service = FlightService()
        logger.info("Services initialized successfully")
        
        logger.info("Bot with services initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_with_services()) 