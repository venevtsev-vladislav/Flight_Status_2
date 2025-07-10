from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from bot.services.database import DatabaseService
from bot.services.flight_service import FlightService
from bot.keyboards.inline_keyboards import (
    get_flight_card_keyboard, get_feature_request_keyboard, 
    get_user_flights_keyboard, get_empty_keyboard
)
from bot.config import CALLBACK_PREFIXES, MESSAGE_TEMPLATES, DEFAULT_LANGUAGE

router = Router()

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["refresh"]))
async def handle_refresh_flight(callback: CallbackQuery, db: DatabaseService, flight_service: FlightService):
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
        
        # Get updated flight data
        flight_data = await flight_service.get_flight_data(
            flight['flight_number'], 
            flight['date'], 
            user['id']
        )
        
        # Format response
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        text = flight_data.get('message', '⚠️ Нет данных по рейсу.')
        
        # Check subscription status
        is_subscribed = await db.is_subscribed(user['id'], flight_id)
        keyboard = get_flight_card_keyboard(flight_id, is_subscribed, lang)
        
        # Update message
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer("Flight data updated!")
        
    except Exception as e:
        await callback.answer("Error updating flight data")
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
        
        # Update keyboard
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        keyboard = get_flight_card_keyboard(flight_id, True, lang)
        
        # Update message
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer("Subscribed to flight updates!")
        
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
        success = await db.unsubscribe_from_flight(user['id'], flight_id)
        
        if success:
            # Update keyboard
            lang = user.get('language_code', DEFAULT_LANGUAGE)
            keyboard = get_flight_card_keyboard(flight_id, False, lang)
            
            # Update message
            await callback.message.edit_reply_markup(reply_markup=keyboard)
            await callback.answer("Unsubscribed from flight updates!")
        else:
            await callback.answer("Error unsubscribing from flight")
        
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
        
        # Get user's subscriptions
        subscriptions = await db.get_user_subscriptions(user['id'])
        
        if not subscriptions:
            lang = user.get('language_code', DEFAULT_LANGUAGE)
            text = "You don't have any flight subscriptions yet."
            if lang == "ru":
                text = "У вас пока нет подписок на рейсы."
            
            await callback.message.edit_reply_markup(reply_markup=get_empty_keyboard())
            await callback.message.answer(text)
            await callback.answer()
            return
        
        # Create keyboard with user's flights
        lang = user.get('language_code', DEFAULT_LANGUAGE)
        keyboard = get_user_flights_keyboard(subscriptions, lang)
        
        text = "Your flight subscriptions:"
        if lang == "ru":
            text = "Ваши подписки на рейсы:"
        
        # Update message
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Error loading your flights")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='my_flights_error',
            details={'error': str(e)}
        )

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["date_select"]))
async def handle_date_selection(callback: CallbackQuery, db: DatabaseService, flight_service: FlightService):
    """Handle date selection from keyboard"""
    try:
        # Parse callback data: date:FLIGHT_NUMBER:DATE_TYPE
        parts = callback.data.replace(CALLBACK_PREFIXES["date_select"], "").split(":")
        if len(parts) != 2:
            await callback.answer("Invalid date selection")
            return
        
        flight_number, date_type = parts
        
        # Convert date type to actual date
        if date_type == "yesterday":
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif date_type == "today":
            date = datetime.now().strftime('%Y-%m-%d')
        elif date_type == "tomorrow":
            date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            await callback.answer("Invalid date type")
            return
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Process the flight request
        from bot.handlers.text import process_flight_request
        await process_flight_request(
            callback.message, flight_number, date, user, db, flight_service, 
            user.get('language_code', DEFAULT_LANGUAGE)
        )
        
        # Remove the date selection message
        await callback.message.delete()
        await callback.answer()
        
    except Exception as e:
        await callback.answer("Error processing date selection")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='date_selection_error',
            details={'error': str(e), 'callback_data': callback.data}
        )

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["feature_request"]))
async def handle_feature_request(callback: CallbackQuery, db: DatabaseService):
    """Handle feature request button"""
    try:
        # Parse callback data: feature:FEATURE_CODE:FLIGHT_ID
        parts = callback.data.replace(CALLBACK_PREFIXES["feature_request"], "").split(":")
        feature_code = parts[0]
        flight_id = parts[1] if len(parts) > 1 else None
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Save feature request
        await db.save_feature_request(
            user_id=user['id'],
            feature_code=feature_code,
            flight_id=flight_id,
            comment="Requested via inline button"
        )
        
        # Update keyboard to show it's been requested
        await callback.message.edit_reply_markup(reply_markup=get_empty_keyboard())
        await callback.answer("Feature request saved! We'll notify you when it's ready.")
        
    except Exception as e:
        await callback.answer("Error saving feature request")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='feature_request_error',
            details={'error': str(e), 'callback_data': callback.data}
        ) 

@router.callback_query(F.data.startswith("select_flight_"))
async def handle_select_flight(callback: CallbackQuery, db: DatabaseService, flight_service: FlightService):
    # Пример callback_data: select_flight_SU1314_2025-07-07 или select_flight_SU1314_2025-07-07_07:10
    data = callback.data.replace("select_flight_", "")
    parts = data.split("_")
    flight_number = parts[0]
    date = parts[1] if len(parts) > 1 else None
    # time = parts[2] if len(parts) > 2 else None  # пока не используем

    user = await db.get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username
    )
    lang = user.get('language_code', 'en')

    # Новый запрос к backend для выбранного рейса
    await process_flight_request(
        callback.message, flight_number, date, user, db, flight_service, lang
    )
    await callback.answer() 