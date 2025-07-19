from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from bot.services.database import DatabaseService
from bot.services.flight_service import FlightService, extract_flight_number
from bot.services.language_service import LanguageService
from bot.services.typing_service import TypingService
from bot.services.search_service import SearchService
from bot.keyboards.inline_keyboards import get_date_selection_keyboard, get_flight_card_keyboard, get_feature_request_keyboard
from bot.config import MESSAGE_TEMPLATES, DEFAULT_LANGUAGE
import asyncio
import logging

logger = logging.getLogger(__name__)

router = Router()

class FlightSearchStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_number = State()

def build_inline_keyboard(buttons_data):
    if not buttons_data:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn['text'], callback_data=btn['callback_data']) for btn in row]
            for row in buttons_data
        ]
    )

@router.message(F.text)
async def handle_text_message(message: Message, state: FSMContext, db: DatabaseService, 
                            flight_service: FlightService, language_service: LanguageService,
                            typing_service: TypingService, search_service: SearchService):
    """Handle text messages for flight search"""
    try:
        # Check if user has an active search
        active_search = await search_service.get_active_search(message.from_user.id)
        logger.info(f"🔍 DEBUG: Active search found: {active_search}")
        
        if active_search:
            # User has an active search, handle based on state
            logger.info(f"🔍 DEBUG: Processing with active search state: {active_search['search_state']}")
            if active_search['search_state'] == 'waiting_for_number':
                logger.info(f"🔍 DEBUG: Handling number input with search")
                await handle_number_input_with_search(message, active_search, db, flight_service, 
                                                   typing_service, search_service)
                return
            elif active_search['search_state'] == 'waiting_for_date':
                logger.info(f"🔍 DEBUG: Handling date input with search")
                await handle_date_input_with_search(message, active_search, db, flight_service, 
                                                 typing_service, search_service)
                return
        
        # Detect user language
        detected_language = language_service.detect_language(
            user_language_code=message.from_user.language_code,
            user_text=message.text
        )
        
        # Get or create user
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            language_code=detected_language
        )
        
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        
        # Save message to database
        await db.save_message(
            user_id=user['id'],
            message_id=message.message_id,
            content=message.text
        )
        
        # Parse flight request first
        logger.info(f"🔍 DEBUG: Parsing text: '{message.text}'")
        parse_result = await flight_service.parse_flight_request(message.text, user['id'])
        logger.info(f"🔍 DEBUG: Parse result: {parse_result}")
        logger.info(f"🔍 DEBUG: Parse result type: {type(parse_result)}")
        logger.info(f"🔍 DEBUG: Parse result is None: {parse_result is None}")
        
        if parse_result is None:
            logger.error(f"❌ Parse result is None for input: '{message.text}'")
            error_text = MESSAGE_TEMPLATES["parse_error"][lang]
            await message.answer(error_text)
            return
        
        if parse_result.get('error'):
            logger.info(f"🔍 DEBUG: Parse error: {parse_result['error']}")
            error_text = MESSAGE_TEMPLATES["parse_error"][lang]
            await message.answer(error_text)
            return
        
        flight_number = parse_result.get('flight_number')
        date = parse_result.get('date')
        
        # Debug logging
        logger.info(f"🔍 DEBUG: flight_number='{flight_number}', date='{date}'")
        
        # Save parsed result
        await db.save_message(
            user_id=user['id'],
            message_id=message.message_id,
            content=message.text,
            parsed_json=parse_result
        )
        
        # Handle incomplete data
        if flight_number and not date:
            logger.info(f"🔍 DEBUG: Only flight number found, handling...")
            # User provided flight number but no date
            await handle_flight_number_only_with_search(message, flight_number, lang, user, search_service)
        elif date and not flight_number:
            logger.info(f"🔍 DEBUG: Only date found, handling...")
            # User provided date but no flight number
            await handle_date_only_with_search(message, date, lang, user, search_service)
        elif flight_number and date:
            logger.info(f"🔍 DEBUG: Both flight number and date found, processing...")
            # Complete data - process flight request
            await process_flight_request(message, flight_number, date, user, db, flight_service, lang, typing_service)
            # Clear active search
            await search_service.delete_active_search(message.from_user.id)
        else:
            logger.info(f"🔍 DEBUG: No useful data found")
            # No useful data found - show detailed error
            logger.warning(f"❌ Parse failed for user input: '{message.text}'")
            logger.warning(f"❌ Parse result: {parse_result}")
            logger.warning(f"❌ Flight number: '{flight_number}', Date: '{date}'")
            
            # Create detailed error message
            if flight_number:
                error_text = f"✅ Найден номер рейса: {flight_number}\n❌ Не удалось распознать дату.\n\nПопробуйте: {flight_number} сегодня или {flight_number} 13.07.2025"
            elif date:
                error_text = f"✅ Найденная дата: {date}\n❌ Не удалось распознать номер рейса.\n\nПопробуйте: SU100 {date} или QR123 {date}"
            else:
                error_text = f"❌ Не удалось распознать номер рейса и дату из: '{message.text}'\n\nПримеры:\n• AA8242 сегодня\n• SU100 13.07.2025\n• QR123 завтра"
            
            await message.answer(error_text)
            
    except Exception as e:
        # Log error and send fallback message
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='text_message_error',
            details={'error': str(e), 'message': message.text}
        )
        
        error_text = MESSAGE_TEMPLATES["parse_error"][DEFAULT_LANGUAGE]
        await message.answer(error_text)

