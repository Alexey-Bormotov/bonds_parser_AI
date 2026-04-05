#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы парсера облигаций.
Запускает spider с ограничением на 2 страницы для быстрой проверки.
"""

import os
import sys
import time
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def test_parser():
    """Запуск тестового парсинга"""
    print("=" * 60)
    print("ТЕСТ ПАРСЕРА КОРПОРАТИВНЫХ ОБЛИГАЦИЙ")
    print("=" * 60)
    
    # Добавление пути к проекту
    project_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_path)
    
    # Получение настроек проекта
    settings = get_project_settings()
    
    # Настройки для тестирования
    settings.update({
        'DOWNLOAD_DELAY': 3,  # Уменьшенная задержка для тестов
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': 'logs/test_parser.log',
        'HTTPCACHE_ENABLED': False,
    })
    
    # Создание процесса
    process = CrawlerProcess(settings)
    
    print("Запуск парсера с ограничением: 2 страницы")
    print("Ожидаемая минимальная длительность: ~6 секунд")
    print("-" * 60)
    
    start_time = time.time()
    
    # Запуск spider с ограничением
    process.crawl('smartlab_bonds', max_pages=2)
    process.start()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print("-" * 60)
    print(f"Время выполнения: {execution_time:.2f} секунд")
    
    # Проверка созданных файлов
    data_dir = os.path.join(project_path, 'data')
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if csv_files:
            print(f"Созданные CSV файлы: {', '.join(csv_files)}")
            
            # Проверка содержимого первого файла
            csv_path = os.path.join(data_dir, csv_files[0])
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"Количество строк в CSV: {len(lines)}")
                    if len(lines) > 0:
                        print(f"Заголовок: {lines[0].strip()}")
                        if len(lines) > 1:
                            print(f"Первая строка данных: {lines[1].strip()}")
        else:
            print("CSV файлы не созданы")
    else:
        print("Директория data не создана")
    
    print("=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    
    # Проверка логов
    log_file = os.path.join(project_path, 'logs', 'test_parser.log')
    if os.path.exists(log_file):
        print(f"Логи сохранены в: {log_file}")
    
    return execution_time

if __name__ == '__main__':
    try:
        test_parser()
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        sys.exit(1)