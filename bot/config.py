import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot settings
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Supabase settings
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")

# Edge Functions URLs
PARSE_FLIGHT_URL = f"{SUPABASE_URL}/functions/v1/parse-flight"
FLIGHT_API_URL = f"{SUPABASE_URL}/functions/v1/flight-api"

# Bot settings
BOT_VERSION = "1.0.0"
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en", "ru"]

# AeroDataBox API settings (RapidAPI)
AERODATABOX_API_KEY = os.getenv('AERODATABOX_API_KEY')
AERODATABOX_API_HOST = 'aerodatabox.p.rapidapi.com'
AERODATABOX_API_URL = 'https://aerodatabox.p.rapidapi.com'

# Flight API settings
FLIGHT_API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Message templates
MESSAGE_TEMPLATES = {
    "welcome": {
        "en": "👋 Hello, {username}!\nI can help you track flight status.\nJust type flight number and date, for example:\n✈️ SU100 today\n📅 AFL123 05.07.2025",
        "ru": "👋 Привет, {username}!\nЯ помогу отследить статус рейса.\nПросто напиши номер рейса и дату, например:\n✈️ SU100 сегодня\n📅 AFL123 05.07.2025"
    },
    "parse_error": {
        "en": "⚠️ Sorry, I couldn't recognize the flight number or date.\nPlease use the format like: SU100 today or SU100 05.07.2025",
        "ru": "⚠️ Извините, не удалось распознать номер рейса или дату.\nПожалуйста, используйте формат: SU100 сегодня или SU100 05.07.2025"
    },
    "no_date_request": {
        "en": "I found flight number: {flight_number}.\nNow choose a date or type the date manually (DD.MM.YYYY):",
        "ru": "Я нашел номер рейса: {flight_number}.\nТеперь выберите дату или введите дату вручную (ДД.ММ.ГГГГ):"
    },
    "no_number_request": {
        "en": "You entered a date: {date}\nPlease enter the flight number (e.g. QR123)",
        "ru": "Вы ввели дату: {date}\nПожалуйста, введите номер рейса (например QR123)"
    },
    "future_flight": {
        "en": "📅 Flight {flight_number} on {date} is too far in the future.\nWe've saved your request and will notify you once data is available.",
        "ru": "📅 Рейс {flight_number} на {date} слишком далеко в будущем.\nМы сохранили ваш запрос и уведомим, когда данные станут доступны."
    },
    "past_flight": {
        "en": "❌ This flight is too far in the past.\nHistorical data is not yet supported.\n🚧 Feature under development.\n👇 Tap to request early access.",
        "ru": "❌ Этот рейс слишком далеко в прошлом.\nИсторические данные пока не поддерживаются.\n🚧 Функция в разработке.\n👇 Нажмите, чтобы запросить ранний доступ."
    },
    "new_search": {
        "en": "Please enter flight number and date. For example: 'SU100 today' or 'AFL123 05.07.2025'",
        "ru": "Пожалуйста, введите номер рейса и дату. Например: 'SU100 сегодня' или 'AFL123 05.07.2025'"
    }
}

# Button labels
BUTTON_LABELS = {
    "refresh": {
        "en": "🔄 Обновить",
        "ru": "🔄 Обновить"
    },
    "subscribe": {
        "en": "🔔 Подписаться",
        "ru": "🔔 Подписаться"
    },
    "unsubscribe": {
        "en": "🔕 Отписаться",
        "ru": "🔕 Отписаться"
    },
    "new_search": {
        "en": "🔍 Новый поиск",
        "ru": "🔍 Новый поиск"
    },
    "my_flights": {
        "en": "📋 Мои рейсы",
        "ru": "📋 Мои рейсы"
    },
    "yesterday": {
        "en": "Вчера",
        "ru": "Вчера"
    },
    "today": {
        "en": "Сегодня",
        "ru": "Сегодня"
    },
    "tomorrow": {
        "en": "Завтра",
        "ru": "Завтра"
    },
    "request_feature": {
        "en": "🔔 Notify me when ready",
        "ru": "🔔 Уведомить когда готово"
    }
}

# Callback data prefixes
CALLBACK_PREFIXES = {
    "refresh": "refresh:",
    "subscribe": "subscribe:",
    "unsubscribe": "unsubscribe:",
    "new_search": "new_search",
    "my_flights": "my_flights",
    "date_select": "date:",
    "feature_request": "feature:"
} 