async def handle_flight_number_only_with_search(message: Message, flight_number: str, lang: str, user: dict, search_service: SearchService):
    """Handle case when only flight number is provided using SearchService"""
    # Save flight number to active search
    await search_service.update_search_with_flight_number(
        telegram_id=message.from_user.id,
        user_id=user['id'],
        flight_number=flight_number,
        parsed_data={'flight_number': flight_number}
    )
    
    # Use today's date as default
    today_date = datetime.now().strftime('%Y-%m-%d')
    today_display = datetime.now().strftime('%d.%m.%Y')
    
    # Get services
    from bot.services.database import DatabaseService
    from bot.services.flight_service import FlightService
    from bot.services.typing_service import TypingService
    
    db = DatabaseService()
    flight_service = FlightService()
    typing_service = TypingService(message.bot)
    
    # Process with today's date
    await process_flight_request(message, flight_number, today_date, user, db, 
                               flight_service, lang, typing_service)
    
    # Also offer date selection buttons
    text = f"Я использовал сегодняшнюю дату ({today_display}). Если нужна другая дата, выберите ниже:"
    keyboard = get_date_selection_keyboard(flight_number, lang)
    
    await message.answer(text, reply_markup=keyboard)

async def handle_date_only_with_search(message: Message, date: str, lang: str, user: dict, search_service: SearchService):
    """Handle case when only date is provided using SearchService"""
    # Save date to active search
    await search_service.update_search_with_date(
        telegram_id=message.from_user.id,
        user_id=user['id'],
        search_date=date,
        parsed_data={'date': date}
    )
    
    text = MESSAGE_TEMPLATES["no_number_request"][lang].format(date=date)
    await message.answer(text)

async def process_flight_request(message: Message, flight_number: str, date: str, user: dict, 
                               db: DatabaseService, flight_service: FlightService, lang: str,
                               typing_service: TypingService):
    """Process complete flight request"""
    try:
        logger.info(f"🔍 DEBUG: Starting process_flight_request for {flight_number} on {date}")
        
        # Get or create flight record
        flight = await db.get_or_create_flight(flight_number, date)
        logger.info(f"🔍 DEBUG: Flight record: {flight}")
        
        # Save flight request
        await db.save_flight_request(user['id'], flight['id'])
        logger.info(f"🔍 DEBUG: Flight request saved")
        
        # Send search started message
        search_started_text = MESSAGE_TEMPLATES["search_started"][lang].format(
            flight_number=flight_number, date=date
        )
        logger.info(f"🔍 DEBUG: Sending search started message: {search_started_text}")
        await message.answer(search_started_text)
        
        # Get flight data directly
        logger.info(f"🔍 DEBUG: Calling flight_service.get_flight_data directly")
        flight_data = await flight_service.get_flight_data(flight_number, date, user['id'])
        logger.info(f"🔍 DEBUG: Flight data received: {flight_data}")
        
        if flight_data.get('error'):
            logger.info(f"🔍 DEBUG: Flight data has error: {flight_data['error']}")
            # Handle API error
            if flight_data['error'] == 'past_flight':
                text = MESSAGE_TEMPLATES["past_flight"][lang]
                keyboard = get_feature_request_keyboard(flight['id'], lang)
            elif flight_data['error'] == 'future_flight':
                text = MESSAGE_TEMPLATES["future_flight"][lang].format(
                    flight_number=flight_number, date=date
                )
                keyboard = get_feature_request_keyboard(flight['id'], lang)
            else:
                text = MESSAGE_TEMPLATES["api_error"][lang]
                keyboard = None
        else:
            logger.info(f"🔍 DEBUG: Flight data successful, preparing response")
            # Backend handles all validation and formatting
            text = flight_data.get('message', MESSAGE_TEMPLATES["no_data_found"][lang])
            buttons = flight_data.get('buttons')
            keyboard = build_inline_keyboard(buttons)
        
        # Send response
        logger.info(f"🔍 DEBUG: Sending final response: {text}")
        if keyboard:
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(text)
            
    except Exception as e:
        logger.error(f"❌ ERROR in process_flight_request: {str(e)}")
        # Log error and send fallback message
        await db.log_audit(
            user_id=user['id'],
            action='flight_request_error',
            details={'error': str(e), 'flight_number': flight_number, 'date': date}
        )
        
        error_text = MESSAGE_TEMPLATES["technical_error"][lang]
        await message.answer(error_text)

