# План настройки задержек между запросами

## Требования к задержкам
- Минимальная задержка между запросами: **5 секунд**
- Имитация поведения реального пользователя
- Избежание блокировки IP адреса
- Соблюдение правил robots.txt (если применимо)

## Стратегии реализации задержек

### 1. Базовая настройка Scrapy (settings.py)

```python
# Минимальная задержка между запросами (5 секунд)
DOWNLOAD_DELAY = 5

# Случайная добавка к задержке (имитация пользователя)
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_DELAY_RANDOMIZE_ADDITION = 2  # Добавляет от 0 до 2 секунд

# Итоговая задержка: от 5 до 7 секунд
```

### 2. Автоматическое регулирование скорости (AutoThrottle)

```python
# Включение автоматического регулирования
AUTOTHROTTLE_ENABLED = True

# Начальная задержка (совпадает с DOWNLOAD_DELAY)
AUTOTHROTTLE_START_DELAY = 5

# Максимальная задержка при регулировании
AUTOTHROTTLE_MAX_DELAY = 10

# Целевая параллельность (меньше = больше задержка)
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5

# Отслеживание задержек
AUTOTHROTTLE_DEBUG = False  # True для отладки
```

### 3. Middleware для точного контроля

```python
import time
import random
import logging
from scrapy import signals


class PreciseDelayMiddleware:
    """
    Middleware для точного контроля задержек между запросами.
    Гарантирует минимальную задержку 5 секунд между запросами.
    """
    
    def __init__(self, delay, random_addition):
        self.delay = delay
        self.random_addition = random_addition
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        # Получение настроек из crawler
        delay = crawler.settings.getfloat('DOWNLOAD_DELAY', 5)
        random_addition = crawler.settings.getfloat('DOWNLOAD_DELAY_RANDOMIZE_ADDITION', 2)
        
        # Создание экземпляра middleware
        instance = cls(delay, random_addition)
        
        # Подключение сигналов
        crawler.signals.connect(instance.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(instance.spider_closed, signal=signals.spider_closed)
        
        return instance
    
    def spider_opened(self, spider):
        spider.logger.info(
            f"PreciseDelayMiddleware инициализирован: "
            f"базовая задержка={self.delay}с, "
            f"случайная добавка={self.random_addition}с"
        )
    
    def spider_closed(self, spider):
        spider.logger.info("PreciseDelayMiddleware завершил работу")
    
    def process_request(self, request, spider):
        """
        Обработка каждого запроса с добавлением задержки.
        """
        current_time = time.time()
        
        # Расчет времени с последнего запроса
        time_since_last = current_time - self.last_request_time
        
        if self.last_request_time > 0 and time_since_last < self.delay:
            # Не прошло достаточно времени, добавляем задержку
            sleep_time = self.delay - time_since_last
            
            # Добавляем случайную составляющую
            if self.random_addition > 0:
                random_sleep = random.uniform(0, self.random_addition)
                sleep_time += random_sleep
            
            # Применяем задержку
            if sleep_time > 0:
                spider.logger.debug(
                    f"Задержка запроса: {sleep_time:.2f} секунд "
                    f"(прошло {time_since_last:.2f}с с последнего запроса)"
                )
                time.sleep(sleep_time)
        
        # Обновляем время последнего запроса
        self.last_request_time = time.time()
        
        # Добавляем информацию о задержке в метаданные запроса
        request.meta['request_delay_applied'] = True
        request.meta['request_timestamp'] = self.last_request_time
```

### 4. Domain-specific задержки

```python
class DomainAwareDelayMiddleware:
    """
    Middleware для различных задержек в зависимости от домена.
    Полезно при парсинге нескольких сайтов.
    """
    
    def __init__(self):
        self.domain_delays = {
            'smart-lab.ru': {
                'min_delay': 5,
                'max_delay': 7,
                'last_request': 0
            }
        }
    
    def process_request(self, request, spider):
        domain = request.url.split('/')[2]  # Извлечение домена из URL
        
        if domain in self.domain_delays:
            config = self.domain_delays[domain]
            current_time = time.time()
            
            # Проверка времени с последнего запроса к этому домену
            time_since_last = current_time - config['last_request']
            required_delay = config['min_delay']
            
            if time_since_last < required_delay:
                sleep_time = required_delay - time_since_last
                time.sleep(sleep_time)
                spider.logger.debug(f"Domain-aware задержка для {domain}: {sleep_time:.2f}с")
            
            # Обновление времени последнего запроса
            config['last_request'] = time.time()
```

