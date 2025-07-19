from typing import Optional
from bot.config import LANGUAGE_DETECTION_ENABLED, FALLBACK_LANGUAGE, LANGUAGE_MAPPING, SUPPORTED_LANGUAGES

class LanguageService:
    """Service for language detection and management"""
    
    def __init__(self):
        self.language_mapping = LANGUAGE_MAPPING
        self.supported_languages = SUPPORTED_LANGUAGES
        self.fallback_language = FALLBACK_LANGUAGE
    
    def detect_language(self, user_language_code: Optional[str] = None, 
                       user_text: Optional[str] = None) -> str:
        """
        Detect user language based on Telegram language code and/or text content
        
        Args:
            user_language_code: Telegram language code (e.g., 'ru', 'en', 'de')
            user_text: User's message text for content-based detection
            
        Returns:
            Supported language code ('en' or 'ru')
        """
        if not LANGUAGE_DETECTION_ENABLED:
            return self.fallback_language
        
        # First, try to detect from Telegram language code
        if user_language_code:
            detected_lang = self._detect_from_telegram_code(user_language_code)
            if detected_lang:
                return detected_lang
        
        # If no Telegram code or detection failed, try content-based detection
        if user_text:
            detected_lang = self._detect_from_text(user_text)
            if detected_lang:
                return detected_lang
        
        # Fallback to default language
        return self.fallback_language
    
    def _detect_from_telegram_code(self, language_code: str) -> Optional[str]:
        """Detect language from Telegram language code"""
        if not language_code:
            return None
        
        # Normalize language code (take first part if contains dash)
        lang_code = language_code.split('-')[0].lower()
        
        # Check direct mapping
        if lang_code in self.language_mapping:
            return self.language_mapping[lang_code]
        
        # Check if it's a supported language
        if lang_code in self.supported_languages:
            return lang_code
        
        return None
    
    def _detect_from_text(self, text: str) -> Optional[str]:
        """Detect language from text content using simple heuristics"""
        if not text:
            return None
        
        # Convert to lowercase for analysis
        text_lower = text.lower()
        
        # Russian character detection
        russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        text_chars = set(text_lower)
        
        # Count Russian characters
        russian_char_count = len(text_chars.intersection(russian_chars))
        total_chars = len([c for c in text_lower if c.isalpha()])
        
        # If more than 30% of characters are Russian, assume Russian
        if total_chars > 0 and (russian_char_count / total_chars) > 0.3:
            return 'ru'
        
        # Check for common Russian words
        russian_words = {
            'сегодня', 'завтра', 'вчера', 'рейс', 'аэропорт', 'время', 'вылет', 'прилет',
            'номер', 'дата', 'помощь', 'найти', 'поиск', 'статус', 'информация'
        }
        
        text_words = set(text_lower.split())
        russian_word_count = len(text_words.intersection(russian_words))
        
        if russian_word_count > 0:
            return 'ru'
        
        # Default to English for Latin-based languages
        return 'en'
    
    def is_supported_language(self, language_code: str) -> bool:
        """Check if language is supported"""
        return language_code in self.supported_languages
    
    def get_language_name(self, language_code: str) -> str:
        """Get human-readable language name"""
        language_names = {
            'en': 'English',
            'ru': 'Русский'
        }
        return language_names.get(language_code, language_code)
    
    def get_available_languages(self) -> list:
        """Get list of available languages with names"""
        return [
            {'code': lang, 'name': self.get_language_name(lang)}
            for lang in self.supported_languages
        ] 