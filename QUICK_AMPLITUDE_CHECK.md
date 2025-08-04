# ⚡ Быстрая проверка Amplitude

## 🚀 5 минут до работающей аналитики

### Шаг 1: Проверка текущего статуса
```bash
python check_amplitude_status.py
```

### Шаг 2: Если есть проблемы - настройка

#### 2.1 Создайте проект в Amplitude
1. Зайдите на [amplitude.com](https://amplitude.com)
2. Создайте аккаунт и проект "Flight Status Bot"
3. Получите API ключи в Settings → API Keys

#### 2.2 Настройте переменные окружения
```bash
# Скопируйте пример
cp env.example .env

# Отредактируйте .env и добавьте:
AMPLITUDE_API_KEY=your_api_key_here
AMPLITUDE_SECRET_KEY=your_secret_key_here
AMPLITUDE_PROJECT_ID=your_project_id_here
```

### Шаг 3: Тестирование
```bash
# Проверьте статус
python check_amplitude_status.py

# Запустите тесты
python test_amplitude.py
```

### Шаг 4: Проверка в Amplitude
1. Зайдите в ваш проект Amplitude
2. Перейдите в Events → Event Segmentation
3. Найдите события:
   - `user_action_test_action`
   - `api_call`
   - `error`
   - `flight_search`
   - `subscription`

### Шаг 5: Запуск бота
```bash
python run.py
```

## ✅ Что должно работать

### В логах бота:
```
INFO - Analytics service initialized
DEBUG - Successfully sent X events to Amplitude
```

### В Amplitude:
- События появляются в реальном времени
- Пользователи отображаются в User Lookup
- Можно создавать дашборды

## 🚨 Если что-то не работает

### Проблема: "Аналитика отключена"
```bash
# Проверьте .env файл
cat .env | grep AMPLITUDE
```

### Проблема: "События не появляются"
1. Подождите 5-10 минут
2. Проверьте API ключи
3. Запустите `python test_amplitude.py`

### Проблема: "Ошибки в логах"
```bash
# Проверьте подключение
python check_amplitude_status.py
```

## 📊 Первые метрики для отслеживания

1. **DAU** - Ежедневные активные пользователи
2. **Популярные рейсы** - Топ поисков
3. **Ошибки** - Частота и типы ошибок
4. **Время ответа** - Производительность API

## 🎯 Следующие шаги

1. Создайте дашборд в Amplitude
2. Настройте алерты для ошибок
3. Анализируйте данные еженедельно
4. Оптимизируйте бота на основе данных

---

**Готово!** Ваш бот теперь собирает аналитику в Amplitude! 🎉 