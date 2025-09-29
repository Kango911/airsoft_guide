from typing import List, Dict, Optional
from .models import Database
from datetime import datetime, timedelta


class ProductOperations:
    def __init__(self):
        self.db = Database()

    def add_competitor_product(self, product_data: Dict) -> int:
        """Добавление товара конкурента"""
        query = """
            INSERT INTO competitor_products 
            (name, price, old_price, competitor, url, in_stock, weight, package)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            price = VALUES(price),
            old_price = VALUES(old_price),
            in_stock = VALUES(in_stock),
            last_updated = CURRENT_TIMESTAMP
        """

        # Сохраняем историю цены если она изменилась
        existing = self.get_competitor_product_by_url(product_data['url'])
        if existing and existing['price'] != product_data['price']:
            self.add_price_history(existing['id'], 'competitor', existing['price'])

        return self.db.execute_query(
            query,
            (
                product_data['name'],
                product_data['price'],
                product_data.get('old_price'),
                product_data['competitor'],
                product_data['url'],
                product_data.get('in_stock', True),
                product_data.get('weight'),
                product_data.get('package')
            )
        )

    def get_competitor_product_by_url(self, url: str) -> Optional[Dict]:
        """Получение товара конкурента по URL"""
        result = self.db.execute_query(
            "SELECT * FROM competitor_products WHERE url = %s",
            (url,),
            fetch=True
        )
        return result[0] if result else None

    def get_all_competitor_products(self, competitor: str = None) -> List[Dict]:
        """Получение всех товаров конкурентов"""
        if competitor:
            result = self.db.execute_query(
                "SELECT * FROM competitor_products WHERE competitor = %s ORDER BY price ASC",
                (competitor,),
                fetch=True
            )
        else:
            result = self.db.execute_query(
                "SELECT * FROM competitor_products ORDER BY competitor, price ASC",
                fetch=True
            )
        return result

    def add_our_product(self, product_data: Dict) -> int:
        """Добавление нашего товара"""
        query = """
            INSERT INTO our_products 
            (name, price, old_price, vk_url, vk_photo_url, description, in_stock, weight, package, vk_product_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            price = VALUES(price),
            old_price = VALUES(old_price),
            in_stock = VALUES(in_stock),
            updated_at = CURRENT_TIMESTAMP
        """

        existing = self.get_our_product_by_vk_id(product_data.get('vk_product_id'))
        if existing and existing['price'] != product_data['price']:
            self.add_price_history(existing['id'], 'our', existing['price'])

        return self.db.execute_query(
            query,
            (
                product_data['name'],
                product_data['price'],
                product_data.get('old_price'),
                product_data.get('vk_url'),
                product_data.get('vk_photo_url'),
                product_data.get('description'),
                product_data.get('in_stock', True),
                product_data.get('weight'),
                product_data.get('package'),
                product_data.get('vk_product_id')
            )
        )

    def get_our_product_by_vk_id(self, vk_id: int) -> Optional[Dict]:
        """Получение нашего товара по VK ID"""
        if not vk_id:
            return None

        result = self.db.execute_query(
            "SELECT * FROM our_products WHERE vk_product_id = %s",
            (vk_id,),
            fetch=True
        )
        return result[0] if result else None

    def get_all_our_products(self) -> List[Dict]:
        """Получение всех наших товаров"""
        return self.db.execute_query(
            "SELECT * FROM our_products WHERE in_stock = TRUE ORDER BY price ASC",
            fetch=True
        )

    def add_price_history(self, product_id: int, product_type: str, price: float):
        """Добавление записи в историю цен"""
        self.db.execute_query(
            "INSERT INTO price_history (product_id, product_type, price) VALUES (%s, %s, %s)",
            (product_id, product_type, price)
        )

    def get_price_changes(self, hours: int = 24) -> List[Dict]:
        """Получение изменений цен за указанный период"""
        return self.db.execute_query(
            """
            SELECT ph.*, 
                   CASE 
                       WHEN ph.product_type = 'competitor' THEN cp.name
                       ELSE op.name
                   END as product_name,
                   ph.product_type
            FROM price_history ph
            LEFT JOIN competitor_products cp ON ph.product_type = 'competitor' AND ph.product_id = cp.id
            LEFT JOIN our_products op ON ph.product_type = 'our' AND ph.product_id = op.id
            WHERE ph.change_date >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            ORDER BY ph.change_date DESC
            """,
            (hours,),
            fetch=True
        )


class AdminOperations:
    def __init__(self):
        self.db = Database()

    def add_admin(self, user_id: int, username: str = None, full_name: str = None) -> bool:
        """Добавление администратора"""
        try:
            self.db.execute_query(
                """
                INSERT INTO admins (user_id, username, full_name, permissions)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, username, full_name, '["update_prices", "add_admin", "view_stats"]')
            )
            return True
        except Exception as e:
            print(f"Ошибка добавления администратора: {e}")
            return False

    def is_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь администратором"""
        result = self.db.execute_query(
            "SELECT id FROM admins WHERE user_id = %s AND is_active = TRUE",
            (user_id,),
            fetch=True
        )
        return len(result) > 0

    def get_admin(self, user_id: int) -> Optional[Dict]:
        """Получение информации об администраторе"""
        result = self.db.execute_query(
            "SELECT * FROM admins WHERE user_id = %s",
            (user_id,),
            fetch=True
        )
        return result[0] if result else None

    def update_admin_login(self, user_id: int):
        """Обновление времени последнего входа"""
        self.db.execute_query(
            "UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user_id,)
        )

    def get_all_admins(self) -> List[Dict]:
        """Получение списка всех администраторов"""
        return self.db.execute_query(
            "SELECT * FROM admins WHERE is_active = TRUE ORDER BY created_at DESC",
            fetch=True
        )