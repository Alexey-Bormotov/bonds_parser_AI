# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BondItem(scrapy.Item):
    """Item для хранения данных облигации (20 колонок, как на smart-lab.ru)"""
    
    # Поля соответствуют колонкам таблицы на сайте (включая пустые)
    number = scrapy.Field()               # 0: №
    name = scrapy.Field()                 # 1: Имя
    empty1 = scrapy.Field()               # 2: (пустая колонка 3 - картинка)
    years_to_maturity = scrapy.Field()    # 3: Лет до погаш.
    yield_value = scrapy.Field()          # 4: Доходн
    coupon_year = scrapy.Field()          # 5: Год.куп.дох.
    coupon_last = scrapy.Field()          # 6: Куп.дох.посл.
    rating = scrapy.Field()               # 7: Рейтинг
    volume = scrapy.Field()               # 8: Объем, млн руб
    coupon_rub = scrapy.Field()           # 9: Купон, руб
    frequency = scrapy.Field()            # 10: Частота, раз в год
    nkd = scrapy.Field()                  # 11: НКД, руб
    duration = scrapy.Field()             # 12: Дюр-я, лет
    price = scrapy.Field()                # 13: Цена
    coupon_date = scrapy.Field()          # 14: Дата купона
    placement = scrapy.Field()            # 15: Размещение
    maturity_date = scrapy.Field()        # 16: Погашение
    offer_date = scrapy.Field()           # 17: Оферта
    empty2 = scrapy.Field()               # 18: (пустая колонка 19 - картинка)
    empty3 = scrapy.Field()               # 19: (пустая колонка 20 - картинка)
    
    # Метод для преобразования в словарь
    def to_dict(self):
        return {key: self.get(key) for key in self.fields.keys()}
    
    # Метод для получения заголовков CSV (соответствует порядку колонок на сайте)
    @classmethod
    def get_csv_headers(cls):
        return [
            '№',
            'Имя',
            '',                            # пустая колонка 3
            'Лет до погаш.',
            'Доходн',
            'Год.куп.дох.',
            'Куп.дох.посл.',
            'Рейтинг',
            'Объем, млн руб',
            'Купон, руб',
            'Частота, раз в год',
            'НКД, руб',
            'Дюр-я, лет',
            'Цена',
            'Дата купона',
            'Размещение',
            'Погашение',
            'Оферта',
            '',                            # пустая колонка 19
            ''                             # пустая колонка 20
        ]
