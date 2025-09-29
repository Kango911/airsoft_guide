from .base_parser import BaseParser
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import re

logger = logging.getLogger(__name__)


class StrikePlanetParser(BaseParser):
    def __init__(self):
        super().__init__("StrikePlanet")
        self.base_url = "https://strikeplanet.ru"
        self.catalog_url = "https://strikeplanet.ru/catalog/raskhodniki/straykbolnye-shary/"
        self.page_param = "?PAGEN_1="

    def parse_products(self) -> List[Dict]:
        """Парсинг всех товаров с пагинацией"""
        all_products = []
        page = 1

        while True:
            url = f"{self.catalog_url}{self.page_param}{page}" if page > 1 else self.catalog_url
            logger.info(f"Парсинг страницы {page}: {url}")

            html = self.get_page(url)
            if not html:
                logger.error(f"Не удалось загрузить страницу {page}")
                break

            products = self.parse_page(html)
            if not products:
                logger.info(f"На странице {page} товары не найдены, завершаем парсинг")
                break

            all_products.extend(products)
            logger.info(f"Страница {page}: найдено {len(products)} товаров")

            # Проверяем есть ли следующая страница
            if not self.has_next_page(html):
                break

            page += 1

        logger.info(f"Всего найдено товаров: {len(all_products)}")
        return all_products

    def parse_page(self, html: str) -> List[Dict]:
        """Парсинг одной страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Ищем контейнеры с товарами (селекторы могут потребовать настройки)
        product_selectors = [
            '.catalog-item',  # Возможный селектор
            '.product-card',
            '.item',
            '.goods-item'
        ]

        product_containers = None
        for selector in product_selectors:
            product_containers = soup.select(selector)
            if product_containers:
                logger.info(f"Найден селектор товаров: {selector}")
                break

        if not product_containers:
            logger.warning("Не найден селектор для товаров")
            # Альтернативный поиск по структуре
            product_containers = soup.find_all('div', class_=lambda x: x and 'item' in x.lower())

        for container in product_containers:
            try:
                product = self.parse_product_container(container)
                if product and self.validate_product(product):
                    products.append(product)
            except Exception as e:
                logger.error(f"Ошибка парсинга товара: {e}")
                continue

        return products

    def parse_product_container(self, container) -> Dict:
        """Парсинг отдельного товара"""
        # Название товара
        name_selectors = [
            '.catalog-item-name a',
            '.product-name',
            '.item-title',
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
            name_elem = container.find('a', href=True)
            if name_elem:
                name = name_elem.get_text(strip=True)
                url = name_elem.get('href')
                if url and not url.startswith('http'):
                    url = urljoin(self.base_url, url)

        # Цена
        price_selectors = [
            '.catalog-item-price',
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

        # Старая цена (если есть скидка)
        old_price_selectors = [
            '.catalog-item-old-price',
            '.old-price',
            '.price-old'
        ]

        for selector in old_price_selectors:
            old_price_elem = container.select_one(selector)
            if old_price_elem:
                old_price_text = old_price_elem.get_text(strip=True)
                old_price = self.clean_price(old_price_text)
                break

        # Извлекаем дополнительную информацию из названия
        weight = self.extract_weight(name)
        package = self.extract_package(name)

        return {
            'name': name,
            'price': price,
            'old_price': old_price if old_price and old_price > price else None,
            'competitor': self.name,
            'url': url,
            'in_stock': self.check_availability(container),
            'weight': weight,
            'package': package
        }

    def check_availability(self, container) -> bool:
        """Проверка наличия товара"""
        # Ищем признаки отсутствия товара
        unavailable_indicators = [
            'нет в наличии',
            'out of stock',
            'распродано',
            'ожидается'
        ]

        container_text = container.get_text().lower()
        for indicator in unavailable_indicators:
            if indicator in container_text:
                return False

        return True

    def has_next_page(self, html: str) -> bool:
        """Проверка наличия следующей страницы"""
        soup = BeautifulSoup(html, 'html.parser')

        next_page_indicators = [
            '.pagination .next',
            '.page-nav .next',
            'a[rel="next"]'
        ]

        for selector in next_page_indicators:
            if soup.select_one(selector):
                return True

        # Проверяем номера страниц
        pagination = soup.select('.pagination a, .page-nav a')
        if pagination:
            page_numbers = []
            for page in pagination:
                try:
                    page_numbers.append(int(page.get_text()))
                except ValueError:
                    continue

            if page_numbers and max(page_numbers) > 1:
                return True

        return False