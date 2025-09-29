import asyncio
import logging
import sys
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Базовая настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FastBot:
    def __init__(self):
        from config import get_config
        self.config = get_config()

        # Отложенная инициализация базы данных
        self.db = None
        self.product_ops = None
        self.admin_ops = None

        # Быстрая инициализация Telegram
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        self.setup_handlers()

    async def initialize_database(self):
        """Асинхронная инициализация базы данных"""
        try:
            from database.models import Database
            from database.operations import ProductOperations, AdminOperations

            self.db = Database()
            # Инициализируем базу в отдельном потоке чтобы не блокировать
            await asyncio.get_event_loop().run_in_executor(None, self.db.initialize)

            self.product_ops = ProductOperations()
            self.admin_ops = AdminOperations()

            logger.info("✅ База данных инициализирована")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы: {e}")
            return False

    def setup_handlers(self):
        """Базовые обработчики"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("prices", self.show_prices))
        self.application.add_handler(CommandHandler("update", self.update_prices))

    async def start(self, update: Update, context):
        """Оптимизированный старт"""
        user = update.effective_user

        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Я бот для отслеживания цен на airsoft шары.\n\n"
            "✨ *Доступные команды:*\n"
            "/prices - Текущие цены\n"
            "/update - Обновить цены (админы)\n"
            "/help - Помощь\n\n"
            "⚡ Бот работает в быстром режиме!"
        )

        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def help(self, update: Update, context):
        """Быстрая справка"""
        help_text = (
            "🤖 *Помощь по боту*\n\n"
            "Основные команды:\n"
            "/start - Начать работу\n"
            "/prices - Показать цены\n"
            "/update - Обновить цены\n\n"
            "📞 Для связи: @ваш_менеджер"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def show_prices(self, update: Update, context):
        """Быстрый показ цен"""
        try:
            if self.product_ops is None:
                success = await self.initialize_database()
                if not success:
                    await update.message.reply_text("❌ База данных не готова")
                    return

            products = self.product_ops.get_all_competitor_products()

            if not products:
                await update.message.reply_text("📭 Цены пока не обновлены")
                return

            # Простой формат
            message = "🏷 *Цены конкурентов:*\n\n"
            for product in products[:8]:  # Ограничиваем количество
                message += f"• {product['name'][:50]}...\n"
                message += f"  💰 {product['price']} руб. | {product['competitor']}\n\n"

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка показа цен: {e}")
            await update.message.reply_text("❌ Ошибка при загрузке цен")

    async def update_prices(self, update: Update, context):
        """Быстрое обновление цен"""
        user_id = update.effective_user.id

        # Простая проверка админа
        if user_id not in self.config.ADMIN_IDS:
            await update.message.reply_text("❌ Нет прав")
            return

        await update.message.reply_text("🔄 Начинаю обновление...")

        try:
            total_updated = 0

            # Парсинг StrikePlanet
            if 'strikeplanet' in self.parsers:
                try:
                    products = self.parsers['strikeplanet'].parse_products()
                    if products:
                        for product in products:
                            self.product_ops.add_competitor_product(product)
                        total_updated += len(products)
                        logger.info(f"StrikePlanet: обновлено {len(products)} товаров")
                        await update.message.reply_text(f"✅ StrikePlanet: {len(products)} товаров")
                    else:
                        await update.message.reply_text("❌ StrikePlanet: товары не найдены")
                except Exception as e:
                    logger.error(f"Ошибка парсинга StrikePlanet: {e}")
                    await update.message.reply_text(f"❌ Ошибка StrikePlanet: {str(e)}")

            # Парсинг Airsoft-Rus
            if 'airsoftrus' in self.parsers:
                try:
                    products = self.parsers['airsoftrus'].parse_products()
                    if products:
                        for product in products:
                            self.product_ops.add_competitor_product(product)
                        total_updated += len(products)
                        logger.info(f"Airsoft-Rus: обновлено {len(products)} товаров")
                        await update.message.reply_text(f"✅ Airsoft-Rus: {len(products)} товаров")
                    else:
                        await update.message.reply_text("❌ Airsoft-Rus: товары не найдены")
                except Exception as e:
                    logger.error(f"Ошибка парсинга Airsoft-Rus: {e}")
                    await update.message.reply_text(f"❌ Ошибка Airsoft-Rus: {str(e)}")

            if total_updated > 0:
                await update.message.reply_text(f"🎉 Всего обновлено: {total_updated} товаров")
            else:
                await update.message.reply_text("⚠️ Не удалось обновить цены")

        except Exception as e:
            logger.error(f"Ошибка обновления: {e}")
            await update.message.reply_text(f"❌ Ошибка при обновлении: {str(e)}")

    async def on_startup(self, application):
        """Быстрый запуск"""
        logger.info("🤖 Бот запускается...")

        # Инициализируем базу в фоновом режиме
        asyncio.create_task(self.initialize_database())

        # Быстрая настройка команд
        commands = [
            BotCommand("start", "Запустить бота"),
            BotCommand("prices", "Показать цены"),
            BotCommand("help", "Помощь"),
        ]
        await application.bot.set_my_commands(commands)

        logger.info("✅ Бот готов к работе!")

    def run(self):
        """Запуск бота"""
        self.application.post_init = self.on_startup
        self.application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    bot = FastBot()
    bot.run()