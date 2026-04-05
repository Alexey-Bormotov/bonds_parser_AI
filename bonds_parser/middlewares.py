# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import random
import time
import logging
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class BondsParserSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # matching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class BondsParserDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RandomUserAgentMiddleware(UserAgentMiddleware):
    """
    Middleware для ротации User-Agent строк.
    Имитирует разные браузеры и устройства.
    """
    
    USER_AGENTS = [
        # Chrome на Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        
        # Firefox на Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        
        # Safari на Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        
        # Chrome на Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        
        # Edge на Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        
        # Mobile Chrome
        'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        
        # Mobile Safari
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    ]
    
    def __init__(self, user_agent=''):
        super().__init__(user_agent)
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('USER_AGENT'))
    
    def process_request(self, request, spider):
        # Выбор случайного User-Agent
        user_agent = random.choice(self.USER_AGENTS)
        
        # Установка User-Agent в заголовки запроса
        request.headers['User-Agent'] = user_agent
        
        # Добавление других заголовков для имитации браузера
        request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        request.headers['Accept-Language'] = 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        request.headers['Accept-Encoding'] = 'gzip, deflate, br'
        request.headers['Connection'] = 'keep-alive'
        request.headers['Upgrade-Insecure-Requests'] = '1'
        
        spider.logger.debug(f"Установлен User-Agent: {user_agent[:50]}...")
        
        return None


class DelayMiddleware:
    """
    Middleware для добавления точных задержек между запросами.
    Гарантирует минимальную задержку 5 секунд.
    """
    
    def __init__(self, delay):
        self.delay = delay
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        # Получение настроек задержки из crawler
        delay = crawler.settings.getfloat('DOWNLOAD_DELAY', 5)
        return cls(delay)
    
    def process_request(self, request, spider):
        current_time = time.time()
        
        # Расчет времени с последнего запроса
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.delay:
                # Не прошло достаточно времени, добавляем задержку
                sleep_time = self.delay - time_since_last
                
                # Добавляем небольшую случайную составляющую
                random_addition = spider.settings.getfloat('DOWNLOAD_DELAY_RANDOMIZE_ADDITION', 2)
                if random_addition > 0:
                    sleep_time += random.uniform(0, random_addition)
                
                # Применяем задержку
                if sleep_time > 0:
                    spider.logger.debug(f"Задержка запроса: {sleep_time:.2f} секунд")
                    time.sleep(sleep_time)
        
        # Обновляем время последнего запроса
        self.last_request_time = time.time()
        
        # Добавляем информацию о задержке в метаданные запроса
        request.meta['request_delay_applied'] = True
        request.meta['request_timestamp'] = self.last_request_time
        
        return None


class ErrorHandlingMiddleware:
    """
    Middleware для обработки ошибок HTTP.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls()
    
    def process_response(self, request, response, spider):
        # Обработка HTTP ошибок
        if response.status >= 400:
            spider.logger.warning(f"HTTP {response.status} при запросе: {request.url}")
            
            # Для 404 ошибки можно добавить специальную обработку
            if response.status == 404:
                spider.logger.info(f"Страница не найдена: {request.url}")
            
            # Для 429 (Too Many Requests) увеличиваем задержку
            elif response.status == 429:
                spider.logger.warning("Получен статус 429 (Too Many Requests). Увеличиваю задержку.")
                current_delay = spider.settings.get('DOWNLOAD_DELAY', 5)
                spider.settings.set('DOWNLOAD_DELAY', current_delay * 1.5)
        
        return response
    
    def process_exception(self, request, exception, spider):
        # Обработка исключений
        spider.logger.error(f"Исключение при запросе {request.url}: {exception}")
        return None
