"""
Пример файла конфигурации.
Скопируйте этот файл в key.py и заполните своими данными.
"""

# Токен бота Telegram (получить у @BotFather)
BOT_TOKEN = "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"

# Настройки базы данных
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_mysql_password',
    'database': 'airsoft_bot'
}

# Настройки Telegram
GROUP_CHAT_ID = "-1001234567890"  # ID вашей группы с минусом
PRICE_TOPIC_ID = 5  # ID топика для цен
ORDER_TOPIC_ID = 6   # ID топика для заказов

# Токен VK API (для парсинга товаров из VK)
VK_ACCESS_TOKEN = "vk1.a.your_vk_token_here"

# Список администраторов (их user_id в Telegram)
ADMIN_IDS = [
    123456789,  # Замените на реальные ID администраторов
]

# Настройки парсеров
PARSERS_CONFIG = {
    'strikeplanet': {
        'enabled': True,
        'update_interval': 3600
    },
    'airsoftrus': {
        'enabled': True,
        'update_interval': 3600
    },
    'vk': {
        'enabled': True,
        'update_interval': 7200,
    }
}