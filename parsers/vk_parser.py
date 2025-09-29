import requests
import logging
from typing import List, Dict, Optional
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class VKParser(BaseParser):
    def __init__(self, access_token: str = None):
        super().__init__("VK")
        self.access_token = access_token
        self.group_id = "-225037209"  # ID группы с минусом
        self.api_version = "5.131"

    def parse_products(self) -> List[Dict]:
        """Парсинг товаров из VK"""
        if not self.access_token:
            logger.error("Не указан access_token для VK API")
            return []

        try:
            # Получаем список товаров
            products = self.get_market_items()
            parsed_products = []

            for product in products:
                parsed_product = self.parse_vk_product(product)
                if parsed_product and self.validate_product(parsed_product):
                    parsed_products.append(parsed_product)

            logger.info(f"Получено товаров из VK: {len(parsed_products)}")
            return parsed_products

        except Exception as e:
            logger.error(f"Ошибка парсинга VK товаров: {e}")
            return []

    def get_market_items(self) -> List[Dict]:
        """Получение товаров через VK API"""
        url = "https://api.vk.com/method/market.get"
        params = {
            'owner_id': self.group_id,
            'count': 100,  # Максимальное количество
            'extended': 1,  # Получить дополнительную информацию
            'access_token': self.access_token,
            'v': self.api_version
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        if 'error' in data:
            error_msg = data['error'].get('error_msg', 'Unknown VK API error')
            raise Exception(f"VK API error: {error_msg}")

        return data.get('response', {}).get('items', [])

    def parse_vk_product(self, vk_product: Dict) -> Optional[Dict]:
        """Парсинг одного товара VK"""
        try:
            name = vk_product.get('title', '').strip()
            description = vk_product.get('description', '').strip()

            # Цена
            price_info = vk_product.get('price', {})
            price = self.clean_price(str(price_info.get('amount', 0) / 100))  # Цена в копейках

            old_price_info = vk_product.get('old_price', {})
            old_price = None
            if old_price_info:
                old_price = self.clean_price(str(old_price_info.get('amount', 0) / 100))

            # URL товара
            vk_url = f"https://vk.com/market{self.group_id}?w=product{self.group_id}_{vk_product['id']}"

            # URL фото
            photo_url = None
            if vk_product.get('thumb_photo'):
                photo_url = self.get_best_photo_url(vk_product['thumb_photo'])

            # Дополнительная информация
            weight = self.extract_weight(name)
            package = self.extract_package(name)

            # Проверяем наличие
            in_stock = vk_product.get('availability', 1) != 0  # 0 - нет в наличии

            return {
                'name': name,
                'price': price,
                'old_price': old_price if old_price and old_price > price else None,
                'vk_url': vk_url,
                'vk_photo_url': photo_url,
                'description': description,
                'in_stock': in_stock,
                'weight': weight,
                'package': package,
                'vk_product_id': vk_product['id']
            }

        except Exception as e:
            logger.error(f"Ошибка парсинга товара VK: {e}")
            return None

    def get_best_photo_url(self, photo_id: str) -> str:
        """Получение URL лучшего качества фото"""
        # VK API для получения фото
        url = "https://api.vk.com/method/photos.getById"
        params = {
            'photos': f"{self.group_id}_{photo_id}",
            'access_token': self.access_token,
            'v': self.api_version
        }

        try:
            response = self.session.get(url, params=params)
            data = response.json()

            if 'response' in data and data['response']:
                photo = data['response'][0]
                # Ищем фото максимального размера
                sizes = photo.get('sizes', [])
                if sizes:
                    # Сортируем по размеру (width * height)
                    sizes.sort(key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)
                    return sizes[0]['url']

        except Exception as e:
            logger.warning(f"Не удалось получить URL фото: {e}")

        # Возвращаем стандартный URL если не удалось получить лучший
        return f"https://sun1.userapi.com/s/v1/if1/{photo_id}.jpg"

    def set_access_token(self, token: str):
        """Установка access token"""
        self.access_token = token