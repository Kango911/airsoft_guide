from .base_parser import BaseParser
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import re
from urllib.parse import urljoin  # ДОБАВЛЯЕМ ИМПОРТ

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

        # Парсим только первую страницу для теста
        logger.info(f"Парсинг страницы: {self.catalog_url}")

        html = self.get_page(self.catalog_url)
        if not html:
            logger.error(f"Не удалось загрузить страницу")
            return []

        products = self.parse_page(html)
        all_products.extend(products)

        logger.info(f"Всего найдено товаров: {len(all_products)}")
        return all_products

    def parse_page(self, html: str) -> List[Dict]:
        """Парсинг одной страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Более гибкие селекторы для StrikePlanet
        product_selectors = [
            '.catalog-item',
            '.product-item',
            '.item',
            '.product',
            '.goods-item',
            '.catalog-section-item'
        ]

        product_containers = None
        for selector in product_selectors:
            product_containers = soup.select(selector)
            if product_containers:
                logger.info(f"Найден селектор товаров: {selector}, найдено: {len(product_containers)}")
                break

        if not product_containers:
            logger.warning("Не найден селектор для товаров, пробуем альтернативный поиск")
            # Альтернативный поиск по структуре
            product_containers = soup.find_all('div', class_=lambda x: x and any(
                word in str(x).lower() for word in ['item', 'product', 'card', 'goods']))
            logger.info(f"Альтернативный поиск: найдено {len(product_containers)} контейнеров")

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
        name = None
        url = None

        # Ищем название различными способами
        name_selectors = [
            '.catalog-item-name',
            '.product-name',
            '.item-title',
            '.name',
            'h1', 'h2', 'h3', 'h4',
            '.title'
        ]

        for selector in name_selectors:
            name_elem = container.select_one(selector)
            if name_elem:
                name = name_elem.get_text(strip=True)
                # Пробуем найти ссылку
                link_elem = name_elem.find('a') if name_elem else None
                if link_elem and link_elem.get('href'):
                    url = link_elem.get('href')
                break

        # Если не нашли через селекторы, ищем любой текст как название
        if not name:
            # Ищем первый значимый текст
            texts = container.find_all(text=True, recursive=True)
            for text in texts:
                clean_text = text.strip()
                if (len(clean_text) > 10 and
                        not clean_text.startswith('<') and
                        'function(' not in clean_text and
                        not clean_text.isspace()):
                    name = clean_text
                    break

        # Цена
        price = 0
        price_selectors = [
            '.catalog-item-price',
            '.price',
            '.cost',
            '.item-price',
            '.price_value'
        ]

        for selector in price_selectors:
            price_elem = container.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self.clean_price(price_text)
                if price > 0:
                    break

        # Если не нашли цену, ищем числа в тексте
        if price == 0:
            container_text = container.get_text()
            # Ищем цены в формате 1000 руб, 1000р, 1 000 руб и т.д.
            price_patterns = [
                r'(\d+[\s]*[рrуб]|\d+[\s]*\$|\d+[\s]*€)',  # 1000р, 1000 руб, 1000$
                r'(\d{1,3}(?:\s?\d{3})*(?:[.,]\d{2})?)\s*[рrуб]',  # 1 000 руб, 1,000.00 руб
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, container_text, re.IGNORECASE)
                if matches:
                    # Берем первое найденное число
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]  # Если группа захвата
                        clean_price = self.clean_price(match)
                        if clean_price > 0:
                            price = clean_price
                            break
                    if price > 0:
                        break

        # Формируем полный URL
        if url and not url.startswith('http'):
            url = urljoin(self.base_url, url)

        # Если нет URL, используем базовый
        if not url:
            url = self.catalog_url

        # Извлекаем дополнительную информацию
        weight = self.extract_weight(name) if name else None
        package = self.extract_package(name) if name else None

        return {
            'name': name or "Неизвестный товар",
            'price': price,
            'competitor': self.name,
            'url': url,
            'in_stock': True,  # Предполагаем что в наличии
            'weight': weight,
            'package': package
        }

    def extract_weight(self, name: str) -> str:
        """Извлечение веса из названия"""
        if not name:
            return None

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
        if not name:
            return None

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