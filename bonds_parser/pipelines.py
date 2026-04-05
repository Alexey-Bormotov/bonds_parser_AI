# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import csv
import os
from itemadapter import ItemAdapter
from bonds_parser.items import BondItem


class BondsCsvPipeline:
    """Pipeline для сохранения облигаций в CSV файл"""
    
    def __init__(self):
        self.file = None
        self.writer = None
        self.is_header_written = False
        self.output_dir = 'data'
        self.output_file = 'bonds_output.csv'
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls()
    
    def open_spider(self, spider):
        """Открытие файла при старте spider"""
        # Создание директории если не существует
        os.makedirs(self.output_dir, exist_ok=True)
        
        file_path = os.path.join(self.output_dir, self.output_file)
        
        # Открытие файла с кодировкой UTF-8
        self.file = open(file_path, 'w', newline='', encoding='utf-8')
        
        spider.logger.info(f"Начат экспорт в файл: {file_path}")
        
        # Инициализация writer будет выполнена при первом item
        # чтобы гарантировать правильный порядок полей
    
    def process_item(self, item, spider):
        """Обработка каждого item"""
        if not self.is_header_written:
            # Запись заголовка при первом item
            self.write_header(item)
            self.is_header_written = True
        
        # Запись данных
        self.write_row(item)
        return item
    
    def write_header(self, item):
        """Запись заголовка CSV с разделителем точка с запятой"""
        headers = BondItem.get_csv_headers()
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=headers,
            delimiter=';',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        self.writer.writeheader()
    
    def write_row(self, item):
        """Запись строки данных"""
        if not self.writer:
            return
        
        # Преобразование item в словарь, где ключи - заголовки CSV
        adapter = ItemAdapter(item)
        row_data = {}
        headers = BondItem.get_csv_headers()
        # Явный порядок полей, соответствующий порядку заголовков
        field_names = [
            'number',      # 0: №
            'name',        # 1: Имя
            'empty1',      # 2: (пустая колонка 3)
            'years_to_maturity',  # 3: Лет до погаш.
            'yield_value',        # 4: Доходн
            'coupon_year',        # 5: Год.куп.дох.
            'coupon_last',        # 6: Куп.дох.посл.
            'rating',             # 7: Рейтинг
            'volume',             # 8: Объем, млн руб
            'coupon_rub',         # 9: Купон, руб
            'frequency',          # 10: Частота, раз в год
            'nkd',                # 11: НКД, руб
            'duration',           # 12: Дюр-я, лет
            'price',              # 13: Цена
            'coupon_date',        # 14: Дата купона
            'placement',          # 15: Размещение
            'maturity_date',      # 16: Погашение
            'offer_date',         # 17: Оферта
            'empty2',             # 18: (пустая колонка 19)
            'empty3',             # 19: (пустая колонка 20)
        ]
        # Проверяем, что количество полей совпадает с количеством заголовков
        if len(field_names) != len(headers):
            raise ValueError(f"Количество полей ({len(field_names)}) не совпадает с количеством заголовков ({len(headers)})")
        
        for i, field in enumerate(field_names):
            csv_header = headers[i]
            row_data[csv_header] = adapter.get(field, '')
        
        self.writer.writerow(row_data)
    
    def close_spider(self, spider):
        """Закрытие файла при завершении spider"""
        if self.file:
            self.file.close()
            spider.logger.info(f"Экспорт в CSV завершен. Файл: {self.output_dir}/{self.output_file}")


class BondsParserPipeline:
    """Базовый pipeline для обработки items"""
    
    def process_item(self, item, spider):
        return item
