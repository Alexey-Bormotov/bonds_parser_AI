# План обработки ошибок

## Основные типы ошибок для обработки

### 1. Ошибки соединения
- Таймауты (TimeoutError, TCPTimedOutError)
- Ошибки DNS
- Отказ соединения

### 2. HTTP ошибки
- 404 (Страница не найдена)
- 429 (Too Many Requests)
- 500+ (Серверные ошибки)

### 3. Ошибки парсинга
- Отсутствие ожидаемых элементов (таблицы, строк)
- Неправильная структура HTML
- Ошибки преобразования данных

### 4. Системные ошибки
- Ошибки записи в файл
- Нехватка памяти
- Прерывание пользователем

## Стратегия обработки

### Минимальная обработка (по требованиям)
- Обрабатывать только ошибки, которые могут остановить парсер
- Не реализовывать повторные попытки
- Логировать ошибки для диагностики

### Ключевые места обработки
1. **Метод `parse` Spider**: Обработка ошибок парсинга таблицы
2. **Метод `handle_error`**: Обработка ошибок запросов
3. **Pipeline**: Обработка ошибок записи данных

## Реализация

### 1. Обработка ошибок запросов (errback)
```python
async def handle_error(self, failure):
    if failure.check(scrapy.exceptions.TimeoutError):
        self.logger.warning(f"Таймаут: {failure.request.url}")
    elif failure.check(scrapy.exceptions.HttpError):
        response = failure.value.response
        self.logger.warning(f"HTTP {response.status}: {failure.request.url}")
    else:
        self.logger.error(f"Ошибка: {failure.getErrorMessage()}")
```

### 2. Валидация данных в методе parse
```python
async def parse(self, response):
    # Проверка HTTP статуса
    if response.status != 200:
        self.logger.error(f"Неверный статус: {response.status}")
        return
    
    # Проверка наличия таблицы
    if not response.css('table.bonds'):
        self.logger.warning("Таблица облигаций не найдена")
        return
    
    # ... парсинг с try-except блоками
```

### 3. Обработка ошибок в Pipeline
```python
def process_item(self, item, spider):
    try:
        # Запись данных
        self.exporter.export_item(item)
    except Exception as e:
        spider.logger.error(f"Ошибка записи: {e}")
        raise
```

## Настройки Scrapy для обработки ошибок
```python
# Отключение повторных попыток (по требованиям)
RETRY_ENABLED = False

# Таймауты
DOWNLOAD_TIMEOUT = 30

# Игнорирование HTTP кодов (не прерывать выполнение)
HTTPERROR_ALLOWED_CODES = [404, 429, 500, 502, 503, 504]
```

## Логирование ошибок
- Уровень WARNING для ожидаемых ошибок (404, таймауты)
- Уровень ERROR для критических ошибок
- Сохранение логов в файл для анализа

## Тестирование обработки ошибок
1. Тестирование на недоступном URL
2. Тестирование на странице с измененной структурой
3. Тестирование таймаутов (имитация медленного соединения)
4. Тестирование ошибок записи на диск