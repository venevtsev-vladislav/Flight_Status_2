# 📊 Краткий обзор всех событий

## 🎯 Основные события по вашим требованиям

### ✅ 1. Активность пользователя
- `user_first_visit` - Первый вход пользователя
- `user_return_visit` - Повторный вход пользователя
- `user_session_start` - Начало сессии
- `user_session_end` - Конец сессии

### ✅ 2. Идентификация пользователя
- `user_identified` - Пользователь идентифицирован (ID + username)
- `user_profile_updated` - Обновление профиля

### ✅ 3. Команды бота
- `command_used` - Использование команды (/start, /search, /reset)
- `command_success` - Успешное выполнение команды
- `command_error` - Ошибка выполнения команды

### ✅ 4. Клики по кнопкам
- `button_click` - **ВСЕ** клики по кнопкам с контекстом

### ✅ 5. Ошибки
- `error` - **ВСЕ** ошибки с деталями
- `api_error` - Ошибки API
- `parse_error` - Ошибки парсинга
- `database_error` - Ошибки базы данных

### ✅ 6. API ответы
- `api_call` - **ВСЕ** вызовы API с метриками
- `flight_api_response` - Ответы API рейсов
- `subscription_api_response` - Ответы API подписок

### ✅ 7. Подписки (если активированы)
- `subscription` - Подписка/отписка
- `subscription_created` - Создание подписки
- `subscription_deleted` - Удаление подписки
- `notification_sent` - Отправка уведомлений

## 🔍 Дополнительные важные события

### Поиск рейсов
- `flight_search` - Поиск рейса
- `flight_search_started` - Начало поиска
- `flight_search_completed` - Завершение поиска
- `flight_found` - Рейс найден
- `flight_not_found` - Рейс не найден

### Взаимодействие
- `message_received` - Получение сообщений
- `text_message_received` - Текстовые сообщения
- `navigation_step` - Шаги навигации
- `flow_completed` - Завершение потока

### Производительность
- `api_response_time` - Время ответа API
- `bot_response_time` - Время ответа бота
- `high_load_detected` - Высокая нагрузка

### Конверсия и вовлеченность
- `conversion` - Целевые действия
- `user_engagement` - Вовлеченность пользователя
- `feature_used` - Использование функций

## 📊 Ключевые метрики для отслеживания

### Активность
1. **DAU/WAU** - Ежедневные/еженедельные активные пользователи
2. **Retention Rate** - Коэффициент удержания
3. **Session Duration** - Продолжительность сессии

### Производительность
1. **Response Time** - Время ответа API
2. **Error Rate** - Частота ошибок
3. **Success Rate** - Успешность запросов

### Бизнес-метрики
1. **Search Volume** - Количество поисков
2. **Popular Flights** - Популярные рейсы
3. **Subscription Rate** - Конверсия подписок
4. **User Engagement** - Вовлеченность

## 🎨 Примеры использования

### Отслеживание первого входа
```python
await analytics.track_user_session(
    user_id=message.from_user.id,
    username=message.from_user.username,
    is_first_time=True
)
```

### Отслеживание всех кнопок
```python
await analytics.track_button_click(
    user_id=callback.from_user.id,
    button_name="subscribe",
    button_context={"flight_number": "SU100"}
)
```

### Отслеживание ошибок
```python
await analytics.track_error(
    user_id=user_id,
    error_type="api_timeout",
    error_message="API timeout after 30 seconds"
)
```

### Отслеживание API ответов
```python
await analytics.track_api_call(
    user_id=user_id,
    api_name="flight_api",
    success=True,
    response_time=2.5
)
```

## 📋 Чек-лист внедрения

### Обязательные события
- [ ] `user_first_visit` / `user_return_visit`
- [ ] `button_click` (все кнопки)
- [ ] `error` (все ошибки)
- [ ] `api_call` (все API)
- [ ] `command_used` (все команды)

### Дополнительные события
- [ ] `flight_search` (поиск рейсов)
- [ ] `subscription` (подписки)
- [ ] `notification_sent` (уведомления)
- [ ] `user_engagement` (вовлеченность)

### Метрики
- [ ] DAU/WAU дашборд
- [ ] Error rate мониторинг
- [ ] Response time графики
- [ ] Conversion funnel

## 🚀 Быстрый старт

1. **Настройте Amplitude** (см. `QUICK_START_AMPLITUDE.md`)
2. **Добавьте в обработчики**:
   ```python
   await analytics.track_user_session(user_id, username, is_first_time)
   await analytics.track_button_click(user_id, button_name, context)
   await analytics.track_error(user_id, error_type, error_message)
   ```
3. **Протестируйте**: `python test_amplitude.py`
4. **Настройте дашборды** в Amplitude

---

**Результат**: Полная видимость активности пользователей, производительности системы и бизнес-метрик! 🎉 