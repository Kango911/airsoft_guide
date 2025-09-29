import mysql.connector
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'rootroot',
            'database': 'airsoft_bot',
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        self.create_database()
        self.create_tables()
        self.insert_default_data()

    def create_database(self):
        """Создание базы данных если не существует"""
        try:
            conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password']
            )
            cursor = conn.cursor()

            # Создаем базу данных
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

            # Создаем пользователя если нужно (опционально)
            # cursor.execute("CREATE USER IF NOT EXISTS 'airsoft_user'@'localhost' IDENTIFIED BY 'password'")
            # cursor.execute(f"GRANT ALL PRIVILEGES ON {self.config['database']}.* TO 'airsoft_user'@'localhost'")
            # cursor.execute("FLUSH PRIVILEGES")

            cursor.close()
            conn.close()
            print("✅ База данных создана/проверена успешно")
        except Exception as e:
            print(f"❌ Ошибка создания базы данных: {e}")

    def create_tables(self):
        """Создание всех необходимых таблиц"""
        tables_sql = {
            'competitor_products': '''
                CREATE TABLE IF NOT EXISTS competitor_products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    price DECIMAL(10,2),
                    old_price DECIMAL(10,2) NULL,
                    competitor VARCHAR(100) NOT NULL,
                    url VARCHAR(1000),
                    in_stock BOOLEAN DEFAULT TRUE,
                    weight VARCHAR(50) NULL,
                    package VARCHAR(100) NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_competitor (competitor),
                    INDEX idx_price (price),
                    INDEX idx_updated (last_updated)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',

            'our_products': '''
                CREATE TABLE IF NOT EXISTS our_products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    price DECIMAL(10,2),
                    old_price DECIMAL(10,2) NULL,
                    vk_url VARCHAR(1000),
                    vk_photo_url VARCHAR(1000),
                    description TEXT,
                    in_stock BOOLEAN DEFAULT TRUE,
                    weight VARCHAR(50) NULL,
                    package VARCHAR(100) NULL,
                    vk_product_id INT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_price (price),
                    INDEX idx_stock (in_stock)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',

            'admins': '''
                CREATE TABLE IF NOT EXISTS admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL UNIQUE,
                    username VARCHAR(100),
                    full_name VARCHAR(200),
                    is_active BOOLEAN DEFAULT TRUE,
                    permissions JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    INDEX idx_user_id (user_id),
                    INDEX idx_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',

            'price_history': '''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    product_type ENUM('competitor', 'our') NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_product (product_id, product_type),
                    INDEX idx_date (change_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',

            'settings': '''
                CREATE TABLE IF NOT EXISTS settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_key VARCHAR(100) NOT NULL UNIQUE,
                    setting_value TEXT,
                    description VARCHAR(500),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        }

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            for table_name, sql in tables_sql.items():
                cursor.execute(sql)
                print(f"✅ Таблица {table_name} создана/проверена")

            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")

    def insert_default_data(self):
        """Вставка начальных данных"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Добавляем настройки по умолчанию
            default_settings = [
                ('price_update_interval', '3600', 'Интервал обновления цен в секундах'),
                ('max_products_per_message', '10', 'Максимальное количество товаров в одном сообщении'),
                ('notification_enabled', '1', 'Включить уведомления об изменении цен'),
                ('price_change_threshold', '10', 'Порог изменения цены для уведомления (%)'),
                ('group_chat_id', '-1001234567890', 'ID группы Telegram'),
                ('price_topic_id', '5', 'ID топика для цен'),
                ('order_topic_id', '6', 'ID топика для заказов')
            ]

            for key, value, description in default_settings:
                cursor.execute('''
                    INSERT IGNORE INTO settings (setting_key, setting_value, description)
                    VALUES (%s, %s, %s)
                ''', (key, value, description))

            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Начальные данные добавлены")
        except Exception as e:
            print(f"❌ Ошибка добавления начальных данных: {e}")

    def get_connection(self):
        """Получение соединения с базой данных"""
        return mysql.connector.connect(**self.config)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Универсальный метод выполнения запросов"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = None

            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_setting(self, key: str) -> str:
        """Получение значения настройки"""
        result = self.execute_query(
            "SELECT setting_value FROM settings WHERE setting_key = %s",
            (key,),
            fetch=True
        )
        return result[0]['setting_value'] if result else None

    def update_setting(self, key: str, value: str):
        """Обновление значения настройки"""
        self.execute_query(
            "UPDATE settings SET setting_value = %s WHERE setting_key = %s",
            (value, key)
        )