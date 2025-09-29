#!/usr/bin/env python3
"""
Минимальная версия бота для быстрого запуска
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("ping", self.ping))

    async def start(self, update: Update, context):
        await update.message.reply_text("✅ Бот работает!")

    async def ping(self, update: Update, context):
        await update.message.reply_text("🏓 Понг!")

    def run(self):
        logger.info("🚀 Запускаю минимального бота...")
        self.application.run_polling()

if __name__ == "__main__":
    from key.key import BOT_TOKEN
    bot = MinimalBot(BOT_TOKEN)
    bot.run()