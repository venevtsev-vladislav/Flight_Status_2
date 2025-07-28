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
from bot.config import CALLBACK_PREFIXES, MESSAGE_TEMPLATES, DEFAULT_LANGUAGE, AERODATABOX_API_KEY, AERODATABOX_API_HOST, SUPABASE_URL
import asyncio
from aiogram.types import InlineKeyboardMarkup
import logging
import re
import httpx
from bot.handlers.fsm import SimpleFlightSearch

WEBHOOK_URL = "https://taanbgxivbqcuaxcspjx.supabase.co/functions/v1/flight-webhook"

async def create_subscription_via_supabase(user_id: str, flight_number: str, date: str, callback_url: str) -> dict:
    """Создает подписку через Supabase endpoint"""
    try:
        logger.info(f"🔍 DEBUG: Starting create_subscription_via_supabase")
        logger.info(f"🔍 DEBUG: user_id={user_id}, flight_number={flight_number}, date={date}")
        
        url = f"{SUPABASE_URL}/functions/v1/create-subscription"
        
        payload = {
            'user_id': user_id,
            'flight_number': flight_number,
            'flight_date': date,
            'callback_url': callback_url
        }
        
        logger.info(f"[Supabase] Request URL: {url}")
        logger.info(f"[Supabase] Request payload: {payload}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            
            logger.info(f"[Supabase] Response status: {response.status_code}")
            logger.info(f"[Supabase] Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        "success": True,
                        "subscription_id": data.get('subscription_id'),
                        "message": "Subscription created successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "supabase_error",
                        "message": data.get('error', 'Unknown error from Supabase')
                    }
            else:
                logger.error(f"❌ Error creating subscription via Supabase: {response.status_code} {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": f"Failed to create subscription: {response.text}"
                }
                
    except Exception as e:
        logger.error(f"❌ Exception creating subscription via Supabase: {e}")
        return {
            "success": False,
            "error": "exception",
            "message": f"Exception creating subscription: {str(e)}"
        }

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == CALLBACK_PREFIXES["refresh"])
async def handle_refresh_flight(callback: CallbackQuery, db: DatabaseService, 
                              flight_service: FlightService, typing_service: TypingService):
    """Handle refresh flight button"""
    logger.info(f"🔍 DEBUG: Refresh callback triggered with data: {callback.data}")
    try:
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Безопасно получаем текст сообщения
        message_text = getattr(callback.message, 'text', None)
        if not message_text:
            await callback.answer("❌ Нет текста сообщения для обновления рейса")
            return
        logger.info(f"🔍 DEBUG: Refreshing flight data from message: {message_text}")
        
        # Ищем номер рейса в формате "QR 30 EDI→DOH" или "QR030 EDI→DOH"
        flight_match = re.search(r'([A-Z0-9]{2,3}\s?\d{1,4})\s+([A-Z]{3})→([A-Z]{3})', message_text)
        if not flight_match:
            await callback.answer("❌ Could not parse flight information from message")
            return
        flight_number = flight_match.group(1).replace(' ', '')
        dep_iata = flight_match.group(2)
        arr_iata = flight_match.group(3)
        
        # Ищем дату в формате "(DD.MM.YYYY)"
        date_match = re.search(r'\((\d{2}\.\d{2}\.\d{4})\)', message_text)
        if not date_match:
            await callback.answer("❌ Could not parse date from message")
            return
        date_str = date_match.group(1)
        # Конвертируем дату из DD.MM.YYYY в YYYY-MM-DD
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        date = date_obj.strftime('%Y-%m-%d')
        
        logger.info(f"🔍 DEBUG: Parsed flight_number={flight_number}, date={date}")
        
        # Показываем индикатор загрузки
        await callback.answer("🔄 Refreshing flight data...")
        
        # Получаем обновленные данные
        flight_data = await flight_service.get_flight_data(flight_number, date, user['id'])
        
        if flight_data.get('error'):
            await callback.answer("❌ Error refreshing flight data")
            return
        
        # Обновляем сообщение
        text = flight_data.get('message', 'No data available')
        buttons = flight_data.get('buttons')
        
        if buttons:
            from bot.handlers.text import build_inline_keyboard
            keyboard = build_inline_keyboard(buttons)
        else:
            from aiogram.types import InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        # Безопасно вызываем edit_text или answer
        if hasattr(callback.message, 'edit_text') and callable(getattr(callback.message, 'edit_text', None)):
            await callback.message.edit_text(text, reply_markup=keyboard)
        elif hasattr(callback.message, 'answer') and callable(getattr(callback.message, 'answer', None)):
            await callback.message.answer(text, reply_markup=keyboard)
        else:
            await callback.answer(text)
        await callback.answer("✅ Flight data refreshed!")
        
    except Exception as e:
        logger.error(f"❌ Error in handle_refresh_flight: {str(e)}")
        await callback.answer("❌ Error refreshing flight data")
        user_id = user['id'] if 'user' in locals() and user and 'id' in user else None
        await db.log_audit(
            user_id=user_id,
            action='refresh_flight_error',
            details={'error': str(e)}
        )

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["subscribe"]))
async def handle_subscribe_flight(callback: CallbackQuery, db: DatabaseService, 
                                flight_service: FlightService, typing_service: TypingService):
    logger.info(f"🔍 DEBUG: Subscribe callback triggered with data: {callback.data}")
    """Handle subscribe to flight button"""
    logger.info(f"🔍 DEBUG: Subscribe callback triggered with data: {callback.data}")
    try:
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Безопасно получаем текст сообщения
        message_text = getattr(callback.message, 'text', None)
        if not message_text:
            await callback.answer("❌ Нет текста сообщения для парсинга рейса")
            return
        logger.info(f"🔍 DEBUG: Subscribing to flight from message: {message_text}")
        
        # Ищем номер рейса в формате "QR 1197 ELQ→DOH" или "QR1197 ELQ→DOH"
        flight_match = re.search(r'([A-Z0-9]{2,3}\s?\d{1,4})\s+([A-Z]{3})→([A-Z]{3})', message_text)
        if not flight_match:
            await callback.answer("❌ Could not parse flight information from message")
            return
        flight_number = flight_match.group(1).replace(' ', '')
        dep_iata = flight_match.group(2)
        arr_iata = flight_match.group(3)
        
        # Ищем дату в формате "(DD.MM.YYYY)"
        date_match = re.search(r'\((\d{2}\.\d{2}\.\d{4})\)', message_text)
        if not date_match:
            await callback.answer("❌ Could not parse date from message")
            return
        date_str = date_match.group(1)
        # Конвертируем дату из DD.MM.YYYY в YYYY-MM-DD
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        date = date_obj.strftime('%Y-%m-%d')
        
        # Ищем название авиакомпании
        airline_match = re.search(r'Airline: ([^\n]+)', message_text)
        airline_name = airline_match.group(1) if airline_match else "Unknown"
        
        logger.info(f"🔍 DEBUG: Subscribing to flight_number={flight_number}, date={date}, airline={airline_name}")
        
        # Проверяем, не подписан ли уже пользователь на этот рейс
        existing_subscription = await db.get_flight_subscription(
            user_id=user['id'],
            flight_number=flight_number,
            flight_date=date
        )
        logger.info(f"🔍 DEBUG: Existing subscription check result: {existing_subscription}")
        if existing_subscription:
            logger.info(f"🔍 DEBUG: User already subscribed, returning")
            await callback.answer("❌ You are already subscribed to this flight!")
            return
        
        logger.info(f"🔍 DEBUG: Proceeding with subscription creation")
        
        # 1. Создаём подписку на рейс через AeroDataBox
        try:
            # Получаем callback_url для Supabase
            callback_url = WEBHOOK_URL
            logger.info(f"🔍 DEBUG: About to call create_subscription_via_supabase with callback_url: {callback_url}")
            logger.info(f"🔍 DEBUG: Parameters: user_id={user['id']}, flight_number={flight_number}, date={date}")
            webhook_result = await create_subscription_via_supabase(user['id'], flight_number, date, callback_url)
            logger.info(f"🔍 DEBUG: create_subscription_via_supabase result: {webhook_result}")
            
            # Проверяем результат создания webhook
            logger.info(f"🔍 DEBUG: Webhook result: {webhook_result}")
            if not webhook_result.get('success', False):
                error_message = webhook_result.get('message', 'Unknown error')
                logger.error(f"❌ Webhook creation failed: {error_message}")
                await callback.answer(f"❌ Ошибка создания подписки: {error_message}")
                return
            
            subscription_id = webhook_result.get('subscription_id')
            logger.info(f"🔍 DEBUG: Supabase subscriptionId: {subscription_id}")
        except Exception as e:
            logger.error(f"❌ Error creating Supabase webhook: {e}")
            await callback.answer("❌ Не удалось создать подписку на рейс (Supabase)")
            return
        
        # 2. Сохраняем подписку в Supabase
        subscription_data = {
            'user_id': user['id'],
            'flight_number': flight_number,
            'flight_date': date,
            'departure_airport': dep_iata,
            'arrival_airport': arr_iata,
            'airline': airline_name,
            'status': 'active',
            'subscription_id': subscription_id
        }
        logger.info(f"🔍 DEBUG: Перед созданием подписки: {subscription_data}")
        db_subscription_id = await db.create_flight_subscription(subscription_data)
        logger.info(f"🔍 DEBUG: Результат создания подписки: {db_subscription_id}")
        if db_subscription_id:
            await callback.answer("✅ Successfully subscribed to flight!")
            await db.log_audit(
                user_id=user['id'],
                action='flight_subscription_created',
                details={
                    'subscription_id': db_subscription_id,
                    'flight_number': flight_number,
                    'flight_date': date
                }
            )
            # Отправляем короткое сообщение пользователю
            await callback.message.answer(f"✅ Подписка на рейс {flight_number} {date_str} успешно создана!")
            
            # Обновляем клавиатуру (кнопка должна стать 'Отписаться')
            from bot.keyboards.inline_keyboards import get_flight_card_keyboard
            flight = await db.get_or_create_flight(flight_number, date)
            flight_id = flight.get('id', '')
            keyboard = get_flight_card_keyboard(flight_id=flight_id, subscription_id=db_subscription_id, is_subscribed=True)
            if hasattr(callback.message, 'edit_reply_markup') and callable(getattr(callback.message, 'edit_reply_markup', None)):
                await callback.message.edit_reply_markup(reply_markup=keyboard)
        else:
            logger.error(f"❌ Не удалось создать подписку: {subscription_data}")
            await callback.answer("❌ Failed to create subscription")
        
    except Exception as e:
        logger.error(f"❌ Error in handle_subscribe_flight: {str(e)}")
        await callback.answer("❌ Error creating subscription")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='subscribe_flight_error',
            details={'error': str(e)}
        )

