#!/usr/bin/env python3
"""
Тестовый скрипт для проверки вебсокетов и уведомлений
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пример данных уведомления от AeroDataBox API
SAMPLE_NOTIFICATION_DATA = {
    "subscription": {
        "id": "12345678-1234-1234-1234-123456789012",
        "isActive": True,
        "createdOnUtc": "2025-07-20T10:00:00Z",
        "subject": {
            "type": "FlightByNumber",
            "id": "QR1197"
        },
        "subscriber": {
            "type": "Webhook",
            "id": "https://your-webhook-url.com/flight-updates"
        }
    },
    "flights": [
        {
            "number": "QR 1197",
            "status": "EnRoute",
            "lastUpdatedUtc": "2025-07-20T10:30:00Z",
            "notificationSummary": "Flight QR1197 is now en route",
            "notificationRemark": "Flight departed on time",
            "departure": {
                "airport": {
                    "icao": "OEGS",
                    "iata": "ELQ",
                    "name": "Gassim Regional Airport"
                },
                "scheduledTime": {
                    "utc": "2025-07-20T08:10Z",
                    "local": "2025-07-20T11:10+03:00"
                },
                "actualTime": {
                    "utc": "2025-07-20T08:15Z",
                    "local": "2025-07-20T11:15+03:00"
                },
                "terminal": "T1",
                "gate": "A5"
            },
            "arrival": {
                "airport": {
                    "icao": "OTHH",
                    "iata": "DOH",
                    "name": "Doha Hamad International Airport"
                },
                "scheduledTime": {
                    "utc": "2025-07-20T09:55Z",
                    "local": "2025-07-20T12:55+03:00"
                },
                "actualTime": None,
                "terminal": None,
                "gate": None
            },
            "aircraft": {
                "model": "Airbus A320",
                "registration": "A7-ABC"
            },
            "airline": {
                "name": "Qatar Airways",
                "iata": "QR",
                "icao": "QTR"
            },
            "location": {
                "lat": 27.5,
                "lon": 48.2,
                "altitude": 35000,
                "speed": 850,
                "track": 45
            }
        }
    ]
}

def format_notification_message(notification_data: Dict[str, Any]) -> str:
    """Форматирует уведомление для отправки в Telegram"""
    
    flight = notification_data["flights"][0]
    subscription = notification_data["subscription"]
    
    # Статусы рейсов
    status_emoji = {
        "Unknown": "❓",
        "Expected": "⏳",
        "EnRoute": "✈️",
        "CheckIn": "📋",
        "Boarding": "🚪",
        "GateClosed": "🔒",
        "Departed": "🛫",
        "Delayed": "⏰",
        "Approaching": "🛬",
        "Arrived": "✅",
        "Canceled": "❌",
        "Diverted": "🔄",
        "CanceledUncertain": "❓"
    }
    
    status = flight["status"]
    status_icon = status_emoji.get(status, "❓")
    
    # Форматируем сообщение
    message = f"🔔 **Flight Update: {flight['number']}**\n\n"
    message += f"{status_icon} **Status:** {status}\n"
    
    if flight.get("notificationSummary"):
        message += f"📝 **Update:** {flight['notificationSummary']}\n"
    
    if flight.get("notificationRemark"):
        message += f"💬 **Note:** {flight['notificationRemark']}\n"
    
    # Информация о вылете
    dep = flight["departure"]
    message += f"\n🛫 **Departure:** {dep['airport']['iata']} ({dep['airport']['name']})\n"
    message += f"📅 **Scheduled:** {dep['scheduledTime']['local']}\n"
    
    if dep.get("actualTime"):
        message += f"✅ **Actual:** {dep['actualTime']['local']}\n"
    
    if dep.get("gate"):
        message += f"🚪 **Gate:** {dep['gate']}\n"
    
    # Информация о прилете
    arr = flight["arrival"]
    message += f"\n🛬 **Arrival:** {arr['airport']['iata']} ({arr['airport']['name']})\n"
    message += f"📅 **Scheduled:** {arr['scheduledTime']['local']}\n"
    
    if arr.get("actualTime"):
        message += f"✅ **Actual:** {arr['actualTime']['local']}\n"
    
    # Информация о самолете
    if flight.get("aircraft"):
        message += f"\n✈️ **Aircraft:** {flight['aircraft']['model']}\n"
        if flight['aircraft'].get("registration"):
            message += f"🆔 **Registration:** {flight['aircraft']['registration']}\n"
    
    # Информация об авиакомпании
    if flight.get("airline"):
        message += f"🏢 **Airline:** {flight['airline']['name']}\n"
    
    # Местоположение (если доступно)
    if flight.get("location"):
        loc = flight["location"]
        message += f"\n📍 **Location:** {loc['lat']:.2f}, {loc['lon']:.2f}\n"
        message += f"📊 **Altitude:** {loc['altitude']:,} ft\n"
        message += f"⚡ **Speed:** {loc['speed']} km/h\n"
    
    message += f"\n🕐 **Last Updated:** {flight['lastUpdatedUtc']}"
    
    return message

def test_notification_formatting():
    """Тестирует форматирование уведомлений"""
    logger.info("🧪 Testing notification formatting...")
    
    formatted_message = format_notification_message(SAMPLE_NOTIFICATION_DATA)
    
    print("\n" + "="*50)
    print("📱 SAMPLE TELEGRAM NOTIFICATION")
    print("="*50)
    print(formatted_message)
    print("="*50)
    
    return formatted_message

def test_different_statuses():
    """Тестирует разные статусы рейсов"""
    logger.info("🧪 Testing different flight statuses...")
    
    statuses = [
        "Expected", "EnRoute", "CheckIn", "Boarding", 
        "Departed", "Delayed", "Approaching", "Arrived", "Canceled"
    ]
    
    for status in statuses:
        test_data = SAMPLE_NOTIFICATION_DATA.copy()
        test_data["flights"][0]["status"] = status
        test_data["flights"][0]["notificationSummary"] = f"Flight status changed to {status}"
        
        formatted = format_notification_message(test_data)
        print(f"\n--- Status: {status} ---")
        print(formatted[:200] + "..." if len(formatted) > 200 else formatted)

def test_websocket_data_structure():
    """Показывает структуру данных вебсокета"""
    logger.info("🧪 Testing websocket data structure...")
    
    print("\n" + "="*50)
    print("🔌 WEBSOCKET DATA STRUCTURE")
    print("="*50)
    print(json.dumps(SAMPLE_NOTIFICATION_DATA, indent=2))
    print("="*50)

async def simulate_websocket_receiver():
    """Симулирует получение данных по вебсокету"""
    logger.info("🧪 Simulating websocket receiver...")
    
    # Симуляция получения уведомления
    print("\n🔄 Simulating websocket notification...")
    
    # Обработка уведомления
    formatted_message = format_notification_message(SAMPLE_NOTIFICATION_DATA)
    
    # Здесь будет код для отправки в Telegram
    print("📤 Would send to Telegram:")
    print(formatted_message)
    
    return formatted_message

def main():
    """Основная функция тестирования"""
    logger.info("🚀 Starting websocket notification tests...")
    
    # Тест 1: Форматирование уведомлений
    test_notification_formatting()
    
    # Тест 2: Разные статусы
    test_different_statuses()
    
    # Тест 3: Структура данных
    test_websocket_data_structure()
    
    # Тест 4: Симуляция вебсокета
    asyncio.run(simulate_websocket_receiver())
    
    logger.info("✅ All tests completed!")

if __name__ == "__main__":
    main() 