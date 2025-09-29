#!/usr/bin/env python3
"""
Скрипт установки и настройки бота
"""

import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error


def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def install_requirements():
    """Установка зависимостей"""
    print("📦 Устанавливаю зависимости...")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены")
    except subprocess.CalledProcessError:
        print("❌ Ошибка установки зависимостей")
        sys.exit(1)


def setup_database():
    """Настройка базы данных"""
    print("🗄 Настраиваю базу данных...")

    try:
        # Подключаемся к MySQL
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='rootroot'
        )

        cursor = conn.cursor()

        # Создаем базу данных
        cursor.execute("CREATE DATABASE IF NOT EXISTS airsoft_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ База данных создана")

        cursor.close()
        conn.close()

    except Error as e:
        print(f"❌ Ошибка настройки базы данных: {e}")
        sys.exit(1)


def create_key_files():
    """Создание файлов в папке key"""
    key_dir = "key"
    if not os.path.exists(key_dir):
        os.makedirs(key_dir)
        print(f"✅ Создана папка {key_dir}")

    # Создаем __init__.py
    init_file = os.path.join(key_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# Пустой файл для создания пакета\n")
        print("✅ Создан key/__init__.py")

    # Создаем example_key.py если не существует
    example_file = os.path.join(key_dir, "example_key.py")
    if not os.path.exists(example_file):
        with open(example_file, 'w', encoding='utf-8') as f:
            f.write('''"""
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
''')
        print("✅ Создан key/example_key.py")

    # Создаем key.py если не существует
    key_file = os.path.join(key_dir, "key.py")
    if not os.path.exists(key_file):
        print("\n📝 Создаю файл key/key.py...")

        bot_token = input("Введите токен бота от @BotFather: ")
        group_chat_id = input("Введите ID группы Telegram (с минусом): ")
        vk_token = input("Введите токен VK API (опционально, нажмите Enter чтобы пропустить): ")
        admin_id = input("Введите ваш user_id в Telegram (можно узнать у @userinfobot): ")

        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(
                f'"""\nФайл для хранения всех чувствительных данных.\nЗАПРЕЩЕНО коммитить этот файл в git!\n"""\n\n')

            f.write(f'# Токен бота Telegram (получить у @BotFather)\n')
            f.write(f'BOT_TOKEN = "{bot_token}"\n\n')

            f.write(f'# Настройки базы данных\n')
            f.write(f'DB_CONFIG = {{\n')
            f.write(f"    'host': 'localhost',\n")
            f.write(f"    'user': 'root', \n")
            f.write(f"    'password': 'rootroot',  # Пароль от MySQL\n")
            f.write(f"    'database': 'airsoft_bot'\n")
            f.write(f'}}\n\n')

            f.write(f'# Настройки Telegram\n')
            f.write(f'GROUP_CHAT_ID = "{group_chat_id}"  # ID вашей группы с минусом\n')
            f.write(f'PRICE_TOPIC_ID = 5  # ID топика для цен\n')
            f.write(f'ORDER_TOPIC_ID = 6   # ID топика для заказов\n\n')

            if vk_token:
                f.write(f'# Токен VK API (для парсинга товаров из VK)\n')
                f.write(f'VK_ACCESS_TOKEN = "{vk_token}"\n\n')
            else:
                f.write(f'# Токен VK API (для парсинга товаров из VK)\n')
                f.write(f'VK_ACCESS_TOKEN = ""\n\n')

            f.write(f'# Список администраторов (их user_id в Telegram)\n')
            f.write(f'ADMIN_IDS = [\n')
            f.write(f'    {admin_id},  # Ваш user_id\n')
            f.write(f']\n\n')

            f.write(f'# Настройки парсеров\n')
            f.write(f'PARSERS_CONFIG = {{\n')
            f.write(f"    'strikeplanet': {{\n")
            f.write(f"        'enabled': True,\n")
            f.write(f"        'update_interval': 3600  # 1 час\n")
            f.write(f"    }},\n")
            f.write(f"    'airsoftrus': {{\n")
            f.write(f"        'enabled': True, \n")
            f.write(f"        'update_interval': 3600\n")
            f.write(f"    }},\n")
            f.write(f"    'vk': {{\n")
            f.write(f"        'enabled': True,\n")
            f.write(f"        'update_interval': 7200,  # 2 часа\n")
            f.write(f"    }}\n")
            f.write(f'}}\n')

        print("✅ Создан key/key.py")
    else:
        print("✅ Файл key/key.py уже существует")


def update_gitignore():
    """Обновление .gitignore"""
    gitignore_file = ".gitignore"
    key_entries = [
        "\n# Конфиденциальные данные\nkey/key.py\nkey/__pycache__/\n*.env\n"
    ]

    if not os.path.exists(gitignore_file):
        with open(gitignore_file, 'w') as f:
            f.writelines(key_entries)
        print("✅ Создан .gitignore")
    else:
        with open(gitignore_file, 'r') as f:
            content = f.read()

        if 'key/key.py' not in content:
            with open(gitignore_file, 'a') as f:
                f.writelines(key_entries)
            print("✅ Обновлен .gitignore")
        else:
            print("✅ .gitignore уже содержит нужные записи")


def main():
    """Основная функция установки"""
    print("🚀 Установка Airsoft Price Bot")
    print("=" * 40)

    # Проверяем версию Python
    check_python_version()

    # Устанавливаем зависимости
    install_requirements()

    # Настраиваем базу данных
    setup_database()

    # Создаем файлы в папке key
    create_key_files()

    # Обновляем .gitignore
    update_gitignore()

    print("\n🎉 Установка завершена!")
    print("\n📝 Следующие шаги:")
    print("1. Отредактируйте key/key.py если нужно изменить настройки")
    print("2. Добавьте бота в вашу группу")
    print("3. Назначьте бота администратором группы")
    print("4. Запустите бота: python run.py")
    print("5. Проверьте работу командой /start")


if __name__ == "__main__":
    main()