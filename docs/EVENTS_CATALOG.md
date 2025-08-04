# 📊 Каталог событий для аналитики

## 🎯 Основные события по вашим требованиям

### 1. Активность пользователя
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `user_first_visit` | Первый вход пользователя | `username`, `is_first_time: true` |
| `user_return_visit` | Повторный вход пользователя | `username`, `is_first_time: false` |
| `user_session_start` | Начало сессии | `session_id`, `username` |
| `user_session_end` | Конец сессии | `session_duration`, `session_actions` |

### 2. Идентификация пользователя
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `user_identified` | Пользователь идентифицирован | `telegram_id`, `username`, `first_name`, `last_name` |
| `user_profile_updated` | Обновление профиля | `old_username`, `new_username` |

### 3. Команды бота
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `command_used` | Использование команды | `command` (`/start`, `/search`, `/reset`) |
| `command_success` | Успешное выполнение команды | `command`, `response_time` |
| `command_error` | Ошибка выполнения команды | `command`, `error_message` |

### 4. Клики по кнопкам
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `button_click` | Нажатие на кнопку | `button_name`, `button_type`, `button_context` |

**Примеры кнопок:**
- `refresh` - Обновить статус рейса
- `subscribe` - Подписаться на рейс
- `unsubscribe` - Отписаться от рейса
- `new_search` - Новый поиск
- `date_select` - Выбор даты
- `language_change` - Смена языка

### 5. Ошибки
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `error` | Общая ошибка | `error_type`, `error_message`, `context` |
| `api_error` | Ошибка API | `api_name`, `error_message`, `response_time` |
| `parse_error` | Ошибка парсинга | `input_text`, `expected_format` |
| `database_error` | Ошибка базы данных | `operation`, `error_message` |

### 6. API ответы
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `api_call` | Вызов API | `api_name`, `success`, `response_time` |
| `flight_api_response` | Ответ API рейсов | `flight_number`, `status`, `response_time` |
| `subscription_api_response` | Ответ API подписок | `action`, `flight_number`, `success` |

## 🔍 События поиска и работы с рейсами

### Поиск рейсов
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `flight_search` | Поиск рейса | `flight_number`, `date`, `success`, `response_time` |
| `flight_search_started` | Начало поиска | `flight_number`, `date` |
| `flight_search_completed` | Завершение поиска | `flight_number`, `date`, `found_results` |
| `flight_search_no_results` | Поиск без результатов | `flight_number`, `date` |

### Результаты поиска
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `flight_found` | Рейс найден | `flight_number`, `date`, `status`, `airline` |
| `flight_not_found` | Рейс не найден | `flight_number`, `date`, `reason` |
| `flight_status_changed` | Изменение статуса | `flight_number`, `old_status`, `new_status` |

## 🔔 События подписок и уведомлений

### Подписки
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `subscription` | Подписка/отписка | `action`, `flight_number`, `date` |
| `subscription_created` | Создание подписки | `flight_number`, `date`, `user_id` |
| `subscription_deleted` | Удаление подписки | `flight_number`, `date`, `user_id` |
| `subscription_limit_reached` | Достигнут лимит подписок | `user_id`, `current_count`, `limit` |

### Уведомления
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `notification_sent` | Отправлено уведомление | `notification_type`, `flight_number`, `user_id` |
| `notification_delivered` | Уведомление доставлено | `notification_id`, `user_id` |
| `notification_failed` | Ошибка отправки | `notification_id`, `error_message` |

## 📱 События взаимодействия

### Сообщения
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `message_received` | Получено сообщение | `message_type`, `message_length` |
| `text_message_received` | Текстовое сообщение | `text_length`, `contains_flight_number` |
| `photo_message_received` | Фото сообщение | `photo_size`, `has_caption` |

### Навигация
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `navigation_step` | Шаг навигации | `current_step`, `next_step`, `user_id` |
| `flow_completed` | Завершение потока | `flow_name`, `steps_completed`, `total_time` |
| `flow_abandoned` | Прерывание потока | `flow_name`, `abandoned_at_step` |

