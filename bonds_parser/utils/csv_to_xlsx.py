"""
Утилита для конвертации CSV файла в формат XLSX.
Предназначена для автоматического запуска после завершения работы spider.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import Optional

from openpyxl import Workbook

logger = logging.getLogger(__name__)


def convert_csv_to_xlsx(
    csv_path: str,
    xlsx_path: Optional[str] = None,
    delimiter: str = ";",
    encoding: str = "utf-8",
) -> str:
    """
    Конвертирует CSV файл в XLSX.

    Args:
        csv_path: Путь к исходному CSV файлу
        xlsx_path: Путь для сохранения XLSX файла (если None, генерируется автоматически)
        delimiter: Разделитель в CSV (по умолчанию точка с запятой)
        encoding: Кодировка CSV файла

    Returns:
        Путь к созданному XLSX файлу

    Raises:
        FileNotFoundError: Если CSV файл не существует
        ValueError: Если CSV файл пуст или повреждён
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV файл не найден: {csv_path}")

    if xlsx_path is None:
        xlsx_path = str(csv_file.with_suffix(".xlsx"))

    logger.info(f"Конвертация CSV -> XLSX: {csv_path} -> {xlsx_path}")

    wb = Workbook()
    ws = wb.active
    ws.title = "Облигации"

    try:
        with open(csv_path, "r", encoding=encoding, newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row_idx, row in enumerate(reader):
                for col_idx, value in enumerate(row):
                    ws.cell(row=row_idx + 1, column=col_idx + 1, value=value)

        wb.save(xlsx_path)
        logger.info(f"XLSX файл успешно создан: {xlsx_path}")
        return xlsx_path
    except Exception as e:
        logger.error(f"Ошибка при конвертации CSV в XLSX: {e}")
        raise


def main():
    """Точка входа для запуска утилиты из командной строки."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Конвертирует CSV файл (разделитель ';') в XLSX"
    )
    parser.add_argument(
        "csv_path", help="Путь к CSV файлу (например, data/bonds_output.csv)"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Путь для сохранения XLSX файла (по умолчанию: тот же путь с расширением .xlsx)",
    )
    parser.add_argument(
        "-d", "--delimiter", default=";", help="Разделитель в CSV (по умолчанию ';')"
    )
    parser.add_argument(
        "-e", "--encoding", default="utf-8", help="Кодировка CSV файла"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Вывод подробных сообщений"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        convert_csv_to_xlsx(
            csv_path=args.csv_path,
            xlsx_path=args.output,
            delimiter=args.delimiter,
            encoding=args.encoding,
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Конвертация не удалась: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()