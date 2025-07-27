from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List, Dict, Any
from datetime import datetime
from bot.config import BUTTON_LABELS, CALLBACK_PREFIXES

def get_flight_card_keyboard(flight_id: str = "", subscription_id: str = "", is_subscribed: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    """Create keyboard for flight card"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BUTTON_LABELS["refresh"][lang],
                callback_data=f"{CALLBACK_PREFIXES['refresh']}{flight_id}"
            ),
            InlineKeyboardButton(
                text=BUTTON_LABELS["unsubscribe" if is_subscribed else "subscribe"][lang],
                callback_data=f"{CALLBACK_PREFIXES['unsubscribe' if is_subscribed else 'subscribe']}{subscription_id if is_subscribed else flight_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTON_LABELS["new_search"][lang],
                callback_data=CALLBACK_PREFIXES["new_search"]
            ),
            InlineKeyboardButton(
                text=BUTTON_LABELS["my_flights"][lang],
                callback_data=CALLBACK_PREFIXES["my_flights"]
            )
        ]
    ])
    return keyboard

def get_date_selection_keyboard(flight_number: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Create keyboard for date selection"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BUTTON_LABELS["yesterday"][lang],
                callback_data=f"{CALLBACK_PREFIXES['date_select']}{flight_number}:yesterday"
            ),
            InlineKeyboardButton(
                text=BUTTON_LABELS["today"][lang],
                callback_data=f"{CALLBACK_PREFIXES['date_select']}{flight_number}:today"
            ),
            InlineKeyboardButton(
                text=BUTTON_LABELS["tomorrow"][lang],
                callback_data=f"{CALLBACK_PREFIXES['date_select']}{flight_number}:tomorrow"
            )
        ]
    ])
    return keyboard

def get_feature_request_keyboard(flight_id: Optional[str] = None, lang: str = "en") -> InlineKeyboardMarkup:
    """Create keyboard for feature request"""
    callback_data = f"{CALLBACK_PREFIXES['feature_request']}history"
    if flight_id:
        callback_data += f":{flight_id}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BUTTON_LABELS["request_feature"][lang],
                callback_data=callback_data
            )
        ]
    ])
    return keyboard

def get_user_flights_keyboard(subscriptions: List[Dict[str, Any]], lang: str = "en") -> InlineKeyboardMarkup:
    """Create keyboard for user's subscribed flights"""
    buttons = []
    
    for subscription in subscriptions:
        flight_number = subscription.get('flight_number', 'N/A')
        flight_date = subscription.get('flight_date', 'N/A')
        subscription_id = subscription.get('id', '')
        
        # Format date for display
        try:
            date_obj = datetime.strptime(flight_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d.%m.%Y')
        except:
            formatted_date = flight_date
        
        button_text = f"✈️ {flight_number} {formatted_date}"
        callback_data = f"view_subscription|{subscription_id}"
        
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Add action buttons
    buttons.append([
        InlineKeyboardButton(
            text="🔍 Новый поиск",
            callback_data=CALLBACK_PREFIXES["new_search"]
        ),
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=CALLBACK_PREFIXES["my_flights"]
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_empty_keyboard() -> InlineKeyboardMarkup:
    """Create empty keyboard (for removing existing keyboard)"""
    return InlineKeyboardMarkup(inline_keyboard=[]) 

def get_flight_action_keyboard(is_subscribed: bool, flight_id: str):
    if is_subscribed:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отписаться", callback_data=f"unsubscribe_flight|{flight_id}")],
            [InlineKeyboardButton(text="🗂 Мои рейсы", callback_data="my_flights")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Подписаться", callback_data=f"subscribe_flight|{flight_id}")],
            [InlineKeyboardButton(text="🗂 Мои рейсы", callback_data="my_flights")]
        ]) 