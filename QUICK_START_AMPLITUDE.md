# 🚀 Быстрый старт с Amplitude

## Шаг 1: Создание проекта в Amplitude

1. **Зарегистрируйтесь** на [amplitude.com](https://amplitude.com)
2. **Создайте новый проект**:
   - Нажмите "Create New Project"
   - Введите название: "Flight Status Bot"
   - Выберите платформу: "Other"
3. **Получите API ключи**:
   - Перейдите в Settings → API Keys
   - Скопируйте API Key, Secret Key и Project ID

## Шаг 2: Настройка переменных окружения

Добавьте в ваш `.env` файл:

```env
# Amplitude Analytics
AMPLITUDE_API_KEY=your_api_key_here
AMPLITUDE_SECRET_KEY=your_secret_key_here
AMPLITUDE_PROJECT_ID=your_project_id_here
```

## Шаг 3: Тестирование интеграции

Запустите тестовый скрипт:

```bash
python test_amplitude.py
```

Вы должны увидеть:
```
✅ Сервис аналитики инициализирован
📊 Отправка тестовых событий...
📤 Отправка событий в Amplitude...
✅ Тестирование завершено!
```

## Шаг 4: Проверка в Amplitude

1. Зайдите в ваш проект Amplitude
2. Перейдите в раздел "Events"
3. Найдите события:
   - `user_action_test_action`
   - `api_call`
   - `error`
   - `flight_search`
   - `subscription`

## Шаг 5: Запуск бота

```bash
python run.py
```

Теперь ваш бот будет автоматически отправлять аналитику в Amplitude!

## 📊 Что отслеживается

### Автоматически:
- ✅ Запуск бота (`/start`)
- ✅ Поиск рейсов
- ✅ API вызовы и ошибки
- ✅ Подписки на рейсы
- ✅ Нажатия кнопок

### Ручное добавление:
```python
# В любом обработчике
await analytics.track_user_action(
    user_id=message.from_user.id,
    action="custom_action",
    context={"data": "value"}
)
```

## 🎯 Первые дашборды

### 1. Обзор активности
- **Событие**: `user_action_start_command`
- **Метрика**: Количество запусков бота

### 2. Популярные рейсы
- **Событие**: `flight_search`
- **Метрика**: Популярные номера рейсов

### 3. Производительность
- **Событие**: `api_call`
- **Метрика**: Время ответа API

## 🔧 Настройка дашбордов

1. **Создайте дашборд** в Amplitude
2. **Добавьте графики**:
   - Event Segmentation
   - User Segmentation
   - Funnel Analysis
3. **Настройте алерты** для важных метрик

## 📈 Ключевые метрики

| Метрика | Событие | Описание |
|---------|---------|----------|
| DAU | `user_action_start_command` | Ежедневные активные пользователи |
| Популярные рейсы | `flight_search` | Топ рейсов по поискам |
| Время ответа | `api_call` | Производительность API |
| Ошибки | `error` | Количество и типы ошибок |
| Подписки | `subscription` | Конверсия подписок |

## 🚨 Устранение проблем

### Аналитика не работает
1. Проверьте переменные окружения
2. Убедитесь, что `ANALYTICS.enabled = True`
3. Проверьте логи на ошибки

### События не появляются
1. Подождите 5-10 минут (задержка Amplitude)
2. Проверьте API ключи
3. Запустите тестовый скрипт

### Высокая нагрузка
1. Увеличьте `batch_size` в конфигурации
2. Увеличьте `flush_interval`
3. Мониторьте логи производительности

## 📞 Поддержка

- 📖 [Полная документация](docs/AMPLITUDE_INTEGRATION.md)
- 🐛 [Создать Issue](https://github.com/your-repo/issues)
- 💬 [Telegram поддержка](https://t.me/your-support)

---

**Готово!** Ваш бот теперь собирает аналитику в Amplitude. 🎉 