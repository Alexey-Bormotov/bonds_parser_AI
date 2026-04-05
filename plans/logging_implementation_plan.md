# План реализации логирования

## Требования к логированию
- Базовый уровень (по требованиям пользователя)
- Информация о ходе выполнения
- Ошибки и предупреждения
- Прогресс парсинга (страницы, облигации)

## Уровни логирования

### 1. INFO (основной уровень)
- Старт/завершение работы spider
- Обработка страниц (номер, URL)
- Найденное количество облигаций на странице
- Прогресс (обработано страниц/облигаций)

### 2. WARNING
- Ошибки соединения (таймауты)
- HTTP ошибки (404, 429, 500+)
- Отсутствие ожидаемых элементов на странице
- Нарушение задержек между запросами

### 3. ERROR
- Критические ошибки парсинга
- Ошибки записи данных
- Системные ошибки

### 4. DEBUG (опционально)
- Детали запросов/ответов
- Время выполнения операций
- Состояние внутренних переменных

## Конфигурация логирования

### Настройки в settings.py
```python
# Уровень логирования
LOG_LEVEL = 'INFO'

# Формат логов
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Сохранение логов в файл
LOG_FILE = 'logs/bonds_parser.log'
LOG_ENABLED = True
LOG_STDOUT = True  # Вывод в консоль
```

### Создание структуры логов
```
logs/
  bonds_parser.log        # Основной лог-файл
  bonds_parser_errors.log # Только ошибки (опционально)
```

## Ключевые точки логирования

### 1. Инициализация Spider
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.logger.info("Spider инициализирован")
    self.logger.info(f"Начальный URL: {self.start_urls[0]}")
```

### 2. Обработка страницы
```python
async def parse(self, response):
    self.logger.info(f"Обработка страницы {self.processed_pages}: {response.url}")
    
    # После парсинга
    self.logger.info(f"На странице найдено {len(bonds)} облигаций")
```

### 3. Прогресс парсинга
```python
def log_progress(self):
    self.logger.info(
        f"Прогресс: страниц {self.processed_pages}, "
        f"облигаций {self.total_bonds}"
    )
```

### 4. Завершение работы
```python
def closed(self, reason):
    self.logger.info(f"Spider завершен: {reason}")
    self.logger.info(f"Итог: {self.processed_pages} страниц, {self.total_bonds} облигаций")
```

## Кастомный логгер для мониторинга

```python
import logging

class BondsParserLogger:
    """Кастомный логгер для мониторинга парсинга"""
    
    def __init__(self, spider):
        self.spider = spider
        self.setup_logging()
    
    def setup_logging(self):
        # Настройка файлового хендлера
        file_handler = logging.FileHandler('logs/bonds_parser_detailed.log')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Добавление хендлера к логгеру spider
        self.spider.logger.addHandler(file_handler)
    
    def log_page_processed(self, page_num, url, bonds_count):
        self.spider.logger.info(
            f"Страница {page_num} обработана: {bonds_count} облигаций"
        )
    
    def log_error(self, error_type, url, details=""):
        self.spider.logger.warning(
            f"{error_type} на {url}: {details}"
        )
```

## Интеграция с существующей системой логирования Scrapy

### Использование встроенного логгера
```python
class SmartLabBondsSpider(scrapy.Spider):
    
    def parse(self, response):
        # Использование self.logger (наследуется от scrapy.Spider)
        self.logger.info(f"Начата обработка: {response.url}")
        
        try:
            # ... парсинг ...
            self.logger.debug(f"Детали парсинга: {details}")
        except Exception as e:
            self.logger.error(f"Ошибка парсинга: {e}")
```

## Тестирование логирования

### Проверочные сценарии
1. **Нормальный запуск**: Проверка INFO сообщений о старте
2. **Обработка страниц**: Проверка логов о каждой странице
3. **Ошибки**: Проверка WARNING/ERROR сообщений
4. **Завершение**: Проверка итоговой статистики

### Пример ожидаемых логов
```
2026-04-05 12:00:00 [smartlab_bonds] INFO: Spider инициализирован
2026-04-05 12:00:00 [smartlab_bonds] INFO: Начальный URL: https://smart-lab.ru/...
2026-04-05 12:00:00 [smartlab_bonds] INFO: Обработка страницы 1: https://smart-lab.ru/...
2026-04-05 12:00:05 [smartlab_bonds] INFO: На странице найдено 50 облигаций
2026-04-05 12:00:10 [smartlab_bonds] INFO: Обработка страницы 2: https://smart-lab.ru/...
2026-04-05 12:00:25 [smartlab_bonds] INFO: Spider завершен: finished
2026-04-05 12:00:25 [smartlab_bonds] INFO: Итог: 5 страниц, 250 облигаций
```

## Рекомендации по реализации

1. **Используйте встроенный логгер Scrapy** (self.logger)
2. **Настройте уровни логирования** через settings.py
3. **Добавьте логирование ключевых событий**:
   - Старт/завершение
   - Обработка каждой страницы
   - Найденное количество данных
   - Ошибки
4. **Сохраняйте логи в файл** для последующего анализа
5. **Не логируйте слишком много** на уровне INFO

## Минимальная реализация
```python
# В settings.py
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'

# В spider
self.logger.info(f"Обработка страницы {page_num}")
self.logger.warning(f"Предупреждение: {message}")
self.logger.error(f"Ошибка: {error}")
```

Этого достаточно для базового логирования, требуемого в задании.