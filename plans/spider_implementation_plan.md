# План реализации Spider для парсинга облигаций

## Класс SmartLabBondsSpider

### Основные характеристики
- Наследуется от `scrapy.Spider`
- Асинхронная реализация всех методов
- Соответствие принципам ООП
- Обработка ошибок на уровне запросов

### Структура класса

```python
import scrapy
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin
from bonds_parser.items import BondItem


class SmartLabBondsSpider(scrapy.Spider):
    """Spider для парсинга корпоративных облигаций с smart-lab.ru"""
    
    name = "smartlab_bonds"
    allowed_domains = ["smart-lab.ru"]
    
    # Начальный URL с параметрами
    start_urls = [
        "https://smart-lab.ru/q/bonds/order_by_coupon_value/desc/page1/?paids_year=12"
    ]
    
    # Настройки spider
    custom_settings = {
        'DOWNLOAD_DELAY': 5,  # Минимальная задержка 5 секунд
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # Случайная добавка к задержке
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # Один запрос за раз
        'AUTOTHROTTLE_ENABLED': True,  # Автоматическое регулирование скорости
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, *args, **kwargs):
        """Инициализация spider с дополнительными параметрами"""
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.processed_pages = 0
        self.total_bonds = 0
        
    async def parse(self, response):
        """
        Основной метод парсинга страницы.
        
        Args:
            response: Объект Response от Scrapy
            
        Yields:
            BondItem: Данные облигаций
            Request: Запрос на следующую страницу
        """
        self.processed_pages += 1
        self.logger.info(f"Обработка страницы {self.processed_pages}: {response.url}")
        
        # Парсинг таблицы облигаций
        bonds = await self.parse_bonds_table(response)
        
        # Возврат данных облигаций
        for bond_data in bonds:
            self.total_bonds += 1
            yield BondItem(**bond_data)
        
        # Поиск следующей страницы
        next_page_url = await self.get_next_page_url(response)
        if next_page_url:
            self.logger.info(f"Найдена следующая страница: {next_page_url}")
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
                errback=self.handle_error,
                meta={'page_number': self.processed_pages + 1}
            )
        else:
            self.logger.info(f"Парсинг завершен. Обработано страниц: {self.processed_pages}, облигаций: {self.total_bonds}")
    
    async def parse_bonds_table(self, response) -> List[Dict[str, Any]]:
        """
        Парсинг таблицы с облигациями.
        
        Args:
            response: Объект Response
            
        Returns:
            Список словарей с данными облигаций
        """
        bonds = []
        
        # Поиск таблицы облигаций
        table = response.css('table.simple-little-table.bonds')
        if not table:
            table = response.css('table.bonds')
        
        if not table:
            self.logger.warning(f"Таблица облигаций не найдена на странице {response.url}")
            return bonds
        
        # Извлечение строк таблицы (исключая заголовок)
        rows = table.css('tbody tr')
        
        for row in rows:
            bond_data = await self.parse_bond_row(row)
            if bond_data:
                bonds.append(bond_data)
        
        self.logger.info(f"На странице найдено {len(bonds)} облигаций")
        return bonds
    
    async def parse_bond_row(self, row) -> Dict[str, Any]:
        """
        Парсинг строки с данными облигации.
        
        Args:
            row: Selector строки таблицы
            
        Returns:
            Словарь с данными облигации или None при ошибке
        """
        try:
            # Извлечение всех ячеек строки
            cells = row.css('td')
            
            # Проверка наличия достаточного количества ячеек
            if len(cells) < 15:
                self.logger.warning(f"Строка содержит только {len(cells)} ячеек, ожидается минимум 15")
                return None
            
            # Извлечение данных из первых 15 ячеек (игнорируем последние 2)
            bond_data = {
                'number': await self.clean_text(cells[0]),
                'name': await self.clean_text(cells[1]),
                'years_to_maturity': await self.clean_text(cells[2]),
                'yield_value': await self.clean_text(cells[3]),
                'coupon': await self.clean_text(cells[4]),
                'price': await self.clean_text(cells[5]),
                'change': await self.clean_text(cells[6]),
                'volume': await self.clean_text(cells[7]),
                'maturity_date': await self.clean_text(cells[8]),
                'offer_date': await self.clean_text(cells[9]),
                'nkd': await self.clean_text(cells[10]),
                'duration': await self.clean_text(cells[11]),
                'payments_per_year': await self.clean_text(cells[12]),
                'bond_type': await self.clean_text(cells[13]),
                'issuer': await self.clean_text(cells[14]),
            }
            
            # Дополнительная обработка имени (извлечение из ссылки если есть)
            name_link = cells[1].css('a::text').get()
            if name_link:
                bond_data['name'] = await self.clean_text(name_link)
            
            return bond_data
            
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге строки облигации: {e}")
            return None
    
    async def get_next_page_url(self, response) -> str:
        """
        Поиск URL следующей страницы.
        
        Args:
            response: Объект Response
            
        Returns:
            URL следующей страницы или пустая строка
        """
        # Поиск пагинации
        pagination = response.css('.pagination')
        
        if pagination:
            # Поиск ссылки на следующую страницу
            next_link = pagination.css('a.next::attr(href)').get()
            if next_link:
                return urljoin(response.url, next_link)
            
            # Альтернативный поиск: следующая числовая страница
            current_page = self.extract_page_number(response.url)
            next_page_num = current_page + 1
            next_page_url = response.url.replace(f'page{current_page}', f'page{next_page_num}')
            
            # Проверка существования страницы (можно сделать запрос HEAD, но для простоты вернем URL)
            return next_page_url
        
        return ""
    
    async def clean_text(self, text_or_selector) -> str:
        """
        Очистка текста от лишних пробелов и символов.
        
        Args:
            text_or_selector: Текст или Selector объект
            
        Returns:
            Очищенный текст
        """
        if hasattr(text_or_selector, 'get'):
            text = text_or_selector.get('', '')
        else:
            text = str(text_or_selector)
        
        # Очистка текста
        text = text.strip()
        text = ' '.join(text.split())  # Удаление лишних пробелов
        
        return text
    
    def extract_page_number(self, url: str) -> int:
        """
        Извлечение номера страницы из URL.
        
        Args:
            url: URL страницы
            
        Returns:
            Номер страницы или 1 по умолчанию
        """
        import re
        match = re.search(r'/page(\d+)/', url)
        if match:
            return int(match.group(1))
        return 1
    
    async def handle_error(self, failure):
        """
        Обработка ошибок при запросах.
        
        Args:
            failure: Объект Failure с информацией об ошибке
        """
        self.logger.error(f"Ошибка при запросе: {failure.value}")
        
        # Можно добавить логику повторных попыток, но по требованиям не требуется
        if failure.check(scrapy.exceptions.TimeoutError):
            self.logger.warning("Таймаут соединения")
        elif failure.check(scrapy.exceptions.TCPTimedOutError):
            self.logger.warning("Таймаут TCP соединения")
        else:
            self.logger.warning(f"Другая ошибка: {failure.getErrorMessage()}")
```

