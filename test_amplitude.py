#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции Amplitude
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.services.analytics_service import AnalyticsService
from bot.config import ANALYTICS

async def test_amplitude_integration():
    """Тестирование интеграции с Amplitude"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    print("🔍 Тестирование интеграции Amplitude...")
    
    # Проверяем конфигурацию
    print(f"📋 Конфигурация аналитики:")
    print(f"   - Включена: {ANALYTICS.get('enabled', False)}")
    print(f"   - API Key: {'✅' if os.getenv('AMPLITUDE_API_KEY') else '❌'}")
    print(f"   - Secret Key: {'✅' if os.getenv('AMPLITUDE_SECRET_KEY') else '❌'}")
    print(f"   - Project ID: {'✅' if os.getenv('AMPLITUDE_PROJECT_ID') else '❌'}")
    
    # Создаем сервис аналитики
    analytics = AnalyticsService()
    
    if not analytics.enabled:
        print("❌ Аналитика отключена. Проверьте настройки.")
        return
    
    print("✅ Сервис аналитики инициализирован")
    
    # Тестируем различные события
    test_user_id = 123456789
    
    print("\n📊 Отправка тестовых событий...")
    
    # Тест 1: Пользовательское действие
    print("   - Тест пользовательского действия...")
    await analytics.track_user_action(
        user_id=test_user_id,
        action="test_action",
        context={"test": True, "message": "Тестовое событие"}
    )
    
    # Тест 2: API вызов
    print("   - Тест API вызова...")
    await analytics.track_api_call(
        user_id=test_user_id,
        api_name="test_api",
        success=True,
        response_time=1.5
    )
    
    # Тест 3: Ошибка
    print("   - Тест ошибки...")
    await analytics.track_error(
        user_id=test_user_id,
        error_type="test_error",
        error_message="Тестовая ошибка",
        context={"test": True}
    )
    
    # Тест 4: Поиск рейса
    print("   - Тест поиска рейса...")
    await analytics.track_flight_search(
        user_id=test_user_id,
        flight_number="SU100",
        date="2024-01-15",
        success=True,
        response_time=2.1
    )
    
    # Тест 5: Подписка
    print("   - Тест подписки...")
    await analytics.track_subscription(
        user_id=test_user_id,
        action="subscribe",
        flight_number="SU100",
        date="2024-01-15"
    )
    
    # Тест 6: Первый/повторный вход
    print("   - Тест первого входа...")
    await analytics.track_user_session(
        user_id=test_user_id,
        username="test_user",
        is_first_time=True
    )
    
    print("   - Тест повторного входа...")
    await analytics.track_user_session(
        user_id=test_user_id,
        username="test_user",
        is_first_time=False,
        session_duration=300.5
    )
    
    # Тест 7: Клик по кнопке
    print("   - Тест клика по кнопке...")
    await analytics.track_button_click(
        user_id=test_user_id,
        button_name="subscribe",
        button_context={"flight_number": "SU100", "date": "2024-01-15"}
    )
    
    # Тест 8: Использование команды
    print("   - Тест использования команды...")
    await analytics.track_command_usage(
        user_id=test_user_id,
        command="/start",
        context={"username": "test_user"}
    )
    
    # Тест 9: Получение сообщения
    print("   - Тест получения сообщения...")
    await analytics.track_message_received(
        user_id=test_user_id,
        message_type="text",
        message_length=50,
        context={"contains_flight_number": True}
    )
    
    # Тест 10: Отправка уведомления
    print("   - Тест отправки уведомления...")
    await analytics.track_notification_sent(
        user_id=test_user_id,
        notification_type="flight_update",
        flight_number="SU100",
        context={"status": "delayed"}
    )
    
    # Тест 11: Вовлеченность пользователя
    print("   - Тест вовлеченности...")
    await analytics.track_user_engagement(
        user_id=test_user_id,
        engagement_type="high",
        session_actions=15,
        session_duration=600.0,
        context={"features_used": ["search", "subscribe"]}
    )
    
    # Тест 12: Использование функции
    print("   - Тест использования функции...")
    await analytics.track_feature_usage(
        user_id=test_user_id,
        feature_name="flight_search",
        feature_context={"search_count": 5}
    )
    
    # Тест 13: Конверсия
    print("   - Тест конверсии...")
    await analytics.track_conversion(
        user_id=test_user_id,
        conversion_type="subscription",
        conversion_value=1.0,
        context={"flight_number": "SU100", "date": "2024-01-15"}
    )
    
    # Принудительная отправка событий
    print("\n📤 Отправка событий в Amplitude...")
    await analytics.flush()
    
    print("✅ Тестирование завершено!")
    print("\n📋 Что проверить в Amplitude:")
    print("   1. Зайдите в проект Amplitude")
    print("   2. Перейдите в раздел 'Events'")
    print("   3. Найдите события:")
    print("      - user_action_test_action")
    print("      - api_call")
    print("      - error")
    print("      - flight_search")
    print("      - subscription")
    print("      - user_first_visit")
    print("      - user_return_visit")
    print("      - button_click")
    print("      - command_used")
    print("      - message_received")
    print("      - notification_sent")
    print("      - user_engagement")
    print("      - feature_used")
    print("      - conversion")
    
    # Закрываем сервис
    await analytics.shutdown()

async def test_amplitude_config():
    """Тестирование конфигурации Amplitude"""
    
    print("\n🔧 Тестирование конфигурации...")
    
    # Проверяем переменные окружения
    required_vars = [
        'AMPLITUDE_API_KEY',
        'AMPLITUDE_SECRET_KEY', 
        'AMPLITUDE_PROJECT_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("Добавьте их в файл .env:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
    else:
        print("✅ Все переменные окружения настроены")
    
    # Проверяем конфигурацию
    if not ANALYTICS.get('enabled'):
        print("❌ Аналитика отключена в конфигурации")
    else:
        print("✅ Аналитика включена в конфигурации")

def main():
    """Главная функция"""
    print("🚀 Тестирование интеграции Amplitude")
    print("=" * 50)
    
    # Тестируем конфигурацию
    asyncio.run(test_amplitude_config())
    
    # Тестируем интеграцию
    asyncio.run(test_amplitude_integration())

if __name__ == "__main__":
    main() 