## 🌍 События локализации

### Язык
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `language_change` | Смена языка | `old_language`, `new_language` |
| `language_detected` | Автоопределение языка | `detected_language`, `confidence` |

### География
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `user_location` | Местоположение пользователя | `country`, `city`, `timezone` |
| `popular_routes` | Популярные маршруты | `from_airport`, `to_airport`, `search_count` |

## 📈 События производительности

### Время ответа
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `api_response_time` | Время ответа API | `api_name`, `response_time`, `success` |
| `bot_response_time` | Время ответа бота | `command`, `response_time` |
| `database_query_time` | Время запроса к БД | `query_type`, `response_time` |

### Нагрузка
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `high_load_detected` | Высокая нагрузка | `concurrent_users`, `response_time` |
| `rate_limit_hit` | Превышение лимита | `user_id`, `limit_type` |

## 🎯 События конверсии

### Целевые действия
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `conversion` | Конверсия | `conversion_type`, `conversion_value` |
| `subscription_conversion` | Конверсия подписки | `flight_number`, `user_id` |
| `search_conversion` | Конверсия поиска | `flight_number`, `found_results` |

### Вовлеченность
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `user_engagement` | Вовлеченность пользователя | `engagement_type`, `session_actions`, `session_duration` |
| `feature_used` | Использование функции | `feature_name`, `usage_count` |

## 🔧 События разработки

### Отладка
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `debug_event` | Отладочное событие | `debug_type`, `debug_data` |
| `test_event` | Тестовое событие | `test_type`, `test_data` |

### Мониторинг
| Событие | Описание | Параметры |
|---------|----------|-----------|
| `service_health` | Здоровье сервиса | `service_name`, `status`, `response_time` |
| `error_rate` | Частота ошибок | `error_type`, `error_count`, `time_period` |

## 📊 Метрики для отслеживания

### Ключевые показатели (KPI)
1. **DAU/WAU** - Ежедневные/еженедельные активные пользователи
2. **Retention Rate** - Коэффициент удержания
3. **Conversion Rate** - Коэффициент конверсии
4. **Average Session Duration** - Средняя продолжительность сессии
5. **Error Rate** - Частота ошибок

### Бизнес-метрики
1. **Количество поисков рейсов** - Общая активность
2. **Популярные рейсы** - Топ запрашиваемых маршрутов
3. **Конверсия подписок** - Эффективность функции подписок
4. **Время ответа** - Производительность системы

## 🎨 Примеры использования

### Отслеживание первого входа
```python
await analytics.track_user_session(
    user_id=message.from_user.id,
    username=message.from_user.username,
    is_first_time=True
)
```

### Отслеживание клика по кнопке
```python
await analytics.track_button_click(
    user_id=callback.from_user.id,
    button_name="subscribe",
    button_context={"flight_number": "SU100", "date": "2024-01-15"}
)
```

### Отслеживание ошибки
```python
await analytics.track_error(
    user_id=user_id,
    error_type="api_timeout",
    error_message="API timeout after 30 seconds",
    context={"api_name": "flight_api", "flight_number": "SU100"}
)
```

### Отслеживание конверсии
```python
await analytics.track_conversion(
    user_id=user_id,
    conversion_type="subscription",
    conversion_value=1.0,
    context={"flight_number": "SU100", "date": "2024-01-15"}
)
```

## 📋 Чек-лист внедрения

- [ ] Настроить отслеживание первого/повторного входа
- [ ] Добавить отслеживание всех кнопок
- [ ] Настроить мониторинг ошибок
- [ ] Добавить отслеживание API ответов
- [ ] Настроить отслеживание подписок
- [ ] Добавить метрики производительности
- [ ] Настроить дашборды в Amplitude
- [ ] Протестировать все события
- [ ] Настроить алерты для критических метрик 