# Руководство по деплою Flight Status Bot

## Подготовка к деплою

### 1. Создайте файл .env
Скопируйте `env.example` в `.env` и заполните все переменные окружения:

```bash
cp env.example .env
```

Заполните следующие переменные:
- `BOT_TOKEN` - токен вашего Telegram бота
- `SUPABASE_URL` - URL вашего Supabase проекта
- `SUPABASE_ANON_KEY` - анонимный ключ Supabase
- `AERODATABOX_API_KEY` - ключ API RapidAPI для AeroDataBox
- `AMPLITUDE_API_KEY` - ключ API Amplitude (опционально)
- `AMPLITUDE_SECRET_KEY` - секретный ключ Amplitude (опционально)
- `AMPLITUDE_PROJECT_ID` - ID проекта Amplitude (опционально)

## Варианты деплоя

### 1. Railway (Рекомендуется)

Railway - отличная платформа для Python приложений с бесплатным тарифом.

#### Шаги:
1. Зарегистрируйтесь на [railway.app](https://railway.app)
2. Подключите ваш GitHub репозиторий
3. Создайте новый проект
4. Добавьте переменные окружения в настройках проекта
5. Railway автоматически обнаружит Dockerfile и запустит бота

#### Переменные окружения для Railway:
```
BOT_TOKEN=your_telegram_bot_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
AERODATABOX_API_KEY=your_rapidapi_key
AMPLITUDE_API_KEY=your_amplitude_api_key
AMPLITUDE_SECRET_KEY=your_amplitude_secret_key
AMPLITUDE_PROJECT_ID=your_amplitude_project_id
```

### 2. Render

Render предлагает бесплатный хостинг для веб-приложений.

#### Шаги:
1. Зарегистрируйтесь на [render.com](https://render.com)
2. Подключите ваш GitHub репозиторий
3. Создайте новый Web Service
4. Настройте переменные окружения
5. Укажите команду запуска: `python run.py`

### 3. Heroku

Heroku - классический выбор для Python приложений.

#### Шаги:
1. Установите Heroku CLI
2. Войдите в аккаунт: `heroku login`
3. Создайте приложение: `heroku create your-bot-name`
4. Добавьте переменные окружения:
   ```bash
   heroku config:set BOT_TOKEN=your_token
   heroku config:set SUPABASE_URL=your_url
   heroku config:set SUPABASE_ANON_KEY=your_key
   heroku config:set AERODATABOX_API_KEY=your_key
   ```
5. Деплой: `git push heroku main`

### 4. DigitalOcean App Platform

#### Шаги:
1. Создайте аккаунт на DigitalOcean
2. Перейдите в App Platform
3. Подключите GitHub репозиторий
4. Выберите Dockerfile как способ деплоя
5. Настройте переменные окружения

### 5. VPS (Vultr, Linode, AWS EC2)

#### Шаги:
1. Создайте VPS с Ubuntu 20.04+
2. Подключитесь по SSH
3. Установите Docker:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```
4. Клонируйте репозиторий
5. Создайте .env файл
6. Запустите: `docker-compose up -d`

## Локальное тестирование

### С Docker:
```bash
# Сборка образа
docker build -t flight-status-bot .

# Запуск
docker run --env-file .env flight-status-bot
```

### С Docker Compose:
```bash
docker-compose up --build
```

## Мониторинг и логи

### Просмотр логов:
```bash
# Docker
docker logs flight-status-bot

# Docker Compose
docker-compose logs -f
```

### Проверка статуса:
```bash
# Docker
docker ps

# Docker Compose
docker-compose ps
```

## Перезапуск бота

### Docker:
```bash
docker restart flight-status-bot
```

### Docker Compose:
```bash
docker-compose restart
```

## Обновление бота

1. Внесите изменения в код
2. Зафиксируйте изменения: `git add . && git commit -m "Update"`
3. Отправьте в репозиторий: `git push`
4. Хостинг автоматически пересоберет и перезапустит бота

## Устранение неполадок

### Бот не отвечает:
1. Проверьте логи на хостинге
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что токен бота действителен

### Ошибки подключения к Supabase:
1. Проверьте URL и ключи Supabase
2. Убедитесь, что Edge Functions развернуты
3. Проверьте настройки CORS в Supabase

### Проблемы с API:
1. Проверьте ключ AeroDataBox API
2. Убедитесь, что у вас есть активная подписка на RapidAPI

## Безопасность

- Никогда не коммитьте .env файл в Git
- Используйте разные токены для разработки и продакшена
- Регулярно обновляйте зависимости
- Мониторьте использование API ключей

## Масштабирование

Для увеличения производительности:
1. Увеличьте количество реплик в настройках хостинга
2. Настройте балансировщик нагрузки
3. Используйте кэширование для API запросов
4. Оптимизируйте запросы к базе данных 