# Обработка кнопки 'Подробнее'
@router.callback_query(F.data.startswith("details|"))
async def handle_details(callback: CallbackQuery, db: DatabaseService, flight_service: FlightService):
    logger.info(f"🔍 DEBUG: Details callback triggered with data: {callback.data}")
    try:
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        flight_id = callback.data.split("|", 1)[1]
        # Получаем flight из БД
        flight = await db.get_flight_by_id(flight_id)
        if not flight:
            await callback.answer("Рейс не найден")
            return
        flight_number = flight.get('flight_number')
        date = flight.get('date')
        # Получаем подробную информацию
        flight_data = await flight_service.get_flight_data(flight_number, date, user['id'])
        text = flight_data.get('message', 'Нет данных')
        # Кнопки как при обычном поиске
        from bot.keyboards.inline_keyboards import get_flight_card_keyboard
        # Проверяем подписку по flight_number и date
        subscription = await db.get_flight_subscription(user['id'], flight_number, date)
        is_subscribed = subscription is not None
        subscription_id = subscription.get('id', '') if subscription else ''
        keyboard = get_flight_card_keyboard(flight_id=flight_id, subscription_id=subscription_id, is_subscribed=is_subscribed)
        await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Error in handle_details: {e}")
        await callback.answer("Ошибка при получении подробной информации")

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["unsubscribe"]))
async def handle_unsubscribe_flight(callback: CallbackQuery, db: DatabaseService):
    """Handle unsubscribe from flight button"""
    logger.info(f"🔍 DEBUG: Unsubscribe callback triggered with data: {callback.data}")
    try:
        subscription_id = callback.data.replace(CALLBACK_PREFIXES["unsubscribe"], "")
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Получаем подписку из БД
        subscription = await db.get_subscription_by_id(subscription_id)
        if not subscription or subscription['user_id'] != user['id']:
            await callback.answer("❌ Подписка не найдена")
            return
            
        flight_number = subscription.get('flight_number', '')
        flight_date = subscription.get('flight_date', '')
        
        # Unsubscribe from flight
        success = await db.unsubscribe_from_flight(user['id'], subscription_id)
        if success:
            # Сообщение об успешной отписке
            await callback.message.answer(f"✅ Вы успешно отписались от рейса {flight_number} {flight_date}")
            # Кнопки 'Найти новый рейс' и 'Мои рейсы'
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Новый поиск", callback_data=CALLBACK_PREFIXES["new_search"])],
                [InlineKeyboardButton(text="🗂 Мои рейсы", callback_data=CALLBACK_PREFIXES["my_flights"])]
            ])
            await callback.message.answer("Выберите действие:", reply_markup=keyboard)
        else:
            await callback.message.answer("❌ Ошибка при отписке от рейса")
            
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Error in handle_unsubscribe_flight: {e}")
        await callback.answer("Ошибка при отписке от рейса")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='unsubscribe_flight_error',
            details={'error': str(e), 'subscription_id': subscription_id if 'subscription_id' in locals() else None}
        )

