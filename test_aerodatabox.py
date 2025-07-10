#!/usr/bin/env python3
"""
Тестовый скрипт для проверки AeroDataBox API
"""

import requests
import json
import os
from datetime import datetime

def test_aerodatabox_api():
    """Тест AeroDataBox API напрямую"""
    print("=== Тест AeroDataBox API ===")
    
    # API конфигурация
    api_host = 'aerodatabox.p.rapidapi.com'
    api_key = os.getenv('AERODATABOX_API_KEY')
    
    if not api_key:
        print("❌ AERODATABOX_API_KEY не найден в переменных окружения")
        return
    
    print(f"✅ API Key найден (длина: {len(api_key)})")
    
    # Тестовые данные
    test_cases = [
        {"flight_number": "DL47", "date": "2022-10-20"},
        {"flight_number": "IB392", "date": "2025-07-08"},
        {"flight_number": "LA5629", "date": "2025-07-08"}
    ]
    
    headers = {
        'x-rapidapi-host': api_host,
        'x-rapidapi-key': api_key
    }
    
    for test_case in test_cases:
        flight_number = test_case['flight_number']
        date = test_case['date']
        
        url = f'https://{api_host}/flights/number/{flight_number}/{date}?withAircraftImage=false&withLocation=false&dateLocalRole=Both'
        
        print(f"\n🔍 Тестируем: {flight_number} на {date}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Успех! Получено данных: {len(data) if isinstance(data, list) else 1}")
                
                if isinstance(data, list) and len(data) > 0:
                    flight = data[0]
                    print(f"Flight number: {flight.get('number', 'N/A')}")
                    print(f"Status: {flight.get('status', 'N/A')}")
                    print(f"Departure: {flight.get('departure', {}).get('airport', {}).get('iata', 'N/A')}")
                    print(f"Arrival: {flight.get('arrival', {}).get('airport', {}).get('iata', 'N/A')}")
                elif isinstance(data, dict):
                    print(f"Flight number: {data.get('number', 'N/A')}")
                    print(f"Status: {data.get('status', 'N/A')}")
                
            elif response.status_code == 429:
                print("❌ Rate limit exceeded (429)")
                retry_after = response.headers.get('Retry-After', 'Unknown')
                print(f"Retry-After: {retry_after}")
                
            elif response.status_code == 401:
                print("❌ Unauthorized (401) - неверный API ключ")
                
            elif response.status_code == 403:
                print("❌ Forbidden (403) - API ключ не авторизован")
                
            else:
                print(f"❌ Ошибка: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error text: {response.text}")
                    
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        print("-" * 50)

def check_api_key():
    """Проверка API ключа"""
    print("=== Проверка API ключа ===")
    
    api_key = os.getenv('AERODATABOX_API_KEY')
    
    if api_key:
        print(f"✅ API ключ найден")
        print(f"Длина: {len(api_key)}")
        print(f"Префикс: {api_key[:10]}...")
        print(f"Суффикс: ...{api_key[-10:]}")
    else:
        print("❌ API ключ не найден")
        print("Установите переменную окружения AERODATABOX_API_KEY")

if __name__ == "__main__":
    check_api_key()
    test_aerodatabox_api() 