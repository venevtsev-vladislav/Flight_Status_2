# Интеграция Amplitude в Telegram бот

## Обзор

Этот документ описывает интеграцию Amplitude для сбора аналитики в Telegram боте для отслеживания статуса рейсов.

## Настройка Amplitude

### 1. Создание проекта в Amplitude

1. Зайдите на [amplitude.com](https://amplitude.com)
2. Создайте новый проект
3. Получите API ключи:
   - API Key
   - Secret Key
   - Project ID

### 2. Настройка переменных окружения

Добавьте следующие переменные в ваш `.env` файл:

```env
# Amplitude Analytics settings
AMPLITUDE_API_KEY=your_amplitude_api_key_here
AMPLITUDE_SECRET_KEY=your_amplitude_secret_key_here
AMPLITUDE_PROJECT_ID=your_amplitude_project_id_here
```

### 3. Настройка конфигурации

В файле `bot/config.py` уже настроены параметры для Amplitude:

```python
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
```

## Использование AnalyticsService

### Инициализация

Сервис автоматически инициализируется в `main.py`:

```python
analytics_service = AnalyticsService()
dp["analytics"] = analytics_service
```

### Основные методы

#### 1. Отслеживание пользовательских действий

```python
await analytics.track_user_action(
    user_id=message.from_user.id,
    action="start_command",
    context={"username": message.from_user.username}
)
```

#### 2. Отслеживание API вызовов

```python
await analytics.track_api_call(
    user_id=user_id,
    api_name="flight_search",
    success=True,
    response_time=2.5
)
```

#### 3. Отслеживание ошибок

```python
await analytics.track_error(
    user_id=user_id,
    error_type="api_error",
    error_message="API timeout",
    context={"api_name": "flight_api"}
)
```

#### 4. Отслеживание поиска рейсов

```python
await analytics.track_flight_search(
    user_id=user_id,
    flight_number="SU100",
    date="2024-01-15",
    success=True,
    response_time=1.5
)
```

#### 5. Отслеживание подписок

```python
await analytics.track_subscription(
    user_id=user_id,
    action="subscribe",
    flight_number="SU100",
    date="2024-01-15"
)
```

## События, которые отслеживаются

### Пользовательские действия
- `start_command` - пользователь запустил бота
- `search_command` - пользователь начал поиск
- `reset_command` - пользователь сбросил состояние
- `button_click` - нажатие на кнопки
- `language_change` - смена языка

### API вызовы
- `flight_search` - поиск рейса
- `flight_api` - вызов API рейсов
- `parse_flight` - парсинг номера рейса

### Ошибки
- `api_error` - ошибки API
- `parse_error` - ошибки парсинга
- `database_error` - ошибки базы данных

### Подписки
- `subscribe` - подписка на рейс
- `unsubscribe` - отписка от рейса

## Конфигурация

### Параметры батчинга

```python
"batch_size": 100,        # Количество событий в батче
"flush_interval": 10,     # Интервал отправки в секундах
```

### Параметры повторных попыток

```python
"max_retries": 3,         # Максимальное количество попыток
"timeout": 30             # Таймаут запроса в секундах
```

## Мониторинг

### Логирование

Сервис логирует все важные события:

```
INFO - Analytics service initialized
DEBUG - Successfully sent 50 events to Amplitude
ERROR - Failed to send events to Amplitude: 400 - Bad Request
```

### Метрики для отслеживания

1. **Активность пользователей**
   - Количество новых пользователей
   - Количество активных пользователей
   - Частота использования команд

2. **Производительность**
   - Время ответа API
   - Количество ошибок
   - Успешность запросов

3. **Пользовательский опыт**
   - Путь пользователя
   - Точки выхода
   - Популярные функции

## Дашборды в Amplitude

### Рекомендуемые дашборды

1. **Обзор активности**
   - Ежедневные активные пользователи
   - Количество событий по типам
   - География пользователей

2. **Производительность**
   - Время ответа API
   - Количество ошибок
   - Успешность запросов

3. **Пользовательский путь**
   - Воронка использования
   - Точки выхода
   - Популярные функции

### Настройка дашбордов

1. Создайте новый дашборд в Amplitude
2. Добавьте графики:
   - Event Segmentation для анализа событий
   - User Segmentation для анализа пользователей
   - Funnel Analysis для анализа воронки

## Отладка

### Проверка подключения

```python
# В коде
await analytics.track_event(
    user_id=123456,
    event_type="test_event",
    event_properties={"test": True}
)
```

### Проверка в Amplitude

1. Зайдите в проект Amplitude
2. Перейдите в раздел "Events"
3. Найдите событие "test_event"
4. Убедитесь, что событие появилось

### Логи для отладки

```python
# Включите debug логирование
logging.getLogger("bot.services.analytics_service").setLevel(logging.DEBUG)
```

## Безопасность

### Защита данных

1. **Анонимизация**: ID пользователей хешируются
2. **Ограничение данных**: Отправляются только необходимые данные
3. **Валидация**: Все данные проверяются перед отправкой

### Настройки приватности

```python
# В конфигурации
ANALYTICS = {
    "privacy": {
        "hash_user_ids": True,
        "exclude_sensitive_data": True,
        "data_retention_days": 90
    }
}
```

## Производительность

### Оптимизация

1. **Батчинг**: События отправляются батчами
2. **Асинхронность**: Неблокирующие запросы
3. **Кэширование**: Буферизация событий

### Мониторинг производительности

```python
# Отслеживание времени ответа
start_time = time.time()
# ... выполнение операции ...
response_time = time.time() - start_time

await analytics.track_api_call(
    user_id=user_id,
    api_name="flight_search",
    success=True,
    response_time=response_time
)
```

## Заключение

Интеграция Amplitude позволяет:

1. **Понимать пользователей**: Анализировать поведение и предпочтения
2. **Улучшать продукт**: Находить проблемы и возможности
3. **Измерять успех**: Отслеживать ключевые метрики
4. **Принимать решения**: Использовать данные для развития продукта

Для получения дополнительной информации обратитесь к [документации Amplitude](https://developers.amplitude.com/). 