#!/usr/bin/env python3
"""
Диагностика производительности
"""

import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database():
    """Тест скорости базы данных"""
    print("🔍 Тестируем базу данных...")

    start_time = time.time()

    try:
        from database.models import Database
        db = Database()

        # Тест соединения
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()

        db_time = time.time() - start_time
        print(f"✅ Соединение с БД: {db_time:.2f} сек")
        return True

    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False


def test_config():
    """Тест конфигурации"""
    print("🔍 Тестируем конфигурацию...")

    start_time = time.time()

    try:
        from config import get_config
        config = get_config()
        config_time = time.time() - start_time

        print(f"✅ Конфигурация: {config_time:.2f} сек")
        print(f"   BOT_TOKEN: {'✅' if config.BOT_TOKEN else '❌'}")
        print(f"   GROUP_CHAT_ID: {'✅' if config.GROUP_CHAT_ID else '❌'}")
        print(f"   ADMIN_IDS: {len(config.ADMIN_IDS)}")

        return True
    except Exception as e:
        print(f"❌ Ошибка конфига: {e}")
        return False


def test_imports():
    """Тест импортов"""
    print("🔍 Тестируем импорты...")

    modules = [
        'telegram',
        'mysql.connector',
        'bs4',
        'requests'
    ]

    for module in modules:
        start_time = time.time()
        try:
            __import__(module)
            import_time = time.time() - start_time
            print(f"✅ {module}: {import_time:.2f} сек")
        except ImportError as e:
            print(f"❌ {module}: {e}")


def main():
    print("🚀 Диагностика производительности")
    print("=" * 40)

    test_imports()
    print("-" * 20)
    test_config()
    print("-" * 20)
    test_database()

    print("\n📊 Диагностика завершена")


if __name__ == "__main__":
    main()