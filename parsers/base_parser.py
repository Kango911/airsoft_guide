from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.timeout = 30
        self.retry_count = 3
        self.delay_between_requests = 2

    @abstractmethod
    def parse_products(self) -> List[Dict]:
        """Основной метод парсинга товаров"""
        pass

    def get_page(self, url: str) -> Optional[str]:
        """Получение HTML страницы с повторными попытками"""
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Загрузка страницы {url} (попытка {attempt + 1})")

                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()

                # Проверяем что получили HTML
                if 'text/html' not in response.headers.get('content-type', ''):
                    logger.warning(f"Получен не HTML контент: {response.headers.get('content-type')}")
                    return None

                logger.info(f"Страница {url} успешно загружена")
                time.sleep(self.delay_between_requests)  # Задержка между запросами
                return response.text

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при загрузке {url} (попытка {attempt + 1}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)  # Экспоненциальная задержка
                continue
            except Exception as e:
                logger.error(f"Неожиданная ошибка при загрузке {url}: {e}")
                break

        return None

    def clean_price(self, price_text: str) -> float:
        """Очистка и преобразование цены в число"""
        if not price_text:
            return 0.0

        try:
            # Удаляем все символы кроме цифр, точки и запятой
            clean_text = re.sub(r'[^\d,.]', '', price_text.strip())

            # Заменяем запятую на точку если нужно
            if ',' in clean_text and '.' in clean_text:
                # Если есть и точка и запятая, запятая вероятно разделитель тысяч
                clean_text = clean_text.replace(',', '')
            else:
                clean_text = clean_text.replace(',', '.')

            # Удаляем лишние точки (оставляем только первую)
            parts = clean_text.split('.')
            if len(parts) > 2:
                clean_text = parts[0] + '.' + ''.join(parts[1:])

            return float(clean_text) if clean_text else 0.0

        except (ValueError, TypeError) as e:
            logger.warning(f"Ошибка преобразования цены '{price_text}': {e}")
            return 0.0

    def extract_weight(self, name: str) -> str:
        """Извлечение веса из названия товара"""
        weight_patterns = [
            r'(\d+[,.]?\d*)\s*[gг]',  # 0.25g, 0.25г
            r'(\d+[,.]?\d*)\s*грамм',  # 0.25 грамм
            r'(\d+)\s*гр',  # 25 гр
        ]

        for pattern in weight_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                weight = match.group(1).replace(',', '.')
                return f"{weight}g"

        return None

    def extract_package(self, name: str) -> str:
        """Извлечение информации о упаковке"""
        package_patterns = [
            r'(\d+[,.]?\d*)\s*[pр]',  # 1000p, 1000р
            r'(\d+)\s*шт',  # 1000 шт
            r'(\d+)\s*штук',  # 1000 штук
        ]

        for pattern in package_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                count = match.group(1)
                return f"{count} шт"

        return None

    def validate_product(self, product: Dict) -> bool:
        """Валидация данных товара"""
        required_fields = ['name', 'price', 'competitor', 'url']

        for field in required_fields:
            if not product.get(field):
                logger.warning(f"Пропущен товар: отсутствует поле {field}")
                return False

        if product['price'] <= 0:
            logger.warning(f"Пропущен товар: некорректная цена {product['price']}")
            return False

        # Проверяем URL
        parsed_url = urlparse(product['url'])
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.warning(f"Пропущен товар: некорректный URL {product['url']}")
            return False

        return True