async def handle_date_input_with_search(message: Message, active_search: dict, db: DatabaseService, 
                                      flight_service: FlightService, typing_service: TypingService,
                                      search_service: SearchService):
    """Handle date input when waiting for date using SearchService"""
    try:
        # Get stored flight number from active search
        flight_number = active_search.get('flight_number')
        
        if not flight_number:
            await message.answer("Error: Flight number not found. Please start over.")
            await search_service.delete_active_search(message.from_user.id)
            return
        
        # Parse the date input
        date_input = message.text.strip().lower()
        
        # Handle relative dates
        if date_input in ['yesterday', 'вчера']:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif date_input in ['today', 'сегодня']:
            date = datetime.now().strftime('%Y-%m-%d')
        elif date_input in ['tomorrow', 'завтра']:
            date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            # Try to parse date format DD.MM.YYYY
            try:
                date_obj = datetime.strptime(date_input, '%d.%m.%Y')
                date = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_input, '%d.%m.%y')
                    date = date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    await message.answer("Please enter a valid date (DD.MM.YYYY) or choose from the buttons.")
                    return
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        
        # Process the complete request
        await process_flight_request(message, flight_number, date, user, db, flight_service, 
                                  user.get('language_code', 'en'), typing_service)
        
        # Clear active search
        await search_service.delete_active_search(message.from_user.id)
        
    except Exception as e:
        await message.answer("Error processing date. Please try again.")
        await search_service.delete_active_search(message.from_user.id)

async def handle_number_input_with_search(message: Message, active_search: dict, db: DatabaseService, 
                                        flight_service: FlightService, typing_service: TypingService,
                                        search_service: SearchService):
    """Handle flight number input when waiting for number using SearchService"""
    try:
        logger.info(f"🔍 DEBUG: handle_number_input_with_search called with text: '{message.text}'")
        logger.info(f"🔍 DEBUG: active_search: {active_search}")
        # Используем универсальный парсер flight_number
        flight_number = extract_flight_number(message.text)
        logger.info(f"🔍 DEBUG: Parsed flight number: {flight_number}")
        if not flight_number:
            logger.warning(f"❌ Invalid flight number format: '{message.text}'")
            await message.answer("❌ Invalid flight number format. Please enter a valid flight number (e.g. SU100, 5J944, VJ352, etc.)")
            return
        
        # Get stored date from active search
        date = active_search.get('search_date')
        logger.info(f"🔍 DEBUG: Stored date: {date}")
        
        if not date:
            logger.error("❌ No date found in active search")
            await message.answer("Error: Date not found. Please start over.")
            await search_service.delete_active_search(message.from_user.id)
            return
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        
        # Process the complete request
        await process_flight_request(message, flight_number, date, user, db, flight_service, 
                                  user.get('language_code', 'en'), typing_service)
        
        # Clear active search
        await search_service.delete_active_search(message.from_user.id)
        
    except Exception as e:
        logger.error(f"❌ ERROR in handle_number_input_with_search: {str(e)}")
        await message.answer("Error processing flight number. Please try again.")
        await search_service.delete_active_search(message.from_user.id) 