## Конфигурация в settings.py

### Полная конфигурация задержек
```python
# ===== НАСТРОЙКИ ЗАДЕРЖЕК =====

# Базовая задержка между запросами (требование: ≥5 секунд)
DOWNLOAD_DELAY = 5

# Случайная добавка к задержке (имитация пользователя)
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_DELAY_RANDOMIZE_ADDITION = 2  # 0-2 секунды случайной добавки

# Автоматическое регулирование скорости
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = DOWNLOAD_DELAY
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
AUTOTHROTTLE_DEBUG = False

# Ограничение параллельных запросов
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Таймауты
DOWNLOAD_TIMEOUT = 30
RETRY_ENABLED = False  # По требованиям - повторные попытки не нужны

# ===== MIDDLEWARE КОНФИГУРАЦИЯ =====

DOWNLOADER_MIDDLEWARES = {
    # Стандартные middleware
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': None,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 400,
    
    # Кастомные middleware для задержек
    'bonds_parser.middlewares.PreciseDelayMiddleware': 543,
    'bonds_parser.middlewares.RandomUserAgentMiddleware': 545,
    'bonds_parser.middlewares.DomainAwareDelayMiddleware': 550,
    
    # Отключаем стандартный UserAgentMiddleware
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}
```

## Валидация соблюдения задержек

### Мониторинг задержек в реальном времени
```python
class DelayMonitor:
    """Мониторинг и валидация задержек между запросами"""
    
    def __init__(self):
        self.request_times = []
        self.min_allowed_delay = 5
    
    def log_request(self, url, timestamp):
        """Логирование времени запроса"""
        self.request_times.append((url, timestamp))
        
        # Проверка задержки между последними двумя запросами
        if len(self.request_times) >= 2:
            last_url, last_time = self.request_times[-2]
            current_url, current_time = self.request_times[-1]
            actual_delay = current_time - last_time
            
            if actual_delay < self.min_allowed_delay:
                print(f"⚠️  Нарушение задержки: {actual_delay:.2f}с между {last_url} и {current_url}")
            else:
                print(f"✓  Задержка соблюдена: {actual_delay:.2f}с")
    
    def get_statistics(self):
        """Получение статистики по задержкам"""
        if len(self.request_times) < 2:
            return {"total_requests": len(self.request_times), "average_delay": 0}
        
        delays = []
        for i in range(1, len(self.request_times)):
            delay = self.request_times[i][1] - self.request_times[i-1][1]
            delays.append(delay)
        
        return {
            "total_requests": len(self.request_times),
            "average_delay": sum(delays) / len(delays),
            "min_delay": min(delays),
            "max_delay": max(delays),
            "violations": sum(1 for d in delays if d < self.min_allowed_delay)
        }
```

### Интеграция с Spider
```python
class SmartLabBondsSpider(scrapy.Spider):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delay_monitor = DelayMonitor()
    
    async def parse(self, response):
        # Логирование времени запроса
        import time
        self.delay_monitor.log_request(response.url, time.time())
        
        # ... остальной код парсинга ...
        
    def closed(self, reason):
        """Вызывается при завершении spider"""
        stats = self.delay_monitor.get_statistics()
        self.logger.info(f"Статистика задержек: {stats}")
        
        # Проверка соблюдения требований
        if stats['violations'] > 0:
            self.logger.warning(f"Обнаружено {stats['violations']} нарушений минимальной задержки")
        else:
            self.logger.info("Все задержки соблюдены (≥5 секунд)")
```

## Тестирование задержек

### Тестовый скрипт
```python
import scrapy
from scrapy.crawler import CrawlerProcess
from bonds_parser.spiders.smartlab_bonds_spider import SmartLabBondsSpider
import time

def test_delays():
    """Тестирование соблюдения задержек"""
    
    class TestSpider(SmartLabBondsSpider):
        name = "test_delays"
        start_urls = [
            "https://smart-lab.ru/q/bonds/order_by_coupon_value/desc/page1/?paids_year=12",
            "https://smart-lab.ru/q/bonds/order_by_coupon_value/desc/page2/?paids_year=12",
            "https://smart-lab.ru/q/bonds/order_by_coupon_value/desc/page3/?paids_year=12",
        ]
        
        def parse(self, response):
            self.logger.info(f"Обработка {response.url} в {time.time()}")
            # Минимальный парсинг для теста
            return []
    
    process = CrawlerProcess(settings={
        'DOWNLOAD_DELAY': 5,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_DELAY_RANDOMIZE_ADDITION': 2,
        'CONCURRENT_REQUESTS': 1,
        'LOG_LEVEL': 'INFO',
        'FEED_FORMAT': 'json',
        'FEED_URI': 'test_delays.json',
    })
    
    start_time = time.time()
    process.crawl(TestSpider)
    process.start()
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Общее время выполнения: {total_time:.2f} секунд")
    print(f"Ожидаемое минимальное время: {5 * 3} секунд")
```