## Item класс для облигаций

### Файл items.py
```python
import scrapy


class BondItem(scrapy.Item):
    """Item для хранения данных облигации"""
    
    # Основные поля (соответствуют столбцам таблицы)
    number = scrapy.Field()               # №
    name = scrapy.Field()                 # Имя
    years_to_maturity = scrapy.Field()    # Лет до погаш.
    yield_value = scrapy.Field()          # Доходн
    coupon = scrapy.Field()               # Купон
    price = scrapy.Field()                # Цена
    change = scrapy.Field()               # Изменение
    volume = scrapy.Field()               # Объем
    maturity_date = scrapy.Field()        # Дата погаш.
    offer_date = scrapy.Field()           # Оферта
    nkd = scrapy.Field()                  # НКД
    duration = scrapy.Field()             # Дюрация
    payments_per_year = scrapy.Field()    # Выплаты в год
    bond_type = scrapy.Field()            # Тип
    issuer = scrapy.Field()               # Эмитент
    
    # Метод для преобразования в словарь
    def to_dict(self):
        return {key: self.get(key) for key in self.fields.keys()}
```

## Middleware для имитации пользователя

### Файл middlewares.py
```python
import random
import logging
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class RandomUserAgentMiddleware(UserAgentMiddleware):
    """Middleware для ротации User-Agent"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
    ]
    
    def process_request(self, request, spider):
        user_agent = random.choice(self.USER_AGENTS)
        request.headers['User-Agent'] = user_agent
        spider.logger.debug(f"Установлен User-Agent: {user_agent}")


class DelayMiddleware:
    """Middleware для добавления случайных задержек"""
    
    def __init__(self, delay):
        self.delay = delay
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.settings.getfloat('DOWNLOAD_DELAY', 5)
        return cls(delay)
    
    def process_request(self, request, spider):
        # Добавление случайной задержки от 0 до 2 секунд
        import asyncio
        import time
        extra_delay = random.uniform(0, 2)
        time.sleep(extra_delay)
        spider.logger.debug(f"Добавлена задержка: {extra_delay:.2f} секунд")
```

