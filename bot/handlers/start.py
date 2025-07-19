from aiogram import Router, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from bot.services.database import DatabaseService
from bot.services.language_service import LanguageService
from bot.services.typing_service import TypingService
from bot.config import MESSAGE_TEMPLATES, DEFAULT_LANGUAGE, BUTTON_LABELS

router = Router()

def get_date_keyboard(lang="en"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BUTTON_LABELS["yesterday"][lang], callback_data="date:yesterday"),
            InlineKeyboardButton(text=BUTTON_LABELS["today"][lang], callback_data="date:today"),
            InlineKeyboardButton(text=BUTTON_LABELS["tomorrow"][lang], callback_data="date:tomorrow"),
        ]
    ])

@router.message(Command("start"))
async def cmd_start(message: Message, db: DatabaseService, language_service: LanguageService, typing_service: TypingService):
    """Handle /start command"""
    try:
        # Show typing indicator
        await typing_service.show_typing(message.chat.id, duration=2)
        
        user_obj = message.from_user or type('User', (), {'id': 0, 'username': 'unknown', 'language_code': 'en', 'first_name': 'User'})()
        # Detect user language
        detected_language = language_service.detect_language(
            user_language_code=getattr(user_obj, 'language_code', 'en'),
            user_text=message.text
        )
        
        # Get or create user with detected language
        telegram_id = getattr(user_obj, 'id', 0) or 0
        username = getattr(user_obj, 'username', 'unknown') or 'unknown'
        user = await db.get_or_create_user(
            telegram_id=telegram_id,
            username=username,
            language_code=detected_language
        )
        
        # Get welcome message
        lang = user.get('language_code', DEFAULT_LANGUAGE) if user else DEFAULT_LANGUAGE
        from datetime import datetime
        today_str = datetime.now().strftime('%d.%m.%Y')
        welcome_template = MESSAGE_TEMPLATES["welcome"][lang]
        if '{today}' in welcome_template:
            welcome_text = welcome_template.format(
                username=getattr(user_obj, 'first_name', 'User') or 'User',
            today=today_str
        )
        else:
            welcome_text = welcome_template.format(
                username=getattr(user_obj, 'first_name', 'User') or 'User'
            )
        
        # Send boarding pass image with caption and date keyboard
        photo = FSInputFile('Example_Bording_pass.png')
        keyboard = get_date_keyboard(lang)
        await message.answer_photo(photo, caption=welcome_text, reply_markup=keyboard)
        
        # Log the start action
        user_id = user['id'] if user and 'id' in user else 'unknown'
        await db.log_audit(
            user_id=user_id,
            action='bot_start',
            details={
                'telegram_id': telegram_id,
                'username': username,
                'language_code': getattr(user_obj, 'language_code', 'en'),
                'detected_language': detected_language
            }
        )
        
    except Exception as e:
        # Fallback to English if translation fails
        user_name = getattr(message.from_user, 'first_name', None) if message.from_user else "User"
        welcome_text = MESSAGE_TEMPLATES["welcome"]["en"].format(
            username=user_name or "User"
        )
        await message.answer(welcome_text) 


@router.message(Command("search"))
async def cmd_search(message: Message, db: DatabaseService, language_service: LanguageService, typing_service: TypingService):
    """Handle /search command (short version)"""
    try:
        # Show typing indicator
        await typing_service.show_typing(message.chat.id, duration=1)

        user_obj = message.from_user or type('User', (), {'id': 0, 'username': 'unknown', 'language_code': 'en', 'first_name': 'User'})()
        # Detect user language
        detected_language = language_service.detect_language(
            user_language_code=getattr(user_obj, 'language_code', 'en'),
            user_text=message.text
        )

        # Get or create user with detected language
        telegram_id = getattr(user_obj, 'id', 0) or 0
        username = getattr(user_obj, 'username', 'unknown') or 'unknown'
        user = await db.get_or_create_user(
            telegram_id=telegram_id,
            username=username,
            language_code=detected_language
        )

        lang = user.get('language_code', DEFAULT_LANGUAGE) if user else DEFAULT_LANGUAGE
        keyboard = get_date_keyboard(lang)
        await message.answer(
            "Please enter the flight number and date (e.g. SU100, 2024-07-10):",
            reply_markup=keyboard
        )

        # Log the search action
        user_id = user['id'] if user and 'id' in user else 'unknown'
        await db.log_audit(
            user_id=user_id,
            action='bot_search',
            details={
                'telegram_id': telegram_id,
                'username': username,
                'language_code': getattr(user_obj, 'language_code', 'en'),
                'detected_language': detected_language
            }
        )

    except Exception as e:
        await message.answer("Please enter the flight number and date (e.g. SU100, 2024-07-10):") 