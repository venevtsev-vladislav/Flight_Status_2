# Flight Status Bot

Telegram бот для отслеживания статуса рейсов в реальном времени.

## 🚀 Быстрый деплой

### 1. Подготовка
```bash
# Скопируйте файл с переменными окружения
cp env.example .env

# Заполните все переменные в .env файле
```

### 2. Деплой на Railway (Рекомендуется)
```bash
# Установите Railway CLI
npm install -g @railway/cli

# Войдите в аккаунт
railway login

# Деплой
./deploy.sh railway
```

### 3. Деплой на другие платформы
```bash
# Render
./deploy.sh render

# Heroku
./deploy.sh heroku

# Docker
./deploy.sh docker

# Docker Compose
./deploy.sh docker-compose
```

## 📋 Требования

- Python 3.11+
- Telegram Bot Token
- Supabase проект
- AeroDataBox API ключ (RapidAPI)

## 🔧 Установка

### Локальная разработка
```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd Flight_Status_3

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Настройте переменные окружения
cp env.example .env
# Отредактируйте .env файл

# Запустите бота
python run.py
```

### С Docker
```bash
# Сборка и запуск
docker-compose up --build

# Или с Docker
docker build -t flight-status-bot .
docker run --env-file .env flight-status-bot
```

## 🌐 Деплой на хостинг

### Railway (Бесплатно)
1. Зарегистрируйтесь на [railway.app](https://railway.app)
2. Подключите GitHub репозиторий
3. Добавьте переменные окружения
4. Railway автоматически обнаружит Dockerfile

### Render (Бесплатно)
1. Зарегистрируйтесь на [render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите репозиторий
4. Укажите команду запуска: `python run.py`

### Heroku
1. Установите Heroku CLI
2. Создайте приложение: `heroku create`
3. Добавьте переменные окружения
4. Деплой: `git push heroku main`

## 📁 Структура проекта

```
Flight_Status_3/
├── bot/                    # Основной код бота
│   ├── config.py          # Конфигурация
│   ├── main.py            # Точка входа
│   ├── handlers/          # Обработчики сообщений
│   ├── keyboards/         # Клавиатуры
│   └── services/          # Сервисы
├── supabase/              # Supabase Edge Functions
├── requirements.txt        # Python зависимости
├── Dockerfile             # Docker конфигурация
├── docker-compose.yml     # Docker Compose
├── deploy.sh              # Скрипт деплоя
└── DEPLOYMENT_GUIDE.md    # Подробное руководство
```

## 🔑 Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | ✅ |
| `SUPABASE_URL` | URL Supabase проекта | ✅ |
| `SUPABASE_ANON_KEY` | Анонимный ключ Supabase | ✅ |
| `AERODATABOX_API_KEY` | Ключ API RapidAPI | ✅ |
| `AMPLITUDE_API_KEY` | Ключ Amplitude API | ❌ |
| `AMPLITUDE_SECRET_KEY` | Секретный ключ Amplitude | ❌ |
| `AMPLITUDE_PROJECT_ID` | ID проекта Amplitude | ❌ |

## 🚀 Команды

```bash
# Запуск бота
python run.py

# Деплой на Railway
./deploy.sh railway

# Деплой на Heroku
./deploy.sh heroku

# Запуск с Docker
docker-compose up

# Просмотр логов
docker-compose logs -f
```

## 📊 Мониторинг

- Логи доступны в панели управления хостинга
- Amplitude аналитика (если настроена)
- Supabase Edge Functions логи

## 🔧 Устранение неполадок

### Бот не отвечает
1. Проверьте логи на хостинге
2. Убедитесь, что все переменные окружения установлены
3. Проверьте токен бота

### Ошибки API
1. Проверьте ключи API
2. Убедитесь в активности подписок
3. Проверьте лимиты запросов

## 📝 Лицензия

MIT License

## 🤝 Поддержка

Если у вас есть вопросы или проблемы:
1. Проверьте [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Создайте issue в репозитории
3. Обратитесь к документации платформы хостинга 