from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
# from bot.services.database import DatabaseService
from bot.services.language_service import LanguageService
from bot.services.typing_service import TypingService
from bot.config import MESSAGE_TEMPLATES, DEFAULT_LANGUAGE, BUTTON_LABELS
import logging

logger = logging.getLogger(__name__)

router = Router()

class SimpleFlightSearch(StatesGroup):
    waiting_for_date = State()
    waiting_for_flight_number = State()

def get_simple_date_keyboard(lang="en"):
    """Get simple date selection keyboard"""
    if lang == "ru":
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Вчера", callback_data="simple_date:yesterday"),
                InlineKeyboardButton(text="Сегодня", callback_data="simple_date:today"),
                InlineKeyboardButton(text="Завтра", callback_data="simple_date:tomorrow"),
            ]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Yesterday", callback_data="simple_date:yesterday"),
                InlineKeyboardButton(text="Today", callback_data="simple_date:today"),
                InlineKeyboardButton(text="Tomorrow", callback_data="simple_date:tomorrow"),
            ]
        ])

@router.message(Command("start"))
async def cmd_start(message: Message, language_service: LanguageService, typing_service: TypingService, state: FSMContext, db=None):
    """Handle /start command with simplified flow"""
    try:
        # Check if we're already in a conversation
        current_state = await state.get_state()
        if current_state:
            # If already in conversation, just answer and don't send new message
            await message.answer("🔄 Search already in progress. Wait for completion or start again with /search")
            return
        
        # Show typing indicator
        await typing_service.show_typing(message.chat.id, duration=2)
        
        # Get user info (if db available)
        user = None
        if db:
            user = await db.get_or_create_user(message.from_user.id, message.from_user.username)
        
        # Get user language preference
        lang = user.get('language_code', 'en') if user else 'en'
        
        # Simplified welcome message
        welcome_text = "**Step 1 - enter date or select below**"
        
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
        welcome_text = "**Step 1 - enter date or select below**"
        keyboard = get_simple_date_keyboard("en")
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        logger.error(f"❌ ERROR in cmd_start: {str(e)}")

@router.message(Command("search"))
async def cmd_search(message: Message, language_service: LanguageService, typing_service: TypingService, state: FSMContext, db=None):
    """Handle /search command with simplified flow"""
    try:
        # Check if we're already in a conversation
        current_state = await state.get_state()
        if current_state:
            # If already in conversation, just answer and don't send new message
            await message.answer("🔄 Search already in progress. Wait for completion or start again with /start")
            return
        
        # Show typing indicator
        await typing_service.show_typing(message.chat.id, duration=2)
        
        # Get user info
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username)
        
        # Get user language preference
        lang = user.get('language_code', 'en')
        
        # Get date selection keyboard
        keyboard = get_simple_date_keyboard(lang)
        
        welcome_text = "**Step 1 - enter date or select below**"
        sent_message = await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        
        # Store the welcome message ID and user's command message ID in state for later deletion
        await state.update_data(
            welcome_message_id=sent_message.message_id,
            user_command_message_id=message.message_id
        )
        
        logger.info(f"✅ Search command handled for user {message.from_user.id}")

    except Exception as e:
        # Fallback to simple message
        welcome_text = "**Step 1 - enter date or select below**"
        keyboard = get_simple_date_keyboard("en")
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        logger.error(f"❌ ERROR in cmd_search: {str(e)}")

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """Handle /reset command"""
    try:
        # Clear state
        await state.clear()
        
        # Send reset confirmation
        await message.answer("🔄 State reset. Start again with /start")
        
        logger.info(f"✅ Reset command handled for user {message.from_user.id}")

    except Exception as e:
        await message.answer("❌ Error resetting state")
        logger.error(f"❌ ERROR in cmd_reset: {str(e)}") 