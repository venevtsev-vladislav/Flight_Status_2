# Flight Status Bot — Knowledge Base & Changelog

## 🎯 Цель проекта
Создать надёжного Telegram-бота для мониторинга статуса авиарейсов по номеру и дате, с возможностью автоматической подписки на обновления, персонализированным взаимодействием, хранением данных в Supabase и масштабируемой архитектурой.

## 🏗 Архитектура (MVP)

### Компоненты
- **Telegram Bot** (aiogram) — UI и взаимодействие с пользователем
- **Supabase** — основное хранилище данных
- **Edge Functions** — GPT-парсер и Flight API proxy
- **Flight API** — внешний API для получения статуса рейсов
- **Worker** (Railway/CRON) — фоновый воркер для подписок (Этап 2)

### Структура проекта
```
Flight_Status_2/
├── bot/                    # Telegram Bot (aiogram)
│   ├── main.py            # Основной файл бота
│   ├── handlers/          # Обработчики сообщений
│   ├── keyboards/         # Клавиатуры и кнопки
│   ├── services/          # Бизнес-логика
│   └── config.py          # Конфигурация
├── supabase/              # Supabase конфигурация
│   ├── migrations/        # Миграции БД
│   ├── functions/         # Edge Functions
│   └── schema.sql         # Схема таблиц
├── worker/                # Фоновый воркер (Этап 2)
├── docs/                  # Документация
│   ├── CHANGELOG_KNOWLEDGE_BASE.md
│   ├── templates.md       # Шаблоны сообщений
│   └── api_schemas.md     # Схемы API
└── requirements.txt       # Зависимости Python
```

## 📊 Схемы таблиц Supabase

### users
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  language_code TEXT DEFAULT 'en',
  platform TEXT,
  version TEXT,
  first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### flights
```sql
CREATE TABLE flights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flight_number TEXT NOT NULL,
  date DATE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(flight_number, date)
);
```

### flight_details
```sql
CREATE TABLE flight_details (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flight_id UUID REFERENCES flights(id),
  data_source TEXT,
  raw_data JSONB,
  normalized JSONB,
  last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### flight_requests
```sql
CREATE TABLE flight_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  flight_id UUID REFERENCES flights(id),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### subscriptions
```sql
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  flight_id UUID REFERENCES flights(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, flight_id)
);
```

### messages
```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id BIGINT,
  user_id UUID REFERENCES users(id),
  content TEXT,
  parsed_json JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### feature_requests
```sql
CREATE TABLE feature_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  feature_code TEXT NOT NULL,
  flight_id UUID REFERENCES flights(id),
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### flight_logs
```sql
CREATE TABLE flight_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flight_id UUID REFERENCES flights(id),
  status_before TEXT,
  status_after TEXT,
  event_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### translations
```sql
CREATE TABLE translations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key TEXT NOT NULL,
  lang TEXT NOT NULL,
  value TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(key, lang)
);
```

### audit_logs
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  action TEXT NOT NULL,
  details JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔄 Основные сценарии пользователя (MVP)

### 1. Регистрация пользователя
- Пользователь отправляет `/start`
- Бот сохраняет данные в таблицу `users`
- Отправляет приветственное сообщение

### 2. Парсинг запроса
- Пользователь отправляет текст/фото с номером рейса и датой
- Текст отправляется в GPT-парсер (Edge Function)
- Получаем: `{flight_number, date}`
- Если данных не хватает — уточняем у пользователя

### 3. Запрос к Flight API
- Сохраняем запрос в `flight_requests`
- Вызываем Flight API через Edge Function
- Сохраняем результат в `flight_details`

### 4. Карточка рейса
- Формируем карточку из нормализованных данных
- Показываем inline-кнопки:
  - 🔄 Обновить
  - 🔔 Подписаться/Отписаться
  - 🔍 Новый поиск
  - 📋 Мои рейсы

### 5. Обработка ошибок
- Данных нет (будущее) → сохраняем запрос, уведомляем
- Данных нет (прошлое) → кнопка "Ускорить разработку"
- Ошибка парсинга → просим повторить

## 📝 Шаблоны сообщений

### Приветствие
```
👋 Hello, {username}!
I can help you track flight status.
Just type flight number and date, for example:
✈️ SU100 today
📅 AFL123 05.07.2025
```

### Карточка рейса
```
✈️ {flight_number} {departure_iata}→{arrival_iata} {scheduled_departure_local_short}
🛎 {label_status}: {status}
🎟 {label_codeshare}: {codeshares}

