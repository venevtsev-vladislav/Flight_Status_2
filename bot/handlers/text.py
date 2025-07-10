from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from bot.services.database import DatabaseService
from bot.services.flight_service import FlightService
from bot.keyboards.inline_keyboards import get_date_selection_keyboard, get_flight_card_keyboard, get_feature_request_keyboard
from bot.config import MESSAGE_TEMPLATES, DEFAULT_LANGUAGE

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
async def handle_text_message(message: Message, state: FSMContext, db: DatabaseService, flight_service: FlightService):
    """Handle text messages for flight search"""
    try:
        # Get or create user
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            language_code=message.from_user.language_code or DEFAULT_LANGUAGE
        )
        
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        
        # Save message to database
        await db.save_message(
            user_id=user['id'],
            message_id=message.message_id,
            content=message.text
        )
        
        # Parse flight request
        parse_result = await flight_service.parse_flight_request(message.text, user['id'])
        
        if parse_result.get('error'):
            # Handle parsing error
            error_text = MESSAGE_TEMPLATES["parse_error"][lang]
            await message.answer(error_text)
            return
        
        flight_number = parse_result.get('flight_number')
        date = parse_result.get('date')
        
        # Save parsed result
        await db.save_message(
            user_id=user['id'],
            message_id=message.message_id,
            content=message.text,
            parsed_json=parse_result
        )
        
        # Handle incomplete data
        if flight_number and not date:
            # User provided flight number but no date
            await handle_flight_number_only(message, flight_number, lang, state)
        elif date and not flight_number:
            # User provided date but no flight number
            await handle_date_only(message, date, lang, state)
        elif flight_number and date:
            # Complete data - process flight request
            await process_flight_request(message, flight_number, date, user, db, flight_service, lang)
        else:
            # No useful data found
            error_text = MESSAGE_TEMPLATES["parse_error"][lang]
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

async def handle_flight_number_only(message: Message, flight_number: str, lang: str, state: FSMContext):
    """Handle case when only flight number is provided"""
    await state.set_state(FlightSearchStates.waiting_for_date)
    await state.update_data(flight_number=flight_number)
    
    text = MESSAGE_TEMPLATES["no_date_request"][lang].format(flight_number=flight_number)
    keyboard = get_date_selection_keyboard(flight_number, lang)
    
    await message.answer(text, reply_markup=keyboard)

async def handle_date_only(message: Message, date: str, lang: str, state: FSMContext):
    """Handle case when only date is provided"""
    await state.set_state(FlightSearchStates.waiting_for_number)
    await state.update_data(date=date)
    
    text = MESSAGE_TEMPLATES["no_number_request"][lang].format(date=date)
    await message.answer(text)

async def process_flight_request(message: Message, flight_number: str, date: str, user: dict, 
                               db: DatabaseService, flight_service: FlightService, lang: str):
    """Process complete flight request"""
    try:
        # Get or create flight record
        flight = await db.get_or_create_flight(flight_number, date)
        
        # Save flight request
        await db.save_flight_request(user['id'], flight['id'])
        
        # Get flight data
        flight_data = await flight_service.get_flight_data(flight_number, date, user['id'])
        
        if flight_data.get('error'):
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
                text = MESSAGE_TEMPLATES["parse_error"][lang]
                keyboard = None
        else:
            text = flight_data.get('message', '⚠️ No flight data.')
            buttons = flight_data.get('buttons')
            keyboard = build_inline_keyboard(buttons)
        
        # Send response
        if keyboard:
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(text)
            
    except Exception as e:
        # Log error and send fallback message
        await db.log_audit(
            user_id=user['id'],
            action='flight_request_error',
            details={'error': str(e), 'flight_number': flight_number, 'date': date}
        )
        
        error_text = MESSAGE_TEMPLATES["parse_error"][lang]
        await message.answer(error_text)

@router.message(FlightSearchStates.waiting_for_date)
async def handle_date_input(message: Message, state: FSMContext, db: DatabaseService, flight_service: FlightService):
    """Handle date input when waiting for date"""
    try:
        # Get stored flight number
        data = await state.get_data()
        flight_number = data.get('flight_number')
        
        if not flight_number:
            await message.answer("Error: Flight number not found. Please start over.")
            await state.clear()
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
        await process_flight_request(message, flight_number, date, user, db, flight_service, user.get('language_code', 'en'))
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        await message.answer("Error processing date. Please try again.")
        await state.clear()

@router.message(FlightSearchStates.waiting_for_number)
async def handle_number_input(message: Message, state: FSMContext, db: DatabaseService, flight_service: FlightService):
    """Handle flight number input when waiting for number"""
    try:
        # Get stored date
        data = await state.get_data()
        date = data.get('date')
        
        if not date:
            await message.answer("Error: Date not found. Please start over.")
            await state.clear()
            return
        
        # Extract flight number from message
        text = message.text.strip().upper()
        
        # Simple flight number validation (2-3 letters + 1-4 digits)
        import re
        flight_match = re.match(r'^[A-Z]{2,3}\d{1,4}$', text)
        
        if not flight_match:
            await message.answer("Please enter a valid flight number (e.g., QR123, SU1000)")
            return
        
        flight_number = text
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        
        # Process the complete request
        await process_flight_request(message, flight_number, date, user, db, flight_service, user.get('language_code', 'en'))
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        await message.answer("Error processing flight number. Please try again.")
        await state.clear() 