## Pipeline для экспорта в CSV

### Файл pipelines.py
```python
import csv
import os
from scrapy.exporters import CsvItemExporter


class BondsCsvPipeline:
    """Pipeline для сохранения облигаций в CSV файл"""
    
    def __init__(self):
        self.file = None
        self.exporter = None
        self.is_header_written = False
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls()
    
    def open_spider(self, spider):
        """Открытие файла при старте spider"""
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, 'bonds_output.csv')
        self.file = open(file_path, 'w', newline='', encoding='utf-8')
        
        # Создание экспортера с настройками
        self.exporter = CsvItemExporter(
            self.file,
            include_headers_line=True,
            encoding='utf-8',
            fields_to_export=[
                'number', 'name', 'years_to_maturity', 'yield_value',
                'coupon', 'price', 'change', 'volume', 'maturity_date',
                'offer_date', 'nkd', 'duration', 'payments_per_year',
                'bond_type', 'issuer'
            ]
        )
        
        self.exporter.start_exporting()
        spider.logger.info(f"Начат экспорт в файл: {file_path}")
    
    def process_item(self, item, spider):
        """Обработка каждого item"""
        if not self.is_header_written:
            # Заголовок будет записан автоматически экспортером
            self.is_header_written = True
        
        self.exporter.export_item(item)
        return item
    
    def close_spider(self, spider):
        """Закрытие файла при завершении spider"""
        if self.exporter:
            self.exporter.finish_exporting()
        if self.file:
            self.file.close()
            spider.logger.info("Экспорт в CSV завершен")
```

## Настройки проекта

### Файл settings.py
```python
BOT_NAME = 'bonds_parser'

SPIDER_MODULES = ['bonds_parser.spiders']
NEWSPIDER_MODULE = 'bonds_parser.spiders'

# Настройки для имитации пользователя
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False  # На некоторых сайтах нужно отключить

# Настройка задержек (минимальная 5 секунд)
DOWNLOAD_DELAY = 5
RANDOMIZE_DOWNLOAD_DELAY = True

# Конкурентные запросы
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Настройки кэширования (для отладки)
HTTPCACHE_ENABLED = False

# Middleware
DOWNLOADER_MIDDLEWARES = {
    'bonds_parser.middlewares.RandomUserAgentMiddleware': 400,
    'bonds_parser.middlewares.DelayMiddleware': 543,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# Item pipelines
ITEM_PIPELINES = {
    'bonds_parser.pipelines.BondsCsvPipeline': 300,
}

# Настройки логирования
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Настройки экспорта
FEED_EXPORT_ENCODING = 'utf-8'
```

## План тестирования

### 1. Модульные тесты
- Тестирование парсинга строки облигации
- Тестирование извлечения URL следующей страницы
- Тестирование очистки текста

### 2. Интеграционные тесты
- Запуск spider на 1-2 страницах
- Проверка корректности CSV файла
- Проверка соблюдения задержек

### 3. Полное тестирование
- Запуск на всех страницах
- Проверка обработки ошибок
- Проверка потребления памяти

## Следующие шаги
1. Создать структуру проекта Scrapy
2. Реализовать классы Item, Spider, Middleware, Pipeline
3. Настроить settings.py
4. Протестировать на ограниченном количестве страниц
5. Оптимизировать производительность