🛫 {departure_iata} / {departure_city}
   🏢 {label_terminal}: {departure_terminal}
   🏷 {label_checkin}: {departure_checkin}
   🛂 {label_gate}: {departure_gate}
   🕓 {label_boarding}: {boarding_time}
   ⏰ {label_departure}: {actual_departure_local} ({label_was} {scheduled_departure_local})

🛬 {arrival_iata} / {arrival_city}
   ⏰ {label_arrival}: {actual_arrival_local} ({label_expected} {scheduled_arrival_local})
   🛄 {label_belt}: {baggage_belt}
   🛬 {label_landed}: {landing_time}

✈️ {label_aircraft}: {aircraft_model}
👨‍✈️ {airline_name}
```

## 🚀 Этапы разработки

### Этап 1 (MVP) - СЕГОДНЯ
- [x] Создание структуры проекта
- [ ] Настройка Supabase (таблицы, Edge Functions)
- [ ] Telegram Bot (aiogram) - базовая структура
- [ ] Регистрация пользователя
- [ ] GPT-парсер (Edge Function)
- [ ] Flight API интеграция (Edge Function)
- [ ] Карточка рейса + inline-кнопки
- [ ] Сохранение запросов и логов
- [ ] Базовые шаблоны сообщений
- [ ] Мультиязычность (en/ru)

### Этап 2 (Ближайшее будущее)
- [ ] Фоновый воркер для подписок (Railway/CRON)
- [ ] Рассылки при изменении статуса рейса
- [ ] История запросов пользователя
- [ ] Кнопка "Ускорить разработку" для новых фич
- [ ] Ограничения/лимиты для пользователей
- [ ] Расширенное логирование

### Этап 3+ (Долгосрочные планы)
- [ ] Социальные фичи (попутчики, поделиться)
- [ ] Тарифы/оплата
- [ ] Расширенная аналитика
- [ ] Интеграция с другими API
- [ ] Рассылки о новых фичах

## 📋 TODO (MVP) - СЕГОДНЯ

### Supabase Setup
- [ ] Создать проект Supabase
- [ ] Выполнить миграции (создать таблицы)
- [ ] Настроить Edge Functions
- [ ] Добавить переводы в таблицу translations

### Telegram Bot
- [ ] Создать бота через @BotFather
- [ ] Настроить aiogram
- [ ] Реализовать /start команду
- [ ] Обработчик текстовых сообщений
- [ ] Обработчик фото (билеты)
- [ ] Inline-кнопки и их обработчики
- [ ] Интеграция с Supabase

### Edge Functions
- [ ] GPT-парсер для извлечения flight_number и date
- [ ] Flight API proxy
- [ ] Нормализация данных рейса

### Тестирование
- [ ] Тест регистрации пользователя
- [ ] Тест парсинга запроса
- [ ] Тест получения данных рейса
- [ ] Тест inline-кнопок

## 🔧 Технические детали

### Лимиты и ограничения
- Flight API: ограничения по запросам (уточнить в ТЗ)
- Telegram Bot: 30 сообщений в секунду
- Supabase: лимиты на Edge Functions

### Безопасность
- Все данные в Supabase (не в памяти бота)
- Идемпотентные операции
- Логирование всех действий
- Валидация входных данных

### Масштабируемость
- Stateless архитектура
- Использование updated_at и version полей
- Подготовка к фоновому воркеру

## 📈 Метрики и мониторинг

### Ключевые метрики
- Количество активных пользователей
- Количество запросов рейсов
- Количество подписок
- Время ответа API
- Ошибки парсинга

### Логирование
- Все действия пользователей в audit_logs
- Ошибки и исключения
- Производительность API вызовов

## 🔄 Изменения

### 2024-06-XX (Сегодня)
- [x] Создан проект и структура
- [x] Определена архитектура MVP
- [x] Созданы схемы таблиц Supabase
- [x] Определены основные сценарии пользователя
- [x] Создана структура Telegram Bot (aiogram)
- [x] Реализованы Edge Functions для парсинга и API
- [x] Созданы обработчики сообщений и callback'ов
- [x] Настроена мультиязычность (EN/RU)
- [x] Создана документация и README
- [ ] Настройка Supabase проекта
- [ ] Создание Telegram бота через @BotFather
- [ ] Тестирование MVP функциональности

## 📚 Полезные ссылки

- [aiogram документация](https://docs.aiogram.dev/)
- [Supabase документация](https://supabase.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Flight API документация] (уточнить)

## 🎯 Следующие шаги

1. **Настроить Supabase проект:**
   - Создать проект на supabase.com
   - Выполнить SQL скрипт из `supabase/schema.sql`
   - Создать Edge Functions (parse-flight, flight-api)

2. **Создать Telegram бота:**
   - Написать @BotFather в Telegram
   - Создать бота командой `/newbot`
   - Получить токен и добавить в `.env`

3. **Настроить переменные окружения:**
   - Скопировать `env.example` в `.env`
   - Заполнить BOT_TOKEN, SUPABASE_URL, SUPABASE_ANON_KEY

4. **Запустить и протестировать:**
   - Установить зависимости: `pip install -r requirements.txt`
   - Запустить бота: `python bot/main.py`
   - Протестировать основные сценарии

## 📁 Созданные файлы

### Основная структура:
- `bot/main.py` - Главный файл бота
- `bot/config.py` - Конфигурация и настройки
- `bot/services/database.py` - Сервис для работы с Supabase
- `bot/services/flight_service.py` - Сервис для работы с Flight API
- `bot/handlers/start.py` - Обработчик команды /start
- `bot/handlers/text.py` - Обработчик текстовых сообщений
- `bot/handlers/callbacks.py` - Обработчик inline кнопок
- `bot/keyboards/inline_keyboards.py` - Inline клавиатуры

### Supabase:
- `supabase/schema.sql` - Схема базы данных
- `supabase/functions/parse-flight/index.ts` - Edge Function для парсинга
- `supabase/functions/flight-api/index.ts` - Edge Function для Flight API

### Документация:
- `docs/CHANGELOG_KNOWLEDGE_BASE.md` - База знаний и changelog
- `README.md` - Инструкции по установке и использованию
- `requirements.txt` - Python зависимости
- `env.example` - Пример переменных окружения 

---

## Что делать дальше

### 1. Проверить переменные окружения ОС
Выполните в терминале:
```sh
env | grep -i proxy
```
Если увидите что-то типа:
```
HTTP_PROXY=http://...
HTTPS_PROXY=http://...
```
— временно удалите их из окружения или перезапустите терминал без них.

---

### 2. Проверить, не установлен ли старый aiogram параллельно
Выполните:
```sh
pip freeze | grep aiogram
```
Должна быть только одна строка с `aiogram==3.4.1`.

---

### 3. Проверить, не подменён ли httpx или aiogram
Выполните:
```sh
pip show httpx
pip show aiogram
```
Убедитесь, что это официальные пакеты.

---

### 4. Попробовать создать новый виртуальный env
Иногда старые зависимости или мусор в окружении могут вызывать такие баги.  
Создайте новый виртуальный env и установите только нужные зависимости:

```sh
python3 -m venv venv-test
source venv-test/bin/activate
pip install -r requirements.txt
python -m bot.main
```

---

**Если после этих шагов ошибка останется — пришлите вывод всех команд сюда.  
Это поможет точно локализовать источник проблемы!**

---

**P.S.**  
Ошибка не в вашем коде, а в окружении или сторонних зависимостях.  
Если хотите, я могу дать готовый скрипт для всех этих проверок.  
Скажите, если нужно! 