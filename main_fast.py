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

        # Инициализируем все атрибуты сразу
        self.db = None
        self.product_ops = None
        self.admin_ops = None
        self.parsers = {}
        self.initialized = False

        # Быстрая инициализация Telegram
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        self.setup_handlers()

    async def initialize_database(self):
        """Асинхронная инициализация базы данных и парсеров"""
        try:
            from database.models import Database
            from database.operations import ProductOperations, AdminOperations

            self.db = Database()
            # Инициализируем базу в отдельном потоке чтобы не блокировать
            await asyncio.get_event_loop().run_in_executor(None, self.db.initialize)

            self.product_ops = ProductOperations()
            self.admin_ops = AdminOperations()

            # Инициализируем парсеры
            self.parsers = self.setup_parsers()

            self.initialized = True
            logger.info("✅ База данных и парсеры инициализированы")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы: {e}")
            return False

    def setup_parsers(self):
        """Настройка парсеров"""
        parsers = {}

        try:
            if self.config.PARSERS_CONFIG.get('strikeplanet', {}).get('enabled', False):
                from parsers.strikeplanet_parser import StrikePlanetParser
                parsers['strikeplanet'] = StrikePlanetParser()
                logger.info("✅ Парсер StrikePlanet инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации парсера StrikePlanet: {e}")

        try:
            if self.config.PARSERS_CONFIG.get('airsoftrus', {}).get('enabled', False):
                from parsers.airsoftrus_parser import AirsoftRusParser
                parsers['airsoftrus'] = AirsoftRusParser()
                logger.info("✅ Парсер Airsoft-Rus инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации парсера Airsoft-Rus: {e}")

        try:
            vk_config = self.config.PARSERS_CONFIG.get('vk', {})
            if vk_config.get('enabled', False) and vk_config.get('access_token'):
                from parsers.vk_parser import VKParser
                parsers['vk'] = VKParser(vk_config['access_token'])
                logger.info("✅ Парсер VK инициализирован")
            elif vk_config.get('enabled', False):
                from parsers.vk_parser import VKParser
                parsers['vk'] = VKParser()  # Без токена - будет использовать fallback
                logger.info("✅ Парсер VK инициализирован (fallback режим)")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации парсера VK: {e}")

        logger.info(f"✅ Всего инициализировано парсеров: {len(parsers)}")
        return parsers

    def setup_handlers(self):
        """Базовые обработчики"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("prices", self.show_prices))
        self.application.add_handler(CommandHandler("products", self.show_our_products))
        self.application.add_handler(CommandHandler("update", self.update_prices))
        self.application.add_handler(CommandHandler("status", self.bot_status))

    async def start(self, update: Update, context):
        """Оптимизированный старт"""
        user = update.effective_user

        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Я бот для отслеживания цен на airsoft шары.\n\n"
            "✨ *Доступные команды:*\n"
            "/prices - Текущие цены\n"
            "/products - Наши товары\n"
            "/update - Обновить цены (админы)\n"
            "/status - Статус бота\n"
            "/help - Помощь\n\n"
            "⚡ Бот работает в быстром режиме!"
        )

        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def help(self, update: Update, context):
        """Быстрая справка"""
        help_text = """
🤖 *Помощь по боту*

*Основные команды:*
/start - Начать работу
/prices - Показать цены конкурентов
/products - Наши товары
/update - Обновить цены (админы)
/status - Статус бота
/help - Эта справка

*Для заказа:* Используйте кнопки под сообщениями с нашими товарами.

