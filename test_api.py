#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы API функций
"""

import requests
import json
import os
from datetime import datetime

# Конфигурация
SUPABASE_URL = "https://taanbgxivbqcuaxcspjx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRhYW5iZ3hpdmJxY3VheGNzcGp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTExNDE0NzksImV4cCI6MjA2NjcxNzQ3OX0.YS7y157uAw3pMA8_KTMM-WB0IFQwG-uiKVu-c17CqIA"

def test_parse_flight():
    """Тест функции парсинга рейса"""
    print("=== Тест парсинга рейса ===")
    
    url = f"{SUPABASE_URL}/functions/v1/parse-flight"
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json'
    }
    
    test_cases = [
        "IB392 08.07.2025",
        "LA5629 08.07.2025", 
        "SU123 15.12.2024",
        "AA1234 tomorrow",
        "BA567 today"
    ]
    
    for text in test_cases:
        payload = {
            'text': text,
            'user_id': 'test-user'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"Input: '{text}'")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print("-" * 50)
        except Exception as e:
            print(f"Error testing '{text}': {e}")

def test_flight_api():
    """Тест функции получения данных о рейсе"""
    print("\n=== Тест API рейса ===")
    
    url = f"{SUPABASE_URL}/functions/v1/flight-api"
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json'
    }
    
    test_cases = [
        {"flight_number": "IB392", "date": "2025-07-08"},
        {"flight_number": "LA5629", "date": "2025-07-08"},
        {"flight_number": "SU123", "date": "2024-12-15"}
    ]
    
    for test_case in test_cases:
        payload = {
            'flight_number': test_case['flight_number'],
            'date': test_case['date'],
            'user_id': 'test-user'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"Flight: {test_case['flight_number']} on {test_case['date']}")
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Success: {result.get('success', False)}")
            print(f"Message: {result.get('message', 'No message')}")
            if 'data' in result and result['data']:
                if isinstance(result['data'], dict) and 'error' in result['data']:
                    print(f"Error: {result['data']['error']} - {result['data']['message']}")
                else:
                    print(f"Data received: {type(result['data'])}")
            print("-" * 50)
        except Exception as e:
            print(f"Error testing {test_case}: {e}")

def check_rate_limits():
    """Проверка лимитов API"""
    print("\n=== Проверка лимитов API ===")
    
    # Проверяем текущее время
    now = datetime.now()
    print(f"Current time: {now}")
    
    # Проверяем переменные окружения (если доступны)
    api_key = os.getenv('AERODATABOX_API_KEY')
    if api_key:
        print(f"API Key configured: {'Yes' if api_key else 'No'}")
        print(f"API Key length: {len(api_key) if api_key else 0}")
    else:
        print("API Key not found in environment variables")

if __name__ == "__main__":
    check_rate_limits()
    test_parse_flight()
    test_flight_api() 