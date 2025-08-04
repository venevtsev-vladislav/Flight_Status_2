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
from bot.handlers.fsm import SimpleFlightSearch, FlightSearchStates
import asyncio
import logging

logger = logging.getLogger(__name__)

router = Router()

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
    """Handle text messages for flight search with simplified flow"""
    try:
        # Get current state
        current_state = await state.get_state()
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        
        # Handle based on current state
        if current_state == SimpleFlightSearch.waiting_for_date:
            # User is waiting to enter date
            date_input = message.text.strip()
            if is_date_format(date_input):
                await handle_simple_date_input(message, date_input, user, db, flight_service, typing_service, state)
            else:
                await message.answer("❌ Invalid date format. Use DD.MM.YYYY format")
            return
        
        elif current_state == SimpleFlightSearch.waiting_for_flight_number:
            # User is waiting to enter flight number
            flight_number = message.text.strip()
            if flight_number:
                await handle_simple_flight_number_input(message, flight_number, user, db, flight_service, typing_service, state)
            else:
                await message.answer("❌ Please enter flight number")
            return
        
        # If no state, try to detect what user wants
        # Check if this looks like a date input (DD.MM.YYYY format)
        date_input = message.text.strip()
        if is_date_format(date_input):
            await handle_simple_date_input(message, date_input, user, db, flight_service, typing_service, state)
            return
        
        # Check if this looks like a flight number
        flight_number = message.text.strip()
        if flight_number and not is_date_format(flight_number):
            await handle_simple_flight_number_input(message, flight_number, user, db, flight_service, typing_service, state)
            return
        
        # If neither date nor flight number, show help
        await handle_unknown_input(message, user)
            
    except Exception as e:
        logger.error(f"❌ Error in simplified text handler: {str(e)}")
        await message.answer("❌ An error occurred. Please try again.")

def is_date_format(text: str) -> bool:
    """Check if text matches DD.MM.YYYY format"""
    try:
        # Try to parse as DD.MM.YYYY
        datetime.strptime(text, '%d.%m.%Y')
        return True
    except ValueError:
        try:
            # Try to parse as DD.MM.YY
            datetime.strptime(text, '%d.%m.%y')
            return True
        except ValueError:
            return False

async def handle_simple_date_input(message: Message, date_input: str, user: dict, 
                                 db: DatabaseService, flight_service: FlightService, 
                                 typing_service: TypingService, state: FSMContext):
    """Handle date input in simplified flow"""
    try:
        # Parse the date input
        date_obj = datetime.strptime(date_input, '%d.%m.%Y')
        date = date_obj.strftime('%Y-%m-%d')
        date_display = date_input
        
        # Store the date in state
        await state.update_data(selected_date=date, selected_date_display=date_display)
        
        # Set state to waiting for flight number
        await state.set_state(SimpleFlightSearch.waiting_for_flight_number)
        
        text = f"✅ Date: **{date_display}**\n\n**Step 2 - enter flight number**\n\nExamples: SU100, QR123, 5J944, SU1323A"
        
        # Create keyboard with change date button
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Change date", callback_data="change_date")]
        ])
        
        # Send message and store its ID for later deletion
        sent_message = await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.update_data(instruction_message_id=sent_message.message_id)
        
        # Don't delete messages yet - wait until flight number is entered
        
        logger.info(f"✅ Date input handled: {date_display} for user {message.from_user.id}")
        
    except ValueError:
        await message.answer("❌ Invalid date format. Use DD.MM.YYYY format\n\nExample: 15.07.2025")
    except Exception as e:
        logger.error(f"❌ ERROR in handle_simple_date_input: {str(e)}")
        await message.answer("❌ Error processing date. Please try again.")