@router.callback_query(F.data == CALLBACK_PREFIXES["new_search"])
async def handle_new_search(callback: CallbackQuery, db: DatabaseService):
    """Handle new search button"""
    logger.info(f"🔍 DEBUG: New search callback triggered with data: {callback.data}")
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
    logger.info(f"🔍 DEBUG: My flights callback triggered with data: {callback.data}")
    try:
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Get user's subscribed flights
        subscriptions = await db.get_user_subscriptions(user['id'])
        
        if not subscriptions:
            text = "🗂 У вас пока нет подписок на рейсы.\n\nНайдите рейс и нажмите кнопку '🔔 Subscribe' чтобы получать уведомления об изменениях."
            await callback.message.answer(text)
        else:
            # Create message with subscription count
            text = f"🗂 Ваши подписки на рейсы ({len(subscriptions)}):\n\nВыберите рейс для просмотра актуальной информации:"
            
            # Create keyboard with user's flights
            keyboard = get_user_flights_keyboard(subscriptions, user.get('language_code', DEFAULT_LANGUAGE))
            await callback.message.answer(text, reply_markup=keyboard)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Error in handle_my_flights: {e}")
        await callback.answer("Error loading your flights")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='my_flights_error',
            details={'error': str(e)}
        )

@router.callback_query(F.data.startswith("view_subscription|"))
async def handle_view_subscription(callback: CallbackQuery, db: DatabaseService, flight_service: FlightService):
    """Handle viewing a specific subscription"""
    logger.info(f"🔍 DEBUG: View subscription callback triggered with data: {callback.data}")
    try:
        # Parse subscription ID
        subscription_id = callback.data.split("|", 1)[1]
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Get subscription details
        subscription = await db.get_subscription_by_id(subscription_id)
        if not subscription or subscription['user_id'] != user['id']:
            await callback.answer("❌ Subscription not found")
            return
        
        # Get current flight data
        flight_number = subscription['flight_number']
        flight_date = subscription['flight_date']
        
        flight_data = await flight_service.get_flight_data(flight_number, flight_date)
        
        if flight_data.get('success'):
            text = flight_data.get('message', 'No flight data available')
            
            # Create keyboard with unsubscribe option
            from bot.keyboards.inline_keyboards import get_flight_card_keyboard
            keyboard = get_flight_card_keyboard(subscription_id=subscription_id, is_subscribed=True)
            
            await callback.message.answer(text, reply_markup=keyboard)
            await callback.answer()
        else:
            await callback.answer("❌ Failed to load flight data")
            
    except Exception as e:
        logger.error(f"❌ Error in handle_view_subscription: {e}")
        await callback.answer("❌ Error loading subscription")

