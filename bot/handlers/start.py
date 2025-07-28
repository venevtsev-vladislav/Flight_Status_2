from aiogram import Router, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.database import DatabaseService
from bot.services.language_service import LanguageService
from bot.services.typing_service import TypingService
from bot.config import MESSAGE_TEMPLATES, DEFAULT_LANGUAGE, BUTTON_LABELS
from bot.handlers.fsm import SimpleFlightSearch
import logging

logger = logging.getLogger(__name__)

router = Router()

def get_simple_date_keyboard(lang="en"):
    """Simple date selection keyboard with yesterday/today/tomorrow only"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Вчера", callback_data="simple_date:yesterday"),
            InlineKeyboardButton(text="Сегодня", callback_data="simple_date:today"),
            InlineKeyboardButton(text="Завтра", callback_data="simple_date:tomorrow"),
        ]
    ])

@router.message(Command("start"))
async def cmd_start(message: Message, db: DatabaseService, language_service: LanguageService, typing_service: TypingService, state: FSMContext):
    """Handle /start command with simplified flow"""
    try:
        # Check if we're already in a conversation
        current_state = await state.get_state()
        if current_state:
            # If already in conversation, just answer and don't send new message
            await message.answer("🔄 Уже идет поиск. Дождитесь завершения или начните заново с /search")
            return
        
        # Show typing indicator
        await typing_service.show_typing(message.chat.id, duration=2)
        
        # Get user info
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username)
        
        # Get user language preference
        lang = user.get('language_code', 'ru')
        
        # Simplified welcome message
        welcome_text = "**Шаг 1 - укажите дату или выберите ниже**"
        
        # Send welcome message with date selection keyboard
        keyboard = get_simple_date_keyboard(lang)
        sent_message = await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        
        # Store the welcome message ID and user's command message ID in state for later deletion
        await state.update_data(
            welcome_message_id=sent_message.message_id,
            user_command_message_id=message.message_id
        )
        
        logger.info(f"✅ Start command handled for user {message.from_user.id}")
        
    except Exception as e:
        # Fallback to simple message
        welcome_text = "**Шаг 1 - укажите дату или выберите ниже**"
        keyboard = get_simple_date_keyboard("ru")
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        logger.error(f"❌ ERROR in cmd_start: {str(e)}")

@router.message(Command("search"))
async def cmd_search(message: Message, db: DatabaseService, language_service: LanguageService, typing_service: TypingService, state: FSMContext):
    """Handle /search command with simplified flow"""
    try:
        # Check if we're already in a conversation
        current_state = await state.get_state()
        if current_state:
            # If already in conversation, just answer and don't send new message
            await message.answer("🔄 Уже идет поиск. Дождитесь завершения или начните заново с /start")
            return
        
        # Show typing indicator
        await typing_service.show_typing(message.chat.id, duration=2)
        
        # Get user info
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username)
        
        # Get user language preference
        lang = user.get('language_code', 'ru')
        
        # Get date selection keyboard
        keyboard = get_simple_date_keyboard(lang)
        
        welcome_text = "**Шаг 1 - укажите дату или выберите ниже**"
        sent_message = await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        
        # Store the welcome message ID and user's command message ID in state for later deletion
        await state.update_data(
            welcome_message_id=sent_message.message_id,
            user_command_message_id=message.message_id
        )
        
        logger.info(f"✅ Search command handled for user {message.from_user.id}")
        
    except Exception as e:
        welcome_text = "**Шаг 1 - укажите дату или выберите ниже**"
        keyboard = get_simple_date_keyboard("ru")
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        logger.error(f"❌ ERROR in cmd_search: {str(e)}") 

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """Handle /reset command to clear conversation state"""
    try:
        await state.clear()
        await message.answer("🔄 Состояние сброшено. Начните заново с /start")
        logger.info(f"✅ Reset command handled for user {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ ERROR in cmd_reset: {str(e)}")
        await message.answer("❌ Ошибка сброса состояния") 