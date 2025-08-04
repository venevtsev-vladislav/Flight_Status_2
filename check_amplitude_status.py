#!/usr/bin/env python3
"""
Быстрая проверка статуса подключения Amplitude
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_amplitude_status():
    """Проверка статуса подключения Amplitude"""
    
    print("🔍 Проверка статуса Amplitude")
    print("=" * 40)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем переменные окружения
    required_vars = {
        'AMPLITUDE_API_KEY': os.getenv('AMPLITUDE_API_KEY'),
        'AMPLITUDE_SECRET_KEY': os.getenv('AMPLITUDE_SECRET_KEY'),
        'AMPLITUDE_PROJECT_ID': os.getenv('AMPLITUDE_PROJECT_ID')
    }
    
    print("📋 Проверка переменных окружения:")
    
    all_good = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"   ✅ {var_name}: настроен")
        else:
            print(f"   ❌ {var_name}: НЕ настроен")
            all_good = False
    
    if not all_good:
        print("\n🚨 Проблемы с настройкой:")
        print("   1. Скопируйте env.example в .env")
        print("   2. Добавьте ваши ключи Amplitude")
        print("   3. Запустите этот скрипт снова")
        return False
    
    print("\n✅ Все переменные окружения настроены!")
    
    # Проверяем конфигурацию
    try:
        from bot.config import ANALYTICS
        
        print("\n📋 Проверка конфигурации:")
        
        if ANALYTICS.get('enabled'):
            print("   ✅ Аналитика включена")
        else:
            print("   ❌ Аналитика отключена")
            return False
        
        amplitude_config = ANALYTICS.get('amplitude', {})
        
        if amplitude_config.get('enabled'):
            print("   ✅ Amplitude включен")
        else:
            print("   ❌ Amplitude отключен")
            return False
        
        print(f"   📊 Batch size: {amplitude_config.get('batch_size', 'N/A')}")
        print(f"   ⏱️  Flush interval: {amplitude_config.get('flush_interval', 'N/A')} сек")
        
    except ImportError as e:
        print(f"   ❌ Ошибка импорта конфигурации: {e}")
        return False
    
    print("\n✅ Конфигурация корректна!")
    
    # Проверяем подключение к интернету
    print("\n🌐 Проверка подключения к интернету:")
    try:
        import httpx
        import asyncio
        
        async def test_connection():
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get("https://api2.amplitude.com")
                    if response.status_code == 200:
                        print("   ✅ Подключение к Amplitude API доступно")
                        return True
                    else:
                        print(f"   ⚠️  Amplitude API ответил с кодом: {response.status_code}")
                        return False
            except Exception as e:
                print(f"   ❌ Ошибка подключения к Amplitude: {e}")
                return False
        
        # Запускаем тест подключения
        result = asyncio.run(test_connection())
        
        if not result:
            print("\n🚨 Проблемы с подключением:")
            print("   1. Проверьте интернет-соединение")
            print("   2. Убедитесь, что API ключи корректны")
            return False
            
    except ImportError:
        print("   ⚠️  httpx не установлен, пропускаем тест подключения")
    
    print("\n🎉 Все проверки пройдены!")
    print("\n📋 Следующие шаги:")
    print("   1. Запустите: python test_amplitude.py")
    print("   2. Проверьте события в Amplitude")
    print("   3. Запустите бота: python run.py")
    
    return True

def main():
    """Главная функция"""
    success = check_amplitude_status()
    
    if success:
        print("\n✅ Amplitude готов к использованию!")
    else:
        print("\n❌ Требуется настройка Amplitude")
        print("См. AMPLITUDE_SETUP_GUIDE.md для подробной инструкции")

if __name__ == "__main__":
    main() 