@router.callback_query(F.data.startswith(CALLBACK_PREFIXES["feature_request"]))
async def handle_feature_request(callback: CallbackQuery, db: DatabaseService):
    """Handle feature request button"""
    logger.info(f"🔍 DEBUG: Feature request callback triggered with data: {callback.data}")
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
    logger.info(f"🔍 DEBUG: Date selection callback triggered with data: {callback.data}")
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
    logger.info(f"🔍 DEBUG: Select flight callback triggered with data: {callback.data}")
    try:
        # Получаем пользователя для правильного user_id
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # Новый формат callback_data: select_flight|<uuid>
        data = callback.data.replace("select_flight|", "").strip()
        uuid = data
        if not uuid:
            await callback.answer("Invalid flight selection")
            return
            
        # Получаем flight_detail по uuid
        flight_detail = await db.get_flight_detail_by_uuid(uuid)
        if not flight_detail:
            await callback.answer("Flight not found")
            return
            
        logger.info(f"🔍 DEBUG: Found flight_detail: {flight_detail}")
            
        # Формируем сообщение из raw_data или normalized
        from bot.handlers.text import formatTelegramMessage, build_inline_keyboard
        from bot.keyboards.inline_keyboards import get_flight_card_keyboard
        
        flight_data = flight_detail.get('raw_data') or flight_detail.get('normalized')
        
        # Если flight_data это массив, берем первый элемент (это должен быть конкретный рейс)
        if isinstance(flight_data, list) and len(flight_data) > 0:
            flight_data = flight_data[0]  # Берем первый рейс из массива
        
        logger.info(f"🔍 DEBUG: Processing flight_data: {type(flight_data)} - {flight_data}")
        
        try:
            # Проверяем, что flight_data не None и является словарем
            if not flight_data or not isinstance(flight_data, dict):
                logger.error(f"❌ Invalid flight_data: {type(flight_data)} - {flight_data}")
                text = "⚠️ Ошибка: неверные данные рейса"
            else:
                text = formatTelegramMessage(flight_data)
                logger.info(f"🔍 DEBUG: Generated text: {text[:200]}...")
        except Exception as format_error:
            logger.error(f"❌ Error formatting message: {format_error}")
            text = f"✈️ {flight_data.get('number', 'Unknown')} - {flight_data.get('status', 'Unknown')}"
        
        # Добавляем стандартные кнопки действий для одного рейса
        # Используем flight_detail.id как flight_id для кнопки Subscribe
        keyboard = get_flight_card_keyboard(flight_id=uuid, subscription_id="", is_subscribed=False)
        
        # Отправляем новое сообщение с одним рейсом
        try:
            await callback.message.answer(text, reply_markup=keyboard)
            await callback.answer("✅ Выбран рейс")
        except Exception as send_error:
            logger.error(f"❌ Error sending message: {send_error}")
            await callback.answer("❌ Ошибка отправки сообщения")
        
    except Exception as e:
        await callback.answer("Error processing flight selection")
        # Используем правильный user_id для audit log
        try:
            user = await db.get_or_create_user(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username
            )
            await db.log_audit(
                user_id=user['id'],
                action='select_flight_error',
                details={'error': str(e), 'callback_data': callback.data}
            )
        except:
            pass  # Игнорируем ошибки audit log 

