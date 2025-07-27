#!/usr/bin/env python3
"""
Сервис для форматирования уведомлений о рейсах
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис для создания уведомлений о рейсах"""
    
    def __init__(self):
        # Статусы рейсов с эмодзи
        self.status_emoji = {
            "Unknown": "❓",
            "Expected": "⏳",
            "EnRoute": "✈️",
            "CheckIn": "📋",
            "Boarding": "🛂",
            "GateClosed": "🔒",
            "Departed": "✈️",
            "Delayed": "⏰",
            "Approaching": "🛬",
            "Arrived": "✅",
            "Canceled": "❌",
            "Diverted": "🔄",
            "CanceledUncertain": "❓"
        }
    
    def format_flight_notification(self, flight_data: Dict[str, Any]) -> str:
        """Форматирует уведомление о рейсе в коротком формате"""
        
        flight_number = flight_data.get("number", "").replace(" ", "")
        status = flight_data.get("status", "Unknown")
        emoji = self.status_emoji.get(status, "❓")
        
        # Базовое сообщение
        message = f"{flight_number}: "
        
        # Форматируем в зависимости от статуса
        if status == "Boarding":
            gate = flight_data.get("departure", {}).get("gate")
            if gate:
                message += f"Идет посадка, выход {gate} {emoji}"
            else:
                message += f"Идет посадка {emoji}"
                
        elif status == "Departed":
            actual_time = flight_data.get("departure", {}).get("actualTime", {}).get("local")
            if actual_time:
                # Извлекаем только время (HH:MM)
                time_str = actual_time.split("T")[1][:5] if "T" in actual_time else actual_time[:5]
                message += f"Отправлен в {time_str} {emoji}"
                
                # Добавляем время прибытия на новой строке
                arrival_time = flight_data.get("arrival", {}).get("scheduledTime", {}).get("local")
                if arrival_time:
                    arrival_str = arrival_time.split("T")[1][:5] if "T" in arrival_time else arrival_time[:5]
                    message += f"\nПримерное время прибытия {arrival_str}"
                    
        elif status == "Arrived":
            actual_time = flight_data.get("arrival", {}).get("actualTime", {}).get("local")
            if actual_time:
                time_str = actual_time.split("T")[1][:5] if "T" in actual_time else actual_time[:5]
                message += f"Прибыл в {time_str} {emoji}"
            else:
                message += f"Прибыл {emoji}"
                
        elif status == "Delayed":
            # Пытаемся найти информацию о задержке
            notification_summary = flight_data.get("notificationSummary", "")
            if "delay" in notification_summary.lower() or "задержка" in notification_summary.lower():
                message += f"Задержка {emoji}"
            else:
                message += f"Задержка {emoji}"
                
        elif status == "Canceled":
            message += f"Отменен {emoji}"
            
        elif status == "EnRoute":
            message += f"В пути {emoji}"
            
        elif status == "CheckIn":
            message += f"Регистрация открыта {emoji}"
            
        elif status == "GateClosed":
            message += f"Выход закрыт {emoji}"
            
        elif status == "Approaching":
            message += f"Заходит на посадку {emoji}"
            
        else:
            # Для неизвестных статусов используем notificationSummary
            notification_summary = flight_data.get("notificationSummary", "")
            if notification_summary:
                message += f"{notification_summary} {emoji}"
            else:
                message += f"Статус: {status} {emoji}"
        
        return message
    
    def format_notification_with_details(self, flight_data: Dict[str, Any]) -> str:
        """Форматирует уведомление с дополнительными деталями"""
        
        base_message = self.format_flight_notification(flight_data)
        
        # Добавляем детали если есть
        details = []
        
        # Информация о задержке
        if flight_data.get("status") == "Delayed":
            departure = flight_data.get("departure", {})
            scheduled = departure.get("scheduledTime", {}).get("local")
            actual = departure.get("actualTime", {}).get("local")
            
            if scheduled and actual:
                # Вычисляем задержку
                try:
                    scheduled_time = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                    actual_time = datetime.fromisoformat(actual.replace("Z", "+00:00"))
                    delay_minutes = int((actual_time - scheduled_time).total_seconds() / 60)
                    
                    if delay_minutes > 0:
                        details.append(f"Задержка {delay_minutes} минут")
                except:
                    pass
        
        # Информация о гейте
        gate = flight_data.get("departure", {}).get("gate")
        if gate and flight_data.get("status") in ["Boarding", "Departed"]:
            details.append(f"Выход {gate}")
        
        # Информация о терминале
        terminal = flight_data.get("departure", {}).get("terminal")
        if terminal:
            details.append(f"Терминал {terminal}")
        
        # Добавляем детали к сообщению
        if details:
            base_message += f"\n{', '.join(details)}"
        
        return base_message

# Пример использования
if __name__ == "__main__":
    service = NotificationService()
    
    # Тестовые данные
    test_flight = {
        "number": "QR 818",
        "status": "Boarding",
        "departure": {
            "gate": "D7",
            "terminal": "T1"
        },
        "arrival": {
            "scheduledTime": {"local": "2025-07-20T14:43+03:00"}
        }
    }
    
    print(service.format_flight_notification(test_flight)) 