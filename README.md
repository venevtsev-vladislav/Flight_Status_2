# Flight Status Bot

Telegram бот для мониторинга статуса авиарейсов с возможностью подписки на обновления.

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте `env.example` в `.env` и заполните необходимые переменные:

```bash
cp env.example .env
```

Заполните `.env` файл:
```env
BOT_TOKEN=your_telegram_bot_token_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### 3. Настройка Supabase

1. Создайте проект на [supabase.com](https://supabase.com)
2. Выполните SQL скрипт из `supabase/schema.sql` в SQL Editor
3. Создайте Edge Functions:
   - `parse-flight` (из `supabase/functions/parse-flight/index.ts`)
   - `flight-api` (из `supabase/functions/flight-api/index.ts`)

### 4. Создание Telegram бота

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Создайте нового бота командой `/newbot`
3. Скопируйте полученный токен в `.env`

### 5. Запуск бота

```bash
python bot/main.py
```

## 📋 Функциональность MVP

### Основные возможности:
- ✅ Регистрация пользователей
- ✅ Парсинг запросов о рейсах (номер + дата)
- ✅ Получение данных о рейсах через API
- ✅ Отображение карточки рейса
- ✅ Подписка/отписка от обновлений
- ✅ Мультиязычность (EN/RU)
- ✅ Inline кнопки для навигации
- ✅ Логирование всех действий

### Команды:
- `/start` - Начало работы с ботом

### Примеры запросов:
- `SU100 today`
- `QR123 15.07.2025`
- `AFL456 tomorrow`

## Формат возвращаемых данных (карточка рейса)

Функция Supabase Edge (normalizeFlightData) теперь возвращает расширенный набор полей:

- flight_number — основной номер рейса
- status — статус рейса
- codeshares — массив всех кодшеров, включая запрошенный номер (без дублей)
- departure_iata — IATA код аэропорта вылета
- departure_city — название аэропорта вылета
- departure_terminal — терминал вылета
- departure_checkin — стойка регистрации
- departure_gate — гейт
- scheduled_departure_local — запланированное время вылета (локальное)
- actual_departure_local — фактическое/уточнённое время вылета (локальное)
- boarding_time — время посадки (локальное)
- arrival_iata — IATA код аэропорта прилёта
- arrival_city — название аэропорта прилёта
- scheduled_arrival_local — запланированное время прилёта (локальное)
- actual_arrival_local — фактическое/уточнённое время прилёта (локальное)
- baggage_belt — лента выдачи багажа
- landing_time — время посадки самолёта (локальное)
- aircraft_model — модель самолёта
- airline_name — название авиакомпании

### Пример форматирования карточки рейса

```
✈️ SU100 SVO→JFK 10:30 AM
🛎 Статус: Вылетел
🎟 Коды рейса: SU100, KL1234

🛫 SVO / Шереметьево
   🏢 Терминал: D
   🏷 Регистрация: 12-24
   🛂 Гейт: 15
   🕓 Посадка: 09:50 AM
   ⏰ Вылет: 10:35 AM (было 10:30 AM)

🛬 JFK / John F Kennedy
   ⏰ Прилёт: 12:45 PM (ожидалось 12:40 PM)
   🛄 Лента: 5
   🛬 Приземление: 12:50 PM

✈️ Самолёт: Airbus A330
👨‍✈️ Аэрофлот
```

- Все поля опциональны, если данных нет — строка не выводится.
- Коды рейса всегда содержат запрошенный номер и все codeshare, без дублей.
- Время форматируется в 12-часовом формате (например, 10:30 AM).

## Требования к Edge Function (normalizeFlightData)
- Всегда возвращать все перечисленные выше поля (если есть в API).
- Корректно собирать codeshares (см. выше).

## Требования к Python (format_flight_card)
- Форматировать карточку по шаблону выше.
- Не выводить пустые строки/поля.
- Время форматировать в 12-часовом формате.

## 🏗 Архитектура

### Компоненты:
- **Telegram Bot** (aiogram) - UI и взаимодействие
- **Supabase** - база данных и Edge Functions
- **Flight API** - получение данных о рейсах
- **GPT-парсер** - извлечение данных из текста

### Структура проекта:
```
Flight_Status_2/
├── bot/                    # Telegram Bot
│   ├── main.py            # Основной файл
│   ├── config.py          # Конфигурация
│   ├── handlers/          # Обработчики
│   ├── services/          # Бизнес-логика
│   └── keyboards/         # Клавиатуры
├── supabase/              # Supabase конфигурация
│   ├── schema.sql         # Схема БД
│   └── functions/         # Edge Functions
├── docs/                  # Документация
└── requirements.txt       # Зависимости
```

## 📊 База данных

### Основные таблицы:
- `users` - пользователи бота
- `flights` - рейсы
- `flight_details` - детали рейсов
- `subscriptions` - подписки пользователей
- `messages` - сообщения пользователей
- `audit_logs` - логи действий

## 🔧 Разработка

### Установка для разработки:
```bash
# Клонирование репозитория
git clone <repository-url>
cd Flight_Status_2

# Установка зависимостей
pip install -r requirements.txt

# Настройка pre-commit hooks (опционально)
pre-commit install
```

### Тестирование:
```bash
# Запуск тестов
python -m pytest tests/

# Проверка типов
mypy bot/
```

## 🚀 Развертывание

### Локально:
```bash
python bot/main.py
```

### На Railway:
1. Подключите репозиторий к Railway
2. Настройте переменные окружения
3. Railway автоматически развернет бота

### На VPS:
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск через systemd
sudo systemctl enable flight-status-bot
sudo systemctl start flight-status-bot
```

## 📈 Мониторинг

### Логи:
- Все действия пользователей логируются в `audit_logs`
- Ошибки записываются в логи приложения

### Метрики:
- Количество активных пользователей
- Количество запросов рейсов
- Количество подписок
- Время ответа API

## 🔮 Планы развития

### Этап 2:
- [ ] Фоновый воркер для подписок
- [ ] Рассылки при изменении статуса
- [ ] История запросов пользователя
- [ ] Ограничения/лимиты

### Этап 3:
- [ ] Социальные фичи (попутчики)
- [ ] Тарифы/оплата
- [ ] Расширенная аналитика
- [ ] Интеграция с другими API

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Поддержка

Если у вас есть вопросы или проблемы:
- Создайте Issue в GitHub
- Напишите в Telegram: @your_support_username

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot API framework
- [Supabase](https://supabase.com) - Backend as a Service
- [Flight API](https://flight-api.com) - Flight data provider 