import scrapy
import logging
import re
import time
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
    
    # Настройки spider (переопределяются в settings.py)
    custom_settings = {
        'DOWNLOAD_DELAY': 5,  # Минимальная задержка 5 секунд
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # Случайная добавка к задержке
        'CONCURRENT_REQUESTS': 1,  # Один запрос за раз
        'AUTOTHROTTLE_ENABLED': True,  # Автоматическое регулирование скорости
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'LOG_LEVEL': 'INFO',
        'RETRY_ENABLED': False,  # По требованиям - повторные попытки не нужны
    }
    
    def __init__(self, *args, **kwargs):
        """Инициализация spider с дополнительными параметрами"""
        super().__init__(*args, **kwargs)
        self.processed_pages = 0
        self.total_bonds = 0
        
        # Параметры ограничений
        self.max_pages = int(kwargs.get('max_pages', 0))  # 0 = без ограничений
        self.max_bonds = int(kwargs.get('max_bonds', 0))  # 0 = без ограничений
        
        self.logger.info(f"Spider инициализирован: max_pages={self.max_pages}, max_bonds={self.max_bonds}")
    
    def start_requests(self):
        """Начальные запросы с обработкой ошибок"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.handle_error,
                meta={'page_number': 1}
            )
    
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
        page_num = response.meta.get('page_number', self.processed_pages)
        
        self.logger.info(f"Обработка страницы {page_num}: {response.url}")
        
        # Валидация страницы
        if not await self.validate_page(response):
            self.logger.warning(f"Страница {page_num} не прошла валидацию")
            return
        
        # Парсинг таблицы облигаций
        bonds = await self.parse_bonds_table(response)
        self.logger.info(f"На странице найдено {len(bonds)} облигаций")
        
        # Если облигаций нет, завершаем работу
        if len(bonds) == 0:
            self.logger.warning(f"На странице {page_num} не найдено облигаций. Завершение работы.")
            return
        
        # Возврат данных облигаций
        for bond_data in bonds:
            self.total_bonds += 1
            
            # Проверка ограничения по количеству облигаций
            if self.max_bonds > 0 and self.total_bonds > self.max_bonds:
                self.logger.info(f"Достигнуто ограничение по облигациям: {self.max_bonds}")
                return
            
            yield BondItem(**bond_data)
        
        # Проверка ограничения по страницам
        if self.max_pages > 0 and self.processed_pages >= self.max_pages:
            self.logger.info(f"Достигнуто ограничение по страницам: {self.max_pages}")
            return
        
        # Поиск следующей страницы
        next_page_url = await self.get_next_page_url(response)
        if next_page_url:
            next_page_num = self.extract_page_number(next_page_url)
            self.logger.info(f"Найдена следующая страница: {next_page_url}")
            
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
                errback=self.handle_error,
                meta={'page_number': next_page_num}
            )
        else:
            self.logger.info(f"Пагинация завершена. Последняя страница: {page_num}")
    
    async def parse_bonds_table(self, response) -> List[Dict[str, Any]]:
        """
        Парсинг таблицы с облигациями.
        
        Args:
            response: Объект Response
            
        Returns:
            Список словарей с данными облигаций
        """
        bonds = []
        
        # Поиск таблицы облигаций (несколько возможных селекторов)
        table_selectors = [
            'table._hidden',
            'table.simple-little-table.bonds',
            'table.bonds',
            'table[class*="bonds"]',
            '//table[contains(@class, "bonds")]',  # XPath
            '//table[contains(@class, "_hidden")]'  # XPath
        ]
        
        table = None
        for selector in table_selectors:
            if selector.startswith('//'):
                table = response.xpath(selector)
            else:
                table = response.css(selector)
            
            if table:
                break
        
        if not table:
            self.logger.warning(f"Таблица облигаций не найдена на странице {response.url}")
            return bonds
        
        # Извлечение строк таблицы (исключая заголовок)
        rows = table.css('tbody tr')
        
        for row in rows:
            bond_data = await self.parse_bond_row(row)
            if bond_data:
                bonds.append(bond_data)
        
        return bonds
    
    async def parse_bond_row(self, row) -> Dict[str, Any]:
        """
        Парсинг строки с данными облигации (20 колонок).
        
        Args:
            row: Selector строки таблицы
            
        Returns:
            Словарь с данными облигации или None при ошибке
        """
        try:
            # Извлечение всех ячеек строки
            cells = row.css('td')
            
            # Проверка наличия достаточного количества ячеек
            # Таблица содержит 20 колонок, нам нужно все 20
            if len(cells) < 20:
                self.logger.debug(f"Строка содержит только {len(cells)} ячеек, ожидается 20")
                return None
            
            # Извлечение данных согласно порядку колонок на сайте
            bond_data = {
                'number': await self.clean_text(cells[0]),
                'name': await self.clean_text(cells[1]),
                'empty1': '',  # колонка 2 (пустая, картинка)
                'years_to_maturity': await self.clean_text(cells[3]),
                'yield_value': await self.clean_text(cells[4]),
                'coupon_year': await self.clean_text(cells[5]),
                'coupon_last': await self.clean_text(cells[6]),
                'rating': await self.clean_text(cells[7]),
                'volume': await self.clean_text(cells[8]),
                'coupon_rub': await self.clean_text(cells[9]),
                'frequency': await self.clean_text(cells[10]),
                'nkd': await self.clean_text(cells[11]),
                'duration': await self.clean_text(cells[12]),
                'price': await self.clean_text(cells[13]),
                'coupon_date': await self.clean_text(cells[14]),
                'placement': await self.clean_text(cells[15]),
                'maturity_date': await self.clean_text(cells[16]),
                'offer_date': await self.clean_text(cells[17]),
                'empty2': '',  # колонка 18 (пустая, картинка)
                'empty3': '',  # колонка 19 (пустая, картинка)
            }
            
            # Дополнительная обработка имени (извлечение из ссылки если есть)
            name_link = cells[1].css('a::text').get()
            if name_link:
                bond_data['name'] = await self.clean_text(name_link)
            
            # Очистка данных
            for key, value in bond_data.items():
                if value:
                    bond_data[key] = self.clean_value(value, key)
            
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
        current_url = response.url
        
        # Стратегия 1: Поиск ссылки "Следующая"
        next_link = response.css('.pagination a.next::attr(href)').get()
        if not next_link:
            # Альтернативные селекторы
            next_link = response.css('.pagination a:contains("Следующая")::attr(href)').get()
        
        if next_link:
            next_url = urljoin(current_url, next_link)
            self.logger.debug(f"Найдена ссылка 'Следующая': {next_url}")
            return next_url
        
        # Стратегия 2: Поиск следующей числовой страницы в пагинации
        pagination_links = response.css('.pagination a::attr(href)').getall()
        current_page = self.extract_page_number(current_url)
        
        for link in pagination_links:
            link_page = self.extract_page_number(link)
            if link_page == current_page + 1:
                next_url = urljoin(current_url, link)
                self.logger.debug(f"Найдена следующая числовая страница: {next_url}")
                return next_url
        
        # Стратегия 3: Инкрементальный перебор
        next_page_num = current_page + 1
        next_url = self.construct_page_url(next_page_num)
        
        self.logger.debug(f"Сконструирован URL следующей страницы: {next_url}")
        return next_url
    
    async def clean_text(self, text_or_selector) -> str:
        """
        Очистка текста от лишних пробелов и символов.
        
        Args:
            text_or_selector: Текст или Selector объект
            
        Returns:
            Очищенный текст
        """
        from scrapy import Selector
        if isinstance(text_or_selector, Selector):
            # Извлекаем текст из селектора
            text = text_or_selector.css('::text').get('')
        else:
            text = str(text_or_selector)
        
        # Очистка текста
        text = text.strip()
        text = ' '.join(text.split())  # Удаление лишних пробелов
        
        return text
    
    def clean_value(self, value: str, field_name: str) -> str:
        """
        Очистка значения поля в зависимости от его типа.
        
        Args:
            value: Значение для очистки
            field_name: Имя поля
            
        Returns:
            Очищенное значение
        """
        if not value:
            return value
        
        # Удаление лишних пробелов и символов
        value = value.strip()
        
        # Замена множественных пробелов на один
        value = ' '.join(value.split())
        
        # Для числовых полей можно убрать лишние символы
        numeric_fields = ['price', 'change', 'volume', 'nkd', 'duration']
        if field_name in numeric_fields:
            # Удаление нецифровых символов кроме точек, запятых, минусов и процентов
            value = re.sub(r'[^\d.,%\-\+]', '', value)
        
        return value
    
    def extract_page_number(self, url: str) -> int:
        """
        Извлечение номера страницы из URL.
        
        Args:
            url: URL страницы
            
        Returns:
            Номер страницы или 1 по умолчанию
        """
        match = re.search(r'/page(\d+)/', url)
        if match:
            return int(match.group(1))
        return 1
    
    def construct_page_url(self, page_number: int) -> str:
        """
        Конструкция URL для заданного номера страницы.
        
        Args:
            page_number: Номер страницы
            
        Returns:
            Полный URL
        """
        base_url = "https://smart-lab.ru/q/bonds/order_by_coupon_value/desc"
        return f"{base_url}/page{page_number}/?paids_year=12"
    
    async def validate_page(self, response) -> bool:
        """
        Валидация страницы перед парсингом.
        
        Returns:
            bool: True если страница валидна
        """
        # Проверка HTTP статуса
        if response.status != 200:
            self.logger.error(f"Неверный статус: {response.status}")
            return False
        
        # Проверка наличия таблицы облигаций
        table_exists = bool(
            response.css('table._hidden').get() or
            response.css('table.bonds').get() or
            response.css('table.simple-little-table.bonds').get()
        )
        
        if not table_exists:
            self.logger.warning("На странице не найдена таблица облигаций")
            return False
        
        return True
    
    async def handle_error(self, failure):
        """
        Обработка ошибок при запросах.
        
        Args:
            failure: Объект Failure с информацией об ошибке
        """
        request = failure.request
        page_num = request.meta.get('page_number', 'unknown')
        
        if failure.check(scrapy.exceptions.TimeoutError):
            self.logger.warning(f"Таймаут при запросе страницы {page_num}: {request.url}")
        elif failure.check(scrapy.exceptions.HttpError):
            response = failure.value.response
            self.logger.warning(f"HTTP ошибка {response.status} на странице {page_num}: {request.url}")
            
            # Если страница не найдена (404), завершаем пагинацию
            if response.status == 404:
                self.logger.info(f"Страница {page_num} не найдена (404). Пагинация завершена.")
        else:
            self.logger.error(f"Ошибка на странице {page_num}: {failure.getErrorMessage()}")
    
    def closed(self, reason):
        """Вызывается при завершении spider"""
        self.logger.info(f"Spider завершен: {reason}")
        self.logger.info(f"Итог: {self.processed_pages} страниц, {self.total_bonds} облигаций")
        
        # Автоматическая конвертация CSV в XLSX после завершения сбора
        try:
            from bonds_parser.utils.csv_to_xlsx import convert_csv_to_xlsx
            from pathlib import Path
            
            csv_path = Path("data/bonds_output.csv")
            if csv_path.exists():
                self.logger.info(f"Найден CSV файл: {csv_path}")
                xlsx_path = csv_path.with_suffix(".xlsx")
                convert_csv_to_xlsx(str(csv_path), str(xlsx_path))
                self.logger.info(f"Конвертация завершена: {xlsx_path}")
            else:
                self.logger.warning(f"CSV файл не найден: {csv_path}. Конвертация не выполнена.")
        except ImportError as e:
            self.logger.warning(f"Не удалось импортировать утилиту конвертации: {e}. Убедитесь, что установлен openpyxl.")
        except Exception as e:
            self.logger.error(f"Ошибка при конвертации CSV в XLSX: {e}")