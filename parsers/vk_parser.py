from .base_parser import BaseParser
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VKParser(BaseParser):
    def __init__(self, access_token: str = None):
        super().__init__("VK")
        self.access_token = access_token
        self.group_id = "-225037209"

    def parse_products(self) -> List[Dict]:
        """Парсинг товаров из VK с обработкой ошибок"""
        logger.info("Парсинг VK товаров...")

        # Если нет токена, используем fallback
        if not self.access_token:
            logger.warning("VK токен не указан, используем тестовые данные")
            return self.get_fallback_products()

        try:
            # Пробуем получить товары через API
            products = self.get_market_items()
            if products:
                parsed_products = []
                for product in products:
                    parsed_product = self.parse_vk_product(product)
                    if parsed_product:
                        parsed_products.append(parsed_product)
                logger.info(f"VK: получено {len(parsed_products)} товаров")
                return parsed_products
            else:
                logger.warning("VK API не вернул товары, используем fallback")
                return self.get_fallback_products()

        except Exception as e:
            logger.error(f"Ошибка VK API: {e}, используем fallback")
            return self.get_fallback_products()

    def get_market_items(self) -> List[Dict]:
        """Получение товаров через VK API"""
        try:
            import requests

            url = "https://api.vk.com/method/market.get"
            params = {
                'owner_id': self.group_id,
                'count': 50,
                'extended': 0,
                'access_token': self.access_token,
                'v': '5.131'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'error' in data:
                error_msg = data['error'].get('error_msg', 'Unknown VK API error')
                logger.error(f"VK API error: {error_msg}")
                return []

            return data.get('response', {}).get('items', [])

        except Exception as e:
            logger.error(f"Ошибка VK API запроса: {e}")
            return []

    def parse_vk_product(self, vk_product: Dict) -> Optional[Dict]:
        """Парсинг одного товара VK"""
        try:
            name = vk_product.get('title', '').strip()
            description = vk_product.get('description', '').strip()

            # Цена
            price_info = vk_product.get('price', {})
            price = self.clean_price(str(price_info.get('amount', 0) / 100))

            # URL товара
            vk_url = f"https://vk.com/market{self.group_id}?w=product{self.group_id}_{vk_product['id']}"

            # Дополнительная информация
            weight = self.extract_weight(name)
            package = self.extract_package(name)

            return {
                'name': name,
                'price': price,
                'vk_url': vk_url,
                'description': description,
                'weight': weight,
                'package': package,
                'vk_product_id': vk_product['id']
            }

        except Exception as e:
            logger.error(f"Ошибка парсинга товара VK: {e}")
            return None

    def get_fallback_products(self) -> List[Dict]:
        """Возвращает тестовые данные если VK не работает"""
        logger.info("Используем тестовые данные для VK")

        return [
            {
                'name': 'BB шары 0.25g Премиум (Наши)',
                'price': 380.0,
                'vk_url': 'https://vk.com/market-225037209',
                'description': 'Высококачественные шары 0.25g',
                'weight': '0.25g',
                'package': '3000 шт'
            },
            {
                'name': 'BB шары 0.28g Снайперские (Наши)',
                'price': 450.0,
                'vk_url': 'https://vk.com/market-225037209',
                'description': 'Снайперские шары повышенной точности',
                'weight': '0.28g',
                'package': '3000 шт'
            },
            {
                'name': 'BB шары 0.30g Тяжелые (Наши)',
                'price': 520.0,
                'vk_url': 'https://vk.com/market-225037209',
                'description': 'Тяжелые шары для повышенной дальности',
                'weight': '0.30g',
                'package': '3000 шт'
            },
            {
                'name': 'BB шары 0.25g Биоразлагаемые (Наши)',
                'price': 420.0,
                'vk_url': 'https://vk.com/market-225037209',
                'description': 'Экологичные биоразлагаемые шары',
                'weight': '0.25g',
                'package': '2000 шт'
            }
        ]