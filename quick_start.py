#!/usr/bin/env python3
"""
Ускоренный запуск бота без глубокой инициализации
"""

import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler

# Минимальная настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuickBot:
    def __init__(self):
        from config import get_config
        self.config = get_config()

        # Быстрая инициализация приложения
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Только основные обработчики"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("prices", self.show_prices))

    async def start(self, update: Update, context):
        """Быстрая команда start"""
        await update.message.reply_text(
            "🚀 Бот запущен в быстром режиме!\n\n"
            "Используйте /prices для просмотра цен\n"
            "Используйте /help для справки"
        )

    async def help(self, update: Update, context):
        """Быстрая команда help"""
        await update.message.reply_text(
            "🤖 Быстрая справка:\n\n"
            "/start - Запустить бота\n"
            "/prices - Показать цены\n"
            "/help - Эта справка"
        )

    async def show_prices(self, update: Update, context):
        """Быстрый показ цен"""
        try:
            # Пробуем получить цены из базы
            from database.operations import ProductOperations
            product_ops = ProductOperations()
            products = product_ops.get_all_competitor_products()

            if products:
                message = "🏷 *Текущие цены конкурентов:*\n\n"
                for product in products[:5]:  # Только первые 5
                    message += f"• {product['name']}: {product['price']} руб.\n"
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text("📭 Цены пока не обновлены. Используйте /update для обновления.")

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            await update.message.reply_text("❌ Ошибка при получении цен")

    def run(self):
        """Быстрый запуск"""
        logger.info("🚀 Запускаю бота в быстром режиме...")
        self.application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    bot = QuickBot()
    bot.run()