@router.callback_query(F.data.startswith("simple_date:"))
async def handle_simple_date_selection(callback: CallbackQuery, db: DatabaseService, 
                                     flight_service: FlightService, typing_service: TypingService,
                                     state: FSMContext):
    """Handle simplified date selection"""
    logger.info(f"🔍 DEBUG: Simple date selection callback triggered with data: {callback.data}")
    try:
        # Parse callback data: simple_date:DATE_TYPE
        date_type = callback.data.replace("simple_date:", "")
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        if date_type == "custom":
            # User wants to enter custom date
            await state.set_state(SimpleFlightSearch.waiting_for_date)
            await callback.message.edit_text(
                "📝 **Введите дату в формате ДД.ММ.ГГГГ**\n\nНапример: 15.07.2025",
                parse_mode="Markdown"
            )
            await callback.answer("Введите дату")
            return
        
        # Convert date type to actual date
        from datetime import datetime, timedelta
        if date_type == "yesterday":
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            date_display = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
            date_text = "вчера"
        elif date_type == "today":
            date = datetime.now().strftime('%Y-%m-%d')
            date_display = datetime.now().strftime('%d.%m.%Y')
            date_text = "сегодня"
        elif date_type == "tomorrow":
            date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            date_display = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
            date_text = "завтра"
        else:
            await callback.answer("❌ Неверный тип даты")
            return
        
        # Store date in state and set state to waiting for flight number
        await state.update_data(selected_date=date, selected_date_display=date_display)
        await state.set_state(SimpleFlightSearch.waiting_for_flight_number)
        
        # Send message asking for flight number
        text = f"✅ Дата: **{date_text}** ({date_display})\n\n**Шаг 2 - введите номер рейса**\n\nНапример: SU100, QR123, 5J944, SU1323A"
        
        # Create keyboard with change date button
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Изменить дату", callback_data="change_date")]
        ])
        
        # Send new message and store its ID for later deletion
        sent_message = await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.update_data(instruction_message_id=sent_message.message_id)
        
        # Don't delete messages yet - wait until flight number is entered
        await callback.answer(f"Выбрана дата: {date_text}")
        
        # Log the date selection
        await db.log_audit(
            user_id=user['id'],
            action='simple_date_selected',
            details={'date_type': date_type, 'date': date, 'date_display': date_display}
        )
        
    except Exception as e:
        logger.error(f"❌ Error in handle_simple_date_selection: {str(e)}")
        await callback.answer("❌ Ошибка выбора даты")
        await db.log_audit(
            user_id=user['id'] if 'user' in locals() else None,
            action='simple_date_selection_error',
            details={'error': str(e), 'callback_data': callback.data}
        )

