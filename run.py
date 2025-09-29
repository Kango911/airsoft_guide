#!/usr/bin/env python3
"""
Скрипт запуска бота
"""

import os
import logging
import sys

# Добавляем папку key в путь импорта
sys.path.append(os.path.dirname(__file__))


def main():
    """Запуск бота"""
    from main import AirsoftBot

    try:
        bot = AirsoftBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        logging.exception("Критическая ошибка")


if __name__ == "__main__":
    main()