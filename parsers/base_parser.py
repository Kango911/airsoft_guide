from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse  # ДОБАВЛЯЕМ ИМПОРТ
import logging

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        })
        self.timeout = 10
        self.retry_count = 2
        self.delay_between_requests = 1

    @abstractmethod
    def parse_products(self) -> List[Dict]:
        pass

    def get_page(self, url: str) -> Optional[str]:
        """Получение HTML страницы"""
        try:
            logger.info(f"Загрузка страницы: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Проверяем кодировку
            if response.encoding.lower() != 'utf-8':
                response.encoding = 'utf-8'

            logger.info(f"Страница загружена успешно")
            time.sleep(self.delay_between_requests)
            return response.text

        except Exception as e:
            logger.error(f"Ошибка загрузки {url}: {e}")
            return None

    def clean_price(self, price_text: str) -> float:
        """Очистка и преобразование цены в число"""
        if not price_text:
            return 0.0

        try:
            # Удаляем все символы кроме цифр и точки
            clean_text = re.sub(r'[^\d.]', '', str(price_text))

            # Если пусто после очистки
            if not clean_text:
                return 0.0

            return float(clean_text)

        except (ValueError, TypeError) as e:
            logger.warning(f"Ошибка преобразования цены '{price_text}': {e}")
            return 0.0

    def validate_product(self, product: Dict) -> bool:
        """Валидация данных товара"""
        if not product.get('name'):
            return False

        if product.get('price', 0) <= 0:
            return False

        return True