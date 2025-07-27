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
    # Проверяем, что каждая строка — это массив кнопок
    keyboard = []
    for row in buttons_data:
        # row — это массив объектов с text и callback_data
        buttons = [InlineKeyboardButton(text=btn['text'], callback_data=btn['callback_data']) for btn in row]
        keyboard.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
        
        # Проверяем подписку пользователя на этот рейс
        user_id = user['id'] if user and 'id' in user else None
        flight_id = flight['id'] if flight and 'id' in flight else None
        is_subscribed = False
        if user_id and flight_id:
            is_subscribed = await db.is_subscribed(user_id, flight_id)
        logger.info(f"🔍 DEBUG: is_subscribed={is_subscribed}")
        
        # Get flight data directly
        logger.info(f"🔍 DEBUG: Calling flight_service.get_flight_data directly")
        flight_data = await flight_service.get_flight_data(flight_number, date, user_id)
        logger.info(f"🔍 DEBUG: Flight data received: {flight_data}")
        
        if flight_data.get('error'):
            logger.info(f"🔍 DEBUG: Flight data has error: {flight_data['error']}")
            # Handle API error
            if flight_data['error'] == 'past_flight':
                text = MESSAGE_TEMPLATES["past_flight"][lang]
                keyboard = get_feature_request_keyboard(flight_id, lang)
            elif flight_data['error'] == 'future_flight':
                text = MESSAGE_TEMPLATES["future_flight"][lang].format(
                    flight_number=flight_number, date=date
                )
                keyboard = get_feature_request_keyboard(flight_id, lang)
            else:
                text = MESSAGE_TEMPLATES["api_error"][lang]
                keyboard = None
        else:
            logger.info(f"🔍 DEBUG: Flight data successful, preparing response")
            text = flight_data.get('message', MESSAGE_TEMPLATES["no_data_found"][lang])
            # Всегда используем только кнопки, пришедшие с бэка
            if 'buttons' in flight_data and flight_data['buttons']:
                keyboard = build_inline_keyboard(flight_data['buttons'])
            else:
                keyboard = None
        
        # Send response
        logger.info(f"🔍 DEBUG: Sending final response: {text}")
        if keyboard:
            await message.answer(text or '', reply_markup=keyboard)
        else:
            await message.answer(text or '')
        
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

