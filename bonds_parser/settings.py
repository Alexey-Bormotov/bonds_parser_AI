# Scrapy settings for bonds_parser project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "bonds_parser"

SPIDER_MODULES = ["bonds_parser.spiders"]
NEWSPIDER_MODULE = "bonds_parser.spiders"

ADDONS = {}


# ===== ИМИТАЦИЯ ПОЛЬЗОВАТЕЛЯ =====

# User-Agent для имитации реального браузера
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Не соблюдать robots.txt (сайт может блокировать парсинг)
ROBOTSTXT_OBEY = False


# ===== НАСТРОЙКИ ЗАДЕРЖЕК =====

# Минимальная задержка между запросами (требование: ≥5 секунд)
DOWNLOAD_DELAY = 5

# Случайная добавка к задержке (имитация пользователя)
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_DELAY_RANDOMIZE_ADDITION = 2  # Добавляет от 0 до 2 секунд

# Автоматическое регулирование скорости
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = DOWNLOAD_DELAY
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
AUTOTHROTTLE_DEBUG = False


# ===== ПАРАЛЛЕЛЬНЫЕ ЗАПРОСЫ =====

# Ограничение параллельных запросов (для соблюдения задержек)
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
# CONCURRENT_REQUESTS_PER_IP = 1  # Не поддерживается DownloaderAwarePriorityQueue


# ===== ТАЙМАУТЫ И ПОВТОРЫ =====

# Таймаут загрузки
DOWNLOAD_TIMEOUT = 30

# Отключение повторных попыток (по требованиям)
RETRY_ENABLED = False

# Разрешенные HTTP коды (не прерывать выполнение при этих ошибках)
HTTPERROR_ALLOWED_CODES = [404, 429, 500, 502, 503, 504]


# ===== COOKIES И СЕССИИ =====

# Включение cookies для имитации пользователя
COOKIES_ENABLED = True

# Отключение Telnet Console
TELNETCONSOLE_ENABLED = False


# ===== ЗАГОЛОВКИ ЗАПРОСОВ =====

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


# ===== MIDDLEWARE =====

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    "bonds_parser.middlewares.BondsParserSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "bonds_parser.middlewares.RandomUserAgentMiddleware": 400,
    "bonds_parser.middlewares.DelayMiddleware": 543,
    "bonds_parser.middlewares.ErrorHandlingMiddleware": 600,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,  # Отключаем retry
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}


# ===== EXTENSIONS =====

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
    "scrapy.extensions.logstats.LogStats": None,
}


# ===== ITEM PIPELINES =====

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "bonds_parser.pipelines.BondsCsvPipeline": 300,
    "bonds_parser.pipelines.BondsParserPipeline": 800,
}


# ===== КЭШИРОВАНИЕ =====

# Включение кэширования для отладки
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 400, 404, 403, 429]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"


# ===== ЛОГИРОВАНИЕ =====

# Уровень логирования
LOG_LEVEL = 'INFO'

# Формат логов
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Сохранение логов в файл
# LOG_FILE = 'logs/bonds_parser.log'  # временно отключено для избежания ошибок
LOG_ENABLED = True
LOG_STDOUT = True


# ===== ЭКСПОРТ ДАННЫХ =====

# Кодировка экспорта
FEED_EXPORT_ENCODING = "utf-8"

# Формат экспорта по умолчанию
FEED_FORMAT = "csv"

# Поля для экспорта (порядок соответствует исходной таблице)
FEED_EXPORT_FIELDS = [
    'number',
    'name', 
    'years_to_maturity',
    'yield_value',
    'coupon',
    'price',
    'change',
    'volume',
    'maturity_date',
    'offer_date',
    'nkd',
    'duration',
    'payments_per_year',
    'bond_type',
    'issuer'
]


# ===== DEPTH LIMITS =====

# Ограничение глубины (не используется, но на всякий случай)
DEPTH_LIMIT = 0
DEPTH_PRIORITY = 0


# ===== ДРУГИЕ НАСТРОЙКИ =====

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
