import mysql.connector
from datetime import datetime
from typing import List, Dict, Optional
from config import get_config


class Database:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Это будет вызвано только один раз благодаря __new__
        if not self._initialized:
            self.config = get_config().DB_CONFIG
            self._initialized = True
            # Не инициализируем базу здесь - вынесем в отдельный метод
            print("✅ Database instance created")

    def initialize(self):
        """Явная инициализация базы данных"""
        try:
            self.create_database()
            self.create_tables()
            self.insert_default_data()
            print("✅ База данных полностью инициализирована")
        except Exception as e:
            print(f"❌ Ошибка инициализации базы: {e}")
            raise

    def create_database(self):
        """Создание базы данных если не существует"""
        try:
            # Временно убираем базу из конфига для создания
            temp_config = self.config.copy()
            database_name = temp_config.pop('database')

            conn = mysql.connector.connect(**temp_config)
            cursor = conn.cursor()

            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
            conn.close()

            print("✅ База данных создана/проверена")
        except Exception as e:
            print(f"❌ Ошибка создания базы: {e}")
            raise

    def create_tables(self):
        """Создание таблиц (оптимизированная версия)"""
        tables_sql = {
            'competitor_products': '''
                CREATE TABLE IF NOT EXISTS competitor_products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    price DECIMAL(10,2),
                    competitor VARCHAR(100) NOT NULL,
                    url VARCHAR(1000),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'our_products': '''
                CREATE TABLE IF NOT EXISTS our_products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    price DECIMAL(10,2),
                    vk_url VARCHAR(1000),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'admins': '''
                CREATE TABLE IF NOT EXISTS admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL UNIQUE,
                    username VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
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
            raise

    def insert_default_data(self):
        """Только самые необходимые начальные данные"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Добавляем только критически важные настройки
            cursor.execute('''
                INSERT IGNORE INTO settings (setting_key, setting_value, description)
                VALUES 
                ('price_update_interval', '3600', 'Интервал обновления цен'),
                ('group_chat_id', %s, 'ID группы Telegram')
            ''', (self.config.get('GROUP_CHAT_ID', ''),))

            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Начальные данные добавлены")
        except Exception as e:
            print(f"⚠️ Предупреждение при добавлении начальных данных: {e}")

    def get_connection(self):
        """Получение соединения с базой данных"""
        return mysql.connector.connect(**self.config)

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