def formatTelegramMessage(flight: dict) -> str:
    """Format flight data for Telegram message display"""
    try:
        if not flight or flight is None:
            return '⚠️ No flight data.'
        
        if not isinstance(flight, dict):
            logger.error(f"Flight data is not a dict: {type(flight)}")
            return '⚠️ Invalid flight data format.'
        
        lines = []
        
        # Flight number and route
        flight_number = flight.get('number', '')
        dep_iata = flight.get('departure', {}).get('airport', {}).get('iata')
        arr_iata = flight.get('arrival', {}).get('airport', {}).get('iata')
        dep_name = flight.get('departure', {}).get('airport', {}).get('name')
        arr_name = flight.get('arrival', {}).get('airport', {}).get('name')
        
        # Header line
        header = flight_number
        if dep_iata and arr_iata:
            header += f' {dep_iata}→{arr_iata}'
        
        # Add departure time (prefer revised, then scheduled)
        dep_revised_obj = flight.get('departure', {}).get('revisedTime', {})
        dep_scheduled_obj = flight.get('departure', {}).get('scheduledTime', {})
        
        dep_revised = dep_revised_obj.get('local') if dep_revised_obj else None
        dep_scheduled = dep_scheduled_obj.get('local') if dep_scheduled_obj else None
        dep_time = dep_revised or dep_scheduled
        
        if dep_time:
            try:
                # Parse time from "2025-07-09 21:50+03:00" format
                time_part = dep_time.split(' ')[1].split('+')[0]
                header += f' {time_part}'
                
                # Add date
                date_part = dep_time.split(' ')[0]
                date_obj = datetime.strptime(date_part, '%Y-%m-%d')
                date_str = date_obj.strftime('%d.%m.%Y')
                header += f' ({date_str})'
            except:
                pass
        
        lines.append(header.strip())
        
        # Status
        status = flight.get('status', '')
        if status:
            status_indicators = {
                'scheduled': '⏳',
                'checkin': '🟠',
                'boarding': '🟢',
                'gateclosed': '🔴',
                'departed': '🛫',
                'enroute': '✈️',
                'arrived': '🏁',
                'delayed': '⏰',
                'cancelled': '❌',
                'canceled': '❌',
                'diverted': '⚠️'
            }
            indicator = status_indicators.get(status.lower(), '⏳')
            lines.append(f'{indicator} Status: {status}')
            lines.append('')
        
        # Codeshare info
        codeshares = flight.get('codeshares', [])
        if codeshares:
            codeshare_list = ', '.join(codeshares)
            lines.append(f'Also listed as: {codeshare_list}')
            lines.append('')
        elif flight.get('codeshareNote'):
            lines.append(f'📋 {flight["codeshareNote"]}')
            lines.append('')
        
        # Departure section
        if dep_iata or dep_name:
            lines.append(f'🛫 {dep_iata or "--"} / {dep_name or ""}'.strip())
            
            # Terminal
            terminal = flight.get('departure', {}).get('terminal')
            if terminal:
                lines.append(f'Terminal: {terminal}')
            
            # Check-in desk
            checkin = flight.get('departure', {}).get('checkInDesk')
            if checkin:
                lines.append(f'Check-in: {checkin}')
            
            # Gate
            gate = flight.get('departure', {}).get('gate')
            if gate:
                # Add boarding time for CheckIn status
                status = flight.get('status', '').lower()
                if status == 'checkin':
                    # Calculate boarding time (usually 20 minutes before departure)
                    dep_scheduled = flight.get('departure', {}).get('scheduledTime', {}).get('local')
                    if dep_scheduled:
                        try:
                            # Parse departure time
                            dep_time = datetime.strptime(dep_scheduled.split(' ')[0] + ' ' + dep_scheduled.split(' ')[1].split('+')[0], '%Y-%m-%d %H:%M')
                            # Calculate boarding time (20 minutes before)
                            boarding_time = dep_time - timedelta(minutes=20)
                            boarding_time_str = boarding_time.strftime('%I:%M %p')
                            lines.append(f'Gate: {gate} (boarding at {boarding_time_str})')
                        except Exception as e:
                            logger.error(f"Error calculating boarding time: {e}")
                            lines.append(f'Gate: {gate}')
                    else:
                        lines.append(f'Gate: {gate}')
                elif status == 'boarding':
                    lines.append(f'Gate: {gate} (boarding in progress)')
                else:
                    lines.append(f'Gate: {gate}')
            
            # Departure time
            dep_actual_obj = flight.get('departure', {}).get('actualTime', {})
            dep_revised_obj = flight.get('departure', {}).get('revisedTime', {})
            dep_scheduled_obj = flight.get('departure', {}).get('scheduledTime', {})
            
            dep_actual = dep_actual_obj.get('local') if dep_actual_obj else None
            dep_revised = dep_revised_obj.get('local') if dep_revised_obj else None
            dep_scheduled = dep_scheduled_obj.get('local') if dep_scheduled_obj else None
            
            dep_current = dep_actual or dep_revised or dep_scheduled
            if dep_current and dep_scheduled and dep_current != dep_scheduled:
                try:
                    current_time = dep_current.split(' ')[1].split('+')[0]
                    scheduled_time = dep_scheduled.split(' ')[1].split('+')[0]
                    lines.append(f'Departure: {current_time} (was {scheduled_time})')
                except:
                    try:
                        time_part = dep_current.split(' ')[1].split('+')[0]
                        lines.append(f'Departure: {time_part}')
                    except:
                        lines.append(f'Departure: {dep_current}')
            elif dep_current:
                try:
                    time_part = dep_current.split(' ')[1].split('+')[0]
                    lines.append(f'Departure: {time_part}')
                except:
                    lines.append(f'Departure: {dep_current}')
            
            lines.append('')
        
        # Arrival section
        if arr_iata or arr_name:
            lines.append(f'🛬 {arr_iata or "--"} / {arr_name or ""}'.strip())
            
            # Terminal
            terminal = flight.get('arrival', {}).get('terminal')
            if terminal:
                lines.append(f'Terminal: {terminal}')
            
            # Gate
            gate = flight.get('arrival', {}).get('gate')
            if gate and gate is not None:
                lines.append(f'Gate: {gate}')
            
            # Arrival time
            arr_actual = flight.get('arrival', {}).get('actualTime', {})
            arr_revised = flight.get('arrival', {}).get('revisedTime', {})
            arr_predicted = flight.get('arrival', {}).get('predictedTime', {})
            arr_scheduled = flight.get('arrival', {}).get('scheduledTime', {})
            
            arr_actual_local = arr_actual.get('local') if arr_actual else None
            arr_revised_local = arr_revised.get('local') if arr_revised else None
            arr_predicted_local = arr_predicted.get('local') if arr_predicted else None
            arr_scheduled_local = arr_scheduled.get('local') if arr_scheduled else None
            
            arr_current = arr_actual_local or arr_revised_local or arr_predicted_local or arr_scheduled_local
            if arr_current and arr_scheduled_local and arr_current != arr_scheduled_local:
                try:
                    current_time = arr_current.split(' ')[1].split('+')[0]
                    scheduled_time = arr_scheduled_local.split(' ')[1].split('+')[0]
                    lines.append(f'Arrival: {current_time} (was {scheduled_time})')
                except:
                    try:
                        time_part = arr_current.split(' ')[1].split('+')[0]
                        lines.append(f'Arrival: {time_part}')
                    except:
                        lines.append(f'Arrival: {arr_current}')
            elif arr_current:
                try:
                    time_part = arr_current.split(' ')[1].split('+')[0]
                    lines.append(f'Arrival: {time_part}')
                except:
                    lines.append(f'Arrival: {arr_current}')
            
            # Baggage belt
            baggage = flight.get('arrival', {}).get('baggageBelt')
            if baggage:
                lines.append(f'Baggage: {baggage}')
            
            lines.append('')
        
        # Separator
        lines.append('__________________')
        
        # Aircraft and airline info
        aircraft = flight.get('aircraft')
        if aircraft and isinstance(aircraft, dict):
            aircraft_model = aircraft.get('model')
            if aircraft_model:
                lines.append(f'Aircraft: {aircraft_model}')
        
        airline = flight.get('airline')
        if airline and isinstance(airline, dict):
            airline_name = airline.get('name')
            if airline_name:
                lines.append(f'Airline: {airline_name}')
        
        return '\n'.join(lines).replace('\n\n\n', '\n\n').strip()
        
    except Exception as e:
        logger.error(f"Error in formatTelegramMessage: {e}")
        logger.error(f"Flight data structure: {flight}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return '⚠️ Error formatting flight data.' 