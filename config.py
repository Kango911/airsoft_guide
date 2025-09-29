import os
import logging
from typing import Dict, Any

try:
    from key.key import (
        BOT_TOKEN,
        DB_CONFIG,
        GROUP_CHAT_ID,
        PRICE_TOPIC_ID,
        ORDER_TOPIC_ID,
        VK_ACCESS_TOKEN,
        ADMIN_IDS,
        PARSERS_CONFIG
    )
except ImportError:
    logging.error("❌ Файл key/key.py не найден! Создайте его на основе key/example_key.py")
    raise


class Config:
    """Конфигурация бота"""

    # Токен бота
    BOT_TOKEN = BOT_TOKEN

    # Настройки базы данных
    DB_CONFIG = {
        'host': DB_CONFIG.get('host', 'localhost'),
        'user': DB_CONFIG.get('user', 'root'),
        'password': DB_CONFIG.get('password', ''),
        'database': DB_CONFIG.get('database', 'airsoft_bot'),
        'charset': 'utf8mb4'
    }

    # Настройки Telegram
    GROUP_CHAT_ID = GROUP_CHAT_ID
    PRICE_TOPIC_ID = PRICE_TOPIC_ID
    ORDER_TOPIC_ID = ORDER_TOPIC_ID

    # Настройки парсеров
    PARSERS_CONFIG = PARSERS_CONFIG.copy()
    # Добавляем VK токен в конфиг парсера
    if 'vk' in PARSERS_CONFIG:
        PARSERS_CONFIG['vk']['access_token'] = VK_ACCESS_TOKEN

    # Настройки администраторов
    ADMIN_IDS = ADMIN_IDS

    # Логирование
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Настройки сообщений
    MESSAGE_CONFIG = {
        'max_products_per_message': 10,
        'price_update_notification': True,
        'formatting': {
            'bold': '**',
            'italic': '_',
            'code': '`'
        }
    }

    @classmethod
    def validate_config(cls):
        """Валидация конфигурации"""
        errors = []

        if not cls.BOT_TOKEN or cls.BOT_TOKEN.startswith('ВАШ_') or '1234567890' in cls.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN не настроен в key/key.py")

        if not cls.DB_CONFIG.get('password'):
            errors.append("❌ Пароль базы данных не настроен в key/key.py")

        if not cls.GROUP_CHAT_ID or cls.GROUP_CHAT_ID.startswith('-1001234567890'):
            errors.append("❌ GROUP_CHAT_ID не настроен в key/key.py")

        if not cls.ADMIN_IDS or cls.ADMIN_IDS == [123456789]:
            errors.append("❌ ADMIN_IDS не настроены в key/key.py")

        if errors:
            for error in errors:
                logging.error(error)
            raise ValueError("Неверная конфигурация. Проверьте key/key.py")

        logging.info("✅ Конфигурация проверена успешно")


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    LOG_LEVEL = 'WARNING'


def get_config() -> Config:
    """Получение конфигурации в зависимости от окружения"""
    env = os.getenv('ENVIRONMENT', 'development')

    config = DevelopmentConfig() if env == 'development' else ProductionConfig()
    config.validate_config()

    return config