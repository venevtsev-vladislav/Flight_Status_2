from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.services.database import DatabaseService
from bot.config import MESSAGE_TEMPLATES, DEFAULT_LANGUAGE

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, db: DatabaseService):
    """Handle /start command"""
    try:
        # Get or create user
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            language_code=message.from_user.language_code or DEFAULT_LANGUAGE
        )
        
        # Get welcome message
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        welcome_text = MESSAGE_TEMPLATES["welcome"][lang].format(
            username=message.from_user.first_name or "User"
        )
        
        # Send welcome message
        await message.answer(welcome_text)
        
        # Log the start action
        await db.log_audit(
            user_id=user['id'],
            action='bot_start',
            details={
                'telegram_id': message.from_user.id,
                'username': message.from_user.username,
                'language_code': message.from_user.language_code
            }
        )
        
    except Exception as e:
        # Fallback to English if translation fails
        welcome_text = MESSAGE_TEMPLATES["welcome"]["en"].format(
            username=message.from_user.first_name or "User"
        )
        await message.answer(welcome_text) 