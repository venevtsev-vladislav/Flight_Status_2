import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import BOT_TOKEN, BOT_VERSION
from bot.services.database import DatabaseService
from bot.services.flight_service import FlightService
from bot.handlers import start, text, callbacks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    try:
        # Initialize bot and dispatcher
        bot = Bot(
            token=BOT_TOKEN,
            parse_mode="HTML"
        )
        
        # Use memory storage for FSM
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Initialize services
        db_service = DatabaseService()
        flight_service = FlightService()
        
        # Register dependency injection
        dp["db"] = db_service
        dp["flight_service"] = flight_service
        
        # Include routers
        dp.include_router(start.router)
        dp.include_router(text.router)
        dp.include_router(callbacks.router)
        
        # Log startup
        logger.info(f"Starting Flight Status Bot v{BOT_VERSION}")
        logger.info("Bot is ready to handle messages")
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}") 