async def handle_simple_flight_number_input(message: Message, flight_number: str, user: dict,
                                          db: DatabaseService, flight_service: FlightService,
                                          typing_service: TypingService, state: FSMContext):
    """Handle flight number input in simplified flow"""
    try:
        # Get stored date from state, or use today's date as default
        state_data = await state.get_data()
        selected_date = state_data.get('selected_date')
        selected_date_display = state_data.get('selected_date_display')
        instruction_message_id = state_data.get('instruction_message_id')
        welcome_message_id = state_data.get('welcome_message_id')
        user_command_message_id = state_data.get('user_command_message_id')
        
        if not selected_date:
            # Use today's date as default
            today_date = datetime.now().strftime('%Y-%m-%d')
            today_display = datetime.now().strftime('%d.%m.%Y')
            selected_date = today_date
            selected_date_display = today_display
        
        # Show that we're searching
        search_text = f"🔍 Searching for flight **{flight_number}** on **{selected_date_display}**..."
        search_message = await message.answer(search_text, parse_mode="Markdown")
        
        # Get flight data
        flight_data = await flight_service.get_flight_data(flight_number, selected_date, user['id'])
        
        if not flight_data or (isinstance(flight_data, dict) and flight_data.get('error')):
            # Delete search message first
            try:
                await search_message.delete()
            except Exception as e:
                logger.warning(f"Could not delete search message: {e}")
            
            # Handle different types of errors
            if isinstance(flight_data, dict):
                error_type = flight_data.get('data', {}).get('error') if flight_data.get('data') else flight_data.get('error')
                if error_type == 'no_data':
                    error_message = "❌ Flight not found for the specified date. Check flight number and date."
                elif error_type == 'api_error':
                    error_message = "🚦 High demand, please try later."
                else:
                    error_message = "❌ Flight search error. Please try again."
            else:
                error_message = "❌ Flight not found or search error occurred."
            
            await message.answer(error_message)
            await state.clear()
            return
        
        # Use the original API response format
        if isinstance(flight_data, dict):
            # API response format with message and buttons
            result_text = flight_data.get('message', 'Нет данных о рейсе')
            buttons_data = flight_data.get('buttons', [])
            
            if buttons_data:
                keyboard = build_inline_keyboard(buttons_data)
                await message.answer(result_text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await message.answer(result_text, parse_mode="Markdown")
        else:
            # Fallback for direct flight data
            if isinstance(flight_data, list) and len(flight_data) > 1:
                result_text = format_multiple_flights(flight_data, selected_date_display)
                buttons = get_flight_selection_buttons(flight_data)
                await message.answer(result_text, reply_markup=buttons, parse_mode="Markdown")
            else:
                flight = flight_data[0] if isinstance(flight_data, list) else flight_data
                result_text = format_single_flight(flight, selected_date_display)
                buttons = get_default_buttons()
                await message.answer(result_text, reply_markup=buttons, parse_mode="Markdown")
        
        # NOW delete all previous messages
        try:
            # Delete search message
            await search_message.delete()
            
            # Delete user's flight number input
            await message.delete()
            
            # Delete instruction message
            if instruction_message_id:
                await message.bot.delete_message(message.chat.id, instruction_message_id)
        
            # Delete welcome message
            if welcome_message_id:
                await message.bot.delete_message(message.chat.id, welcome_message_id)
            
            # Delete user's command message (/start or /search)
            if user_command_message_id:
                await message.bot.delete_message(message.chat.id, user_command_message_id)
                
        except Exception as e:
            logger.warning(f"Could not delete some messages: {e}")
        
        # Clear state after successful search
        await state.clear()
        
        logger.info(f"✅ Flight search completed for {flight_number} on {selected_date_display}")
        
    except Exception as e:
        logger.error(f"❌ ERROR in handle_number_input_with_search: {str(e)}")
        # Try to delete search message if it exists
        try:
            if 'search_message' in locals():
                await search_message.delete()
        except Exception as delete_error:
            logger.warning(f"Could not delete search message: {delete_error}")
        
        await message.answer("❌ Flight search error. Please try again.")
        # Clear state on error
        await state.clear()

async def handle_unknown_input(message: Message, user: dict):
    """Handle unknown input in simplified flow"""
    text = """❓ I don't understand your request.

**To search for a flight:**

1️⃣ **Enter date** in one of the following ways:
   • Select a button (yesterday/today/tomorrow)
   • Enter date in DD.MM.YYYY format (example: 15.07.2025)

2️⃣ **Enter flight number** (example: SU100, QR123, 5J944)

**Date examples:**
• 15.07.2025
• 30.07.2025
• 01.08.2025"""
    
    await message.answer(text, parse_mode="Markdown")

def format_single_flight(flight: dict, date_display: str) -> str:
    """Format single flight result using API response format"""
    # Use the message from API response if available
    if isinstance(flight, dict) and 'message' in flight:
        return flight['message']
    
    # Fallback to basic formatting
    flight_number = flight.get('number', 'Unknown')
    status = flight.get('status', 'Unknown')
    departure = flight.get('departure', {})
    arrival = flight.get('arrival', {})
    
    dep_airport = departure.get('airport', {}).get('iata', '--')
    arr_airport = arrival.get('airport', {}).get('iata', '--')
    dep_time = departure.get('scheduledTime', {}).get('local', '--:--')
    arr_time = arrival.get('scheduledTime', {}).get('local', '--:--')
    
    # Extract time from datetime string
    if dep_time != '--:--':
        dep_time = dep_time.split(' ')[1][:5] if ' ' in dep_time else dep_time[:5]
    if arr_time != '--:--':
        arr_time = arr_time.split(' ')[1][:5] if ' ' in arr_time else arr_time[:5]
    
    return f"**{flight_number}** {dep_airport}→{arr_airport}\n\n🛫 Вылет: {dep_time}\n🛬 Прилет: {arr_time}\n\nСтатус: {status}"

def format_multiple_flights(flights: list, date_display: str) -> str:
    """Format multiple flights result"""
    result = f"Found {len(flights)} flights on {date_display}:\n\n"
    for i, flight in enumerate(flights[:5], 1):  # Limit to 5 flights
        flight_number = flight.get('number', 'Unknown')
        departure = flight.get('departure', {})
        arrival = flight.get('arrival', {})
        
        dep_airport = departure.get('airport', {}).get('iata', '--')
        arr_airport = arrival.get('airport', {}).get('iata', '--')
        dep_time = departure.get('scheduledTime', {}).get('local', '--:--')
        
        if dep_time != '--:--':
            dep_time = dep_time.split(' ')[1][:5] if ' ' in dep_time else dep_time[:5]
        
        result += f"{i}. **{flight_number}** {dep_airport}→{arr_airport} {dep_time}\n"
    
    return result

def get_flight_selection_buttons(flights: list):
    """Get buttons for flight selection"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = []
    for i, flight in enumerate(flights[:5], 1):  # Limit to 5 flights
        flight_number = flight.get('number', 'Unknown')
        keyboard.append([InlineKeyboardButton(
            text=f"Flight {i}: {flight_number}",
            callback_data=f"select_flight_{i}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_default_buttons():
    """Get default action buttons"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh"),
            InlineKeyboardButton(text="🔍 New search", callback_data="new_search")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
                            boarding_time_str = boarding_time.strftime('%H:%M')
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