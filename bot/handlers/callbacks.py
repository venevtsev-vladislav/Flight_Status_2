from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from bot.services.database import DatabaseService
from bot.services.flight_service import FlightService
from bot.services.language_service import LanguageService
from bot.services.typing_service import TypingService
from bot.services.search_service import SearchService
from bot.keyboards.inline_keyboards import (
    get_flight_card_keyboard, get_feature_request_keyboard, 
    get_user_flights_keyboard, get_empty_keyboard
)
from bot.config import CALLBACK_PREFIXES, MESSAGE_TEMPLATES, DEFAULT_LANGUAGE
import asyncio
from aiogram.types import InlineKeyboardMarkup

router = Router()

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["refresh"]))
async def handle_refresh_flight(callback: CallbackQuery, db: DatabaseService, 
                              flight_service: FlightService, typing_service: TypingService):
    """Handle refresh flight button"""
    try:
        flight_id = callback.data.replace(CALLBACK_PREFIXES["refresh"], "")
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Get flight details
        flight_response = db.supabase.table('flights').select('*').eq('id', flight_id).execute()
        if not flight_response.data:
            await callback.answer("Flight not found")
            return
        
        flight = flight_response.data[0]
        
        # Show typing indicator while getting updated flight data
        async def get_flight_data():
            return await flight_service.get_flight_data(
                flight['flight_number'], 
                flight['date'], 
                user['id']
            )
        
        flight_data = await typing_service.show_typing_until(
            callback.message.chat.id,
            asyncio.create_task(get_flight_data())
        )
        
        # Format response
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        text = flight_data.get('message', MESSAGE_TEMPLATES["no_data_found"][lang])
        
        # Check subscription status
        is_subscribed = await db.is_subscribed(user['id'], flight_id)
        keyboard = get_flight_card_keyboard(flight_id, is_subscribed, lang)
        
        # Update message
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Error refreshing flight data")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='refresh_flight_error',
            details={'error': str(e), 'flight_id': flight_id if 'flight_id' in locals() else None}
        )

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["subscribe"]))
async def handle_subscribe_flight(callback: CallbackQuery, db: DatabaseService):
    """Handle subscribe to flight button"""
    try:
        flight_id = callback.data.replace(CALLBACK_PREFIXES["subscribe"], "")
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Subscribe to flight
        await db.subscribe_to_flight(user['id'], flight_id)
        
        # Update keyboard to show unsubscribe button
        is_subscribed = True
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        keyboard = get_flight_card_keyboard(flight_id, is_subscribed, lang)
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer("Subscribed to flight updates")
        
    except Exception as e:
        await callback.answer("Error subscribing to flight")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='subscribe_flight_error',
            details={'error': str(e), 'flight_id': flight_id if 'flight_id' in locals() else None}
        )

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["unsubscribe"]))
async def handle_unsubscribe_flight(callback: CallbackQuery, db: DatabaseService):
    """Handle unsubscribe from flight button"""
    try:
        flight_id = callback.data.replace(CALLBACK_PREFIXES["unsubscribe"], "")
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Unsubscribe from flight
        await db.unsubscribe_from_flight(user['id'], flight_id)
        
        # Update keyboard to show subscribe button
        is_subscribed = False
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        keyboard = get_flight_card_keyboard(flight_id, is_subscribed, lang)
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer("Unsubscribed from flight updates")
        
    except Exception as e:
        await callback.answer("Error unsubscribing from flight")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='unsubscribe_flight_error',
            details={'error': str(e), 'flight_id': flight_id if 'flight_id' in locals() else None}
        )

@router.callback_query(F.data == CALLBACK_PREFIXES["new_search"])
async def handle_new_search(callback: CallbackQuery, db: DatabaseService):
    """Handle new search button"""
    try:
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        text = MESSAGE_TEMPLATES["new_search"][lang]
        
        # Remove keyboard and send new message
        await callback.message.edit_reply_markup(reply_markup=get_empty_keyboard())
        await callback.message.answer(text)
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Error starting new search")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='new_search_error',
            details={'error': str(e)}
        )

