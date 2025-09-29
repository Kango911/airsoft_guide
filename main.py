import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from database.models import Database
from key.key import TOKEN
from parsers.strikeplanet_parser import StrikePlanetParser
from parsers.airsoftrus_parser import AirsoftRusParser
from handlers.admin import AdminHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirsoftBot:
    def __init__(self, token: str):
        self.token = token
        self.db = Database()
        self.admin_handler = AdminHandler(self.db)

        # ID топиков в Telegram
        self.PRICE_TOPIC_ID = 5  # https://t.me/c/airsoft_guide/5
        self.ORDER_TOPIC_ID = 6  # https://t.me/c/airsoft_guide/6

        # ID группы (нужно заменить на реальный)
        self.GROUP_CHAT_ID = -1001234567890  # Заменить на реальный ID группы

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Привет! Я бот для мониторинга цен на airsoft шары.")

    async def update_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для обновления цен"""
        user_id = update.effective_user.id

        if not await self.admin_handler.is_admin(user_id):
            await update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        await update.message.reply_text("Начинаю обновление цен...")

        try:
            # Парсим цены конкурентов
            strike_parser = StrikePlanetParser()
            airsoft_parser = AirsoftRusParser()

            strike_products = strike_parser.parse_products()
            airsoft_products = airsoft_rus_parser.parse_products()

            # Сохраняем в базу
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Очищаем старые данные
            cursor.execute("DELETE FROM competitor_products")

            # Сохраняем новые данные
            for product in strike_products + airsoft_products:
                cursor.execute(
                    "INSERT INTO competitor_products (name, price, competitor, url) VALUES (%s, %s, %s, %s)",
                    (product['name'], product['price'], product['competitor'], product['url'])
                )

            conn.commit()
            cursor.close()
            conn.close()

            # Формируем сообщение для топика
            message = "🔄 ОБНОВЛЕНИЕ ЦЕН КОНКУРЕНТОВ\n\n"

            # Добавляем товары StrikePlanet
            message += "🎯 StrikePlanet:\n"
            for product in strike_products[:5]:  # первые 5 товаров
                message += f"• {product['name']}: {product['price']} руб.\n"

            message += "\n🎯 Airsoft-Rus:\n"
            for product in airsoft_products[:5]:  # первые 5 товаров
                message += f"• {product['name']}: {product['price']} руб.\n"

            message += f"\n📦 Наши товары: https://t.me/c/airsoft_guide/{self.ORDER_TOPIC_ID}"

            # Отправляем в топик
            await context.bot.send_message(
                chat_id=self.GROUP_CHAT_ID,
                message_thread_id=self.PRICE_TOPIC_ID,
                text=message
            )

            await update.message.reply_text("Цены успешно обновлены и опубликованы!")

        except Exception as e:
            logger.error(f"Error updating prices: {e}")
            await update.message.reply_text("Произошла ошибка при обновлении цен.")

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель администратора"""
        user_id = update.effective_user.id

        if not await self.admin_handler.is_admin(user_id):
            await update.message.reply_text("Доступ запрещен.")
            return

        keyboard = await self.admin_handler.get_admin_keyboard()
        await update.message.reply_text(
            "Панель администратора:",
            reply_markup=keyboard
        )

    def run(self):
        """Запуск бота"""
        application = Application.builder().token(self.token).build()

        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("update", self.update_prices))
        application.add_handler(CommandHandler("admin", self.admin_panel))
        application.add_handler(CallbackQueryHandler(self.admin_handler.handle_callback))

        # Запускаем бота
        application.run_polling()


if __name__ == "__main__":
    # Токен бота
    BOT_TOKEN = TOKEN

    bot = AirsoftBot(BOT_TOKEN)
    bot.run()