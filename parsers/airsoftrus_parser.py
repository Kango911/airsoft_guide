from .base_parser import BaseParser
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class AirsoftRusParser(BaseParser):
    def __init__(self):
        super().__init__("Airsoft-Rus")
        self.base_url = "https://airsoft-rus.ru"
        self.catalog_url = "https://airsoft-rus.ru/catalog/1096/"

    def parse_products(self) -> List[Dict]:
        """Парсинг товаров Airsoft-Rus"""
        logger.info(f"Начинаем парсинг {self.name}")

        html = self.get_page(self.catalog_url)
        if not html:
            logger.error(f"Не удалось загрузить каталог {self.catalog_url}")
            return []

        return self.parse_page(html)

    def parse_page(self, html: str) -> List[Dict]:
        """Парсинг страницы каталога"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Селекторы для Airsoft-Rus (требуют настройки)
        product_selectors = [
            '.catalog-section.items .item',
            '.products-grid .item',
            '.catalog-item',
            '.item'
        ]

        product_containers = None
        for selector in product_selectors:
            product_containers = soup.select(selector)
            if product_containers:
                logger.info(f"Найден селектор товаров: {selector}")
                break

        if not product_containers:
            logger.warning("Не найден селектор для товаров Airsoft-Rus")
            # Ищем по структуре
            product_containers = soup.find_all('div', class_=lambda x: x and 'item' in x.lower())

        logger.info(f"Найдено контейнеров товаров: {len(product_containers)}")

        for container in product_containers:
            try:
                product = self.parse_product_container(container)
                if product and self.validate_product(product):
                    products.append(product)
            except Exception as e:
                logger.error(f"Ошибка парсинга товара Airsoft-Rus: {e}")
                continue

        return products

    def parse_product_container(self, container) -> Dict:
        """Парсинг отдельного товара Airsoft-Rus"""
        # Название и URL
        name_selectors = [
            '.item-title a',
            '.name a',
            'a.name'
        ]

        name = None
        url = None

        for selector in name_selectors:
            name_elem = container.select_one(selector)
            if name_elem:
                name = name_elem.get_text(strip=True)
                url = name_elem.get('href')
                if url and not url.startswith('http'):
                    url = urljoin(self.base_url, url)
                break

        if not name:
            # Альтернативный поиск
            name_elem = container.find('a', href=True)
            if name_elem:
                name = name_elem.get_text(strip=True)
                url = name_elem.get('href')
                if url and not url.startswith('http'):
                    url = urljoin(self.base_url, url)

        # Цена
        price_selectors = [
            '.price',
            '.cost',
            '.item-price'
        ]

        price = 0
        old_price = None

        for selector in price_selectors:
            price_elem = container.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self.clean_price(price_text)
                if price > 0:
                    break

        # Старая цена
        old_price_selectors = [
            '.old-price',
            '.price-old'
        ]

        for selector in old_price_selectors:
            old_price_elem = container.select_one(selector)
            if old_price_elem:
                old_price_text = old_price_elem.get_text(strip=True)
                old_price = self.clean_price(old_price_text)
                break

        # Дополнительная информация
        weight = self.extract_weight(name) if name else None
        package = self.extract_package(name) if name else None

        # Проверка наличия
        in_stock = self.check_availability(container)

        return {
            'name': name,
            'price': price,
            'old_price': old_price if old_price and old_price > price else None,
            'competitor': self.name,
            'url': url,
            'in_stock': in_stock,
            'weight': weight,
            'package': package
        }

    def check_availability(self, container) -> bool:
        """Проверка наличия товара"""
        container_text = container.get_text().lower()

        unavailable_indicators = [
            'нет в наличии',
            'ожидается',
            'под заказ'
        ]

        available_indicators = [
            'в наличии',
            'купить',
            'добавить в корзину'
        ]

        # Если есть явные признаки отсутствия
        for indicator in unavailable_indicators:
            if indicator in container_text:
                return False

        # Если есть кнопка купить, считаем что в наличии
        buy_buttons = container.select('.buy-btn, .add-to-cart, .basket')
        if buy_buttons:
            return True

        return True  # По умолчанию считаем что в наличии