@router.callback_query(F.data == CALLBACK_PREFIXES["my_flights"])
async def handle_my_flights(callback: CallbackQuery, db: DatabaseService):
    """Handle my flights button"""
    try:
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Get user's subscribed flights
        subscriptions = await db.get_user_subscriptions(user['id'])
        
        if not subscriptions:
            lang = user.get('language_code', DEFAULT_LANGUAGE)
            text = "You don't have any subscribed flights yet."
            await callback.message.answer(text)
        else:
            # Create keyboard with user's flights
            keyboard = get_user_flights_keyboard(subscriptions, user.get('language_code', DEFAULT_LANGUAGE))
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Error loading your flights")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='my_flights_error',
            details={'error': str(e)}
        )

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["feature_request"]))
async def handle_feature_request(callback: CallbackQuery, db: DatabaseService):
    """Handle feature request button"""
    try:
        # Parse callback data: feature:FLIGHT_ID:FEATURE_CODE
        data = callback.data.replace(CALLBACK_PREFIXES["feature_request"], "")
        parts = data.split(":")
        
        if len(parts) < 2:
            await callback.answer("Invalid feature request")
            return
        
        flight_id = parts[0]
        feature_code = parts[1]
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Save feature request
        await db.save_feature_request(user['id'], feature_code, flight_id)
        
        await callback.answer("Feature request saved! We'll notify you when it's ready.")
        
    except Exception as e:
        await callback.answer("Error saving feature request")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='feature_request_error',
            details={'error': str(e), 'callback_data': callback.data}
        )

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["date_select"]))
async def handle_date_selection(callback: CallbackQuery, db: DatabaseService, 
                              flight_service: FlightService, typing_service: TypingService,
                              search_service: SearchService):
    """Handle date selection from keyboard"""
    try:
        # Parse callback data: date:DATE_TYPE (e.g., date:today, date:yesterday, date:tomorrow)
        date_type = callback.data.replace(CALLBACK_PREFIXES["date_select"], "")
        
        # Convert date type to actual date
        if date_type == "yesterday":
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            date_display = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
        elif date_type == "today":
            date = datetime.now().strftime('%Y-%m-%d')
            date_display = datetime.now().strftime('%d.%m.%Y')
        elif date_type == "tomorrow":
            date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            date_display = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
        else:
            await callback.answer("Invalid date type")
            return
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Save date to active search (this automatically sets state to waiting_for_number)
        await search_service.update_search_with_date(
            telegram_id=callback.from_user.id,
            user_id=user['id'],
            search_date=date,
            parsed_data={'date': date, 'date_type': date_type}
        )
        
        # Acknowledge the selection
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        date_text = {
            "yesterday": "вчера" if lang == "ru" else "yesterday",
            "today": "сегодня" if lang == "ru" else "today", 
            "tomorrow": "завтра" if lang == "ru" else "tomorrow"
        }.get(date_type, date_type)
        
        await callback.answer(f"Selected date: {date_text}")
        
        # Send message with example format
        text = f"Вы выбрали дату: {date_text} ({date_display})\n\nТеперь введите номер рейса:"
        await callback.message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        await callback.answer("Error processing date selection")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='date_selection_error',
            details={'error': str(e), 'callback_data': callback.data}
        )

@router.callback_query(F.data.startswith("select_flight"))
async def handle_select_flight(callback: CallbackQuery, db: DatabaseService, 
                             flight_service: FlightService, typing_service: TypingService):
    """Handle selection of specific flight from multiple flights"""
    try:
        # Новый формат callback_data: select_flight|flight_number|date|dep_time|dep_iata|arr_iata|flight_type
        data = callback.data.replace("select_flight|", "")
        parts = data.split("|")
        if len(parts) < 6:
            await callback.answer("Invalid flight selection")
            return
        flight_number = parts[0]
        date = parts[1]
        dep_time = parts[2]
        dep_iata = parts[3]
        arr_iata = parts[4]
        flight_type = parts[5]  # 'departure' или 'arrival'

        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        lang = user.get('language_code', 'en')

        # Выбираем dateLocalRole для API
        date_local_role = 'Departure' if flight_type == 'departure' else 'Arrival'

        # Получаем данные рейса через API с фильтрацией
        flights_data = await flight_service.get_flight_data(flight_number, date, user['id'], date_local_role)
        flights = flights_data.get('data', [])
        
        # Если API вернул отфильтрованные данные, используем готовое сообщение
        if flights_data.get('message'):
            text = flights_data['message']
        else:
            # Если нет готового сообщения, показываем ошибку
            await callback.answer("Flight not found for selection")
            return
        
        # Создаем пустую клавиатуру для отображения только сообщения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Error processing flight selection")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='select_flight_error',
            details={'error': str(e), 'callback_data': callback.data}
        ) 