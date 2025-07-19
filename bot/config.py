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

# Language detection settings
LANGUAGE_DETECTION_ENABLED = True
FALLBACK_LANGUAGE = "en"
LANGUAGE_MAPPING = {
    "ru": "ru",
    "uk": "ru",  # Ukrainian -> Russian
    "be": "ru",  # Belarusian -> Russian
    "kk": "ru",  # Kazakh -> Russian
    "en": "en",
    "de": "en",  # German -> English
    "fr": "en",  # French -> English
    "es": "en",  # Spanish -> English
    "it": "en",  # Italian -> English
    "pt": "en",  # Portuguese -> English
}

# Typing indicator settings
TYPING_INDICATOR_ENABLED = True
TYPING_DURATION = 3  # seconds
TYPING_ACTION = "typing"  # or "upload_photo", "record_video", "upload_video", "record_voice", "upload_voice", "upload_document", "choose_sticker", "find_location"

# API request settings
API_REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# AeroDataBox API settings (RapidAPI)
AERODATABOX_API_KEY = os.getenv('AERODATABOX_API_KEY')
AERODATABOX_API_HOST = 'aerodatabox.p.rapidapi.com'
AERODATABOX_API_URL = 'https://aerodatabox.p.rapidapi.com'

# Flight API settings
FLIGHT_API_TIMEOUT = 30  # seconds

# Message templates
MESSAGE_TEMPLATES = {
    "welcome": {
        "en": "👋 Hello, {username}!\nI can help you track flight status.\nJust type the flight number and date, for example:\n✈️ SU100 {today}\nOr choose a date below:",
        "ru": "👋 Привет, {username}!\nЯ помогу отследить статус рейса.\nПросто напиши номер рейса и дату, например:\n✈️ SU100 {today}\nИли выбери дату ниже:"
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
    },
    "search_started": {
        "en": "🔍 Starting search for flight {flight_number} on {date}...",
        "ru": "🔍 Начинаю поиск рейса {flight_number} на {date}..."
    },
    "search_in_progress": {
        "en": "⏳ Searching for flight data...",
        "ru": "⏳ Ищу данные о рейсе..."
    },
    "api_error": {
        "en": "🚦 Increased demand, I need a little more time to process",
        "ru": "🚦 Повышенный спрос, мне нужно немного больше времени для обработки"
    },
    "no_data_found": {
        "en": "📋 Flight data is currently unavailable",
        "ru": "📋 Данные по рейсу в настоящее время недоступны"
    },
    "technical_error": {
        "en": "🔧 Technical issue, our specialists are already solving",
        "ru": "🔧 Техническая проблема, наши специалисты уже решают"
    },
    "loading": {
        "en": "⏳ Please wait, processing your request...",
        "ru": "⏳ Пожалуйста, подождите, обрабатываю ваш запрос..."
    }
}

# Button labels
BUTTON_LABELS = {
    "refresh": {
        "en": "🔄 Refresh",
        "ru": "🔄 Обновить"
    },
    "subscribe": {
        "en": "🔔 Subscribe",
        "ru": "🔔 Подписаться"
    },
    "unsubscribe": {
        "en": "🔕 Unsubscribe",
        "ru": "🔕 Отписаться"
    },
    "new_search": {
        "en": "🔍 New search",
        "ru": "🔍 Новый поиск"
    },
    "my_flights": {
        "en": "📋 My flights",
        "ru": "📋 Мои рейсы"
    },
    "yesterday": {
        "en": "Yesterday",
        "ru": "Вчера"
    },
    "today": {
        "en": "Today",
        "ru": "Сегодня"
    },
    "tomorrow": {
        "en": "Tomorrow",
        "ru": "Завтра"
    },
    "request_feature": {
        "en": "🔔 Notify me when ready",
        "ru": "🔔 Уведомить когда готово"
    },
    "try_again": {
        "en": "🔄 Try again",
        "ru": "🔄 Попробовать снова"
    },
    "help": {
        "en": "❓ Help",
        "ru": "❓ Помощь"
    },
    "settings": {
        "en": "⚙️ Settings",
        "ru": "⚙️ Настройки"
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
    "feature_request": "feature:",
    "help": "help",
    "settings": "settings",
    "language": "lang:"
}

# Error handling settings
ERROR_HANDLING = {
    "max_retries": 3,
    "retry_delay": 2,
    "show_technical_details": False,  # Set to True for debugging
    "log_errors": True
}

# Performance settings
PERFORMANCE = {
    "cache_enabled": True,
    "cache_ttl": 300,  # 5 minutes
    "rate_limit_enabled": True,
    "rate_limit_per_user": 10,  # requests per minute
    "rate_limit_per_global": 100  # requests per minute
}

# Notification settings
NOTIFICATIONS = {
    "enabled": True,
    "subscription_limit": 10,  # max flights per user
    "check_interval": 300,  # 5 minutes
    "batch_size": 50  # notifications per batch
}

# Analytics settings
ANALYTICS = {
    "enabled": True,
    "track_user_actions": True,
    "track_api_calls": True,
    "track_errors": True,
    "amplitude": {
        "enabled": True,
        "api_key": os.getenv('AMPLITUDE_API_KEY'),
        "secret_key": os.getenv('AMPLITUDE_SECRET_KEY'),
        "project_id": os.getenv('AMPLITUDE_PROJECT_ID'),
        "batch_size": 100,
        "flush_interval": 10,  # seconds
        "max_retries": 3,
        "timeout": 30
    }
} 