@router.callback_query(F.data.startswith("simple_flight_number:"))
async def handle_simple_flight_number(callback: CallbackQuery, db: DatabaseService, 
                                    flight_service: FlightService, typing_service: TypingService):
    """Handle flight number from simplified flow"""
    logger.info(f"🔍 DEBUG: Simple flight number callback triggered with data: {callback.data}")
    try:
        # Parse flight number from callback data
        flight_number = callback.data.replace("simple_flight_number:", "")
        
        # Get user
        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        # For now, we'll handle this in the text handler
        # This is a placeholder for future implementation
        
        await callback.answer(f"Выбран рейс: {flight_number}")
        
    except Exception as e:
        logger.error(f"❌ Error in handle_simple_flight_number: {str(e)}")
        await callback.answer("❌ Ошибка выбора рейса") 

@router.callback_query(F.data == "change_date")
async def handle_change_date(callback: CallbackQuery, state: FSMContext):
    """Handle change date button - return to step 1"""
    try:
        # Clear current state and return to date selection
        await state.clear()
        
        # Get user language (default to Russian)
        lang = "ru"
        
        # Send new date selection message
        from bot.handlers.start import get_simple_date_keyboard
        keyboard = get_simple_date_keyboard(lang)
        
        text = "**Шаг 1 - укажите дату или выберите ниже**"
        sent_message = await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
        # Store the new welcome message ID
        await state.update_data(welcome_message_id=sent_message.message_id)
        
        # Delete the current instruction message
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete instruction message: {e}")
        
        await callback.answer("Выберите новую дату")
        
        logger.info(f"✅ Change date requested for user {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR in handle_change_date: {str(e)}")
        await callback.answer("❌ Ошибка. Попробуйте еще раз.") 