📞 *Для связи:* @Kango911
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def bot_status(self, update: Update, context):
        """Статус бота"""
        status_text = (
            "🤖 *Статус бота*\n\n"
            f"✅ База данных: {'Инициализирована' if self.db else 'Не готова'}\n"
            f"✅ Парсеры: {len(self.parsers)} инициализировано\n"
            f"✅ Готовность: {'Да' if self.initialized else 'Нет'}\n\n"
            f"🔄 Используйте /update для обновления цен"
        )
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def show_prices(self, update: Update, context):
        """Быстрый показ цен"""
        try:
            # Если база данных не инициализирована, пробуем инициализировать
            if not self.initialized:
                success = await self.initialize_database()
                if not success:
                    await update.message.reply_text("❌ База данных не готова")
                    return

            products = self.product_ops.get_all_competitor_products()

            if not products:
                await update.message.reply_text(
                    "📭 Цены пока не обновлены\n\n"
                    "💡 Используйте команду /update чтобы обновить цены"
                )
                return

            # Простой формат
            message = "🏷 *Цены конкурентов:*\n\n"
            for product in products[:8]:  # Ограничиваем количество
                name = product['name'][:50] + "..." if len(product['name']) > 50 else product['name']
                message += f"• {name}\n"
                message += f"  💰 {product['price']} руб. | {product['competitor']}\n\n"

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка показа цен: {e}")
            await update.message.reply_text("❌ Ошибка при загрузке цен")

    async def show_our_products(self, update: Update, context):
        """Показать наши товары"""
        try:
            if not self.initialized:
                success = await self.initialize_database()
                if not success:
                    await update.message.reply_text("❌ База данных не готова")
                    return

            products = self.product_ops.get_all_our_products()

            if not products:
                await update.message.reply_text(
                    "🛒 Наши товары пока не загружены\n\n"
                    "💡 Используйте /update для загрузки товаров из VK"
                )
                return

            message = "🛒 *Наши товары:*\n\n"
            for product in products[:10]:  # Ограничиваем количество
                name = product['name'][:50] + "..." if len(product['name']) > 50 else product['name']
                message += f"• {name}\n"
                message += f"  💰 {product['price']} руб."

                if product.get('weight'):
                    message += f" | ⚖️ {product['weight']}"
                if product.get('package'):
                    message += f" | 📦 {product['package']}"

                message += "\n\n"

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка показа наших товаров: {e}")
            await update.message.reply_text("❌ Ошибка при загрузке наших товаров")

    async def update_prices(self, update: Update, context):
        """Быстрое обновление цен"""
        user_id = update.effective_user.id

        # Простая проверка админа
        if user_id not in self.config.ADMIN_IDS:
            await update.message.reply_text("❌ Нет прав для выполнения этой команды")
            return

        # Проверяем инициализацию
        if not self.initialized:
            await update.message.reply_text("🔄 Инициализирую систему...")
            success = await self.initialize_database()
            if not success:
                await update.message.reply_text("❌ Не удалось инициализировать систему")
                return

        await update.message.reply_text("🔄 Начинаю обновление цен...")

        try:
            total_updated = 0

            # Парсинг StrikePlanet
            if 'strikeplanet' in self.parsers:
                try:
                    await update.message.reply_text("🔍 Парсинг StrikePlanet...")
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
                    await update.message.reply_text(f"❌ Ошибка StrikePlanet: {str(e)[:100]}...")

            # Парсинг Airsoft-Rus
            if 'airsoftrus' in self.parsers:
                try:
                    await update.message.reply_text("🔍 Парсинг Airsoft-Rus...")
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
                    await update.message.reply_text(f"❌ Ошибка Airsoft-Rus: {str(e)[:100]}...")

            # Парсинг VK товаров
            if 'vk' in self.parsers:
                try:
                    await update.message.reply_text("🔍 Парсинг VK товаров...")
                    products = self.parsers['vk'].parse_products()
                    if products:
                        for product in products:
                            self.product_ops.add_our_product(product)
                        vk_count = len(products)
                        logger.info(f"VK: обновлено {vk_count} товаров")
                        await update.message.reply_text(f"✅ VK: {vk_count} наших товаров")
                        # VK товары не считаем в общем счетчике конкурентов
                    else:
                        await update.message.reply_text("❌ VK: товары не найдены")
                except Exception as e:
                    logger.error(f"Ошибка парсинга VK: {e}")
                    await update.message.reply_text(f"❌ Ошибка VK: {str(e)[:100]}...")

            if total_updated > 0:
                await update.message.reply_text(f"🎉 Всего обновлено товаров конкурентов: {total_updated}")
            else:
                await update.message.reply_text(
                    "⚠️ Не удалось обновить цены конкурентов\n\n"
                    "💡 Но это нормально для первого запуска!"
                )

        except Exception as e:
            logger.error(f"Ошибка обновления: {e}")
            await update.message.reply_text(f"❌ Ошибка при обновлении: {str(e)[:100]}...")

    async def on_startup(self, application):
        """Быстрый запуск"""
        logger.info("🤖 Бот запускается...")

        # Инициализируем базу в фоновом режиме
        asyncio.create_task(self.initialize_database())

        # Быстрая настройка команд
        commands = [
            BotCommand("start", "Запустить бота"),
            BotCommand("prices", "Показать цены конкурентов"),
            BotCommand("products", "Наши товары"),
            BotCommand("status", "Статус бота"),
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