### Ожидаемые результаты теста
- Между запросами должно быть не менее 5 секунд
- Общее время выполнения ≥ 15 секунд для 3 страниц
- В логах не должно быть предупреждений о нарушении задержек

## Оптимизация для production

### 1. Динамическая адаптация задержек
```python
class AdaptiveDelayMiddleware:
    """Адаптация задержек на основе ответов сервера"""
    
    def process_response(self, request, response, spider):
        # Увеличение задержки при получении 429 (Too Many Requests)
        if response.status == 429:
            spider.logger.warning("Получен статус 429, увеличиваю задержку")
            spider.settings.set('DOWNLOAD_DELAY', 
                               spider.settings.get('DOWNLOAD_DELAY', 5) * 2)
        
        # Уменьшение задержки при стабильной работе
        elif response.status == 200:
            current_delay = spider.settings.get('DOWNLOAD_DELAY', 5)
            if current_delay > 5:
                spider.settings.set('DOWNLOAD_DELAY', max(5, current_delay * 0.9))
        
        return response
```

### 2. Распределение запросов во времени
```python
import random
from datetime import datetime, time

class TimeBasedDelayMiddleware:
    """Различные задержки в зависимости от времени суток"""
    
    def process_request(self, request, spider):
        now = datetime.now().time()
        
        # Ночью можно увеличить задержку (меньше нагрузки на сервер)
        if time(0, 0) <= now <= time(6, 0):
            additional_delay = random.uniform(2, 5)
            time.sleep(additional_delay)
            spider.logger.debug(f"Ночная задержка: +{additional_delay:.2f}с")
        
        # В рабочее время - стандартные задержки
        elif time(9, 0) <= now <= time(18, 0):
            additional_delay = random.uniform(0, 1)
            time.sleep(additional_delay)
            spider.logger.debug(f"Рабочая задержка: +{additional_delay:.2f}с")
```

## Проблемы и решения

### Проблема 1: Накопление задержек при ошибках
**Решение**: Сброс таймера при ошибках
```python
def process_exception(self, request, exception, spider):
    # При ошибке сбрасываем время последнего запроса
    if hasattr(self, 'last_request_time'):
        self.last_request_time = 0
```

### Проблема 2: Параллельные запросы нарушают задержки
**Решение**: Установка `CONCURRENT_REQUESTS = 1`

### Проблема 3: Точность системного времени
**Решение**: Использование `time.monotonic()` вместо `time.time()`

## Итоговая проверочная таблица

| Параметр | Требование | Реализация | Проверка |
|----------|------------|------------|----------|
| Минимальная задержка | ≥5 секунд | `DOWNLOAD_DELAY = 5` | Мониторинг в DelayMonitor |
| Случайная составляющая | Для имитации пользователя | `RANDOMIZE_DOWNLOAD_DELAY = True` | Логирование фактических задержек |
| Параллельные запросы | Не более 1 | `CONCURRENT_REQUESTS = 1` | Проверка в логах Scrapy |
| Обработка ошибок | Не нарушать задержки | Сброс таймера при ошибках | Тестирование с имитацией ошибок |
| Мониторинг | Логирование задержек | DelayMonitor | Статистика по завершении |

## Рекомендации для реализации

1. **Начните с базовых настроек** (`DOWNLOAD_DELAY = 5`)
2. **Добавьте middleware** для точного контроля
3. **Реализуйте мониторинг** для проверки соблюдения
4. **Протестируйте** на небольшом количестве страниц
5. **Настройте AutoThrottle** для адаптации к ответам сервера

Следуя этому плану, вы гарантируете соблюдение требования о минимальной задержке 5 секунд между запросами и создадите парсер, который имитирует поведение реального пользователя.