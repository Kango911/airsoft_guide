import asyncio
import logging
import sys
from datetime import datetime

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from telegram.error import TelegramError

from config import get_config
from database.models import Database
from database.operations import ProductOperations, AdminOperations
from parsers.strikeplanet_parser import StrikePlanetParser
from parsers.airsoftrus_parser import AirsoftRusParser
from parsers.vk_parser import VKParser
from handlers.admin import AdminHandler
from handlers.user import UserHandler
from utils.helpers import MessageFormatter, Scheduler

# Настройка логирования
config = get_config()
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class AirsoftBot:
    def __init__(self):
        self.config = config
        self.db = Database()
        self.product_ops = ProductOperations()
        self.admin_ops = AdminOperations()

        # Инициализация парсеров
        self.parsers = self.setup_parsers()

        # Инициализация обработчиков
        self.admin_handler = AdminHandler(self.db, self.admin_ops, self.product_ops)
        self.user_handler = UserHandler(self.db, self.product_ops)
        self.formatter = MessageFormatter()
        self.scheduler = Scheduler(self)

        # Инициализация приложения Telegram
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()

        self.setup_handlers()

    def setup_parsers(self):
        """Настройка парсеров"""
        parsers = {}

        if self.config.PARSERS_CONFIG.get('strikeplanet', {}).get('enabled', False):
            parsers['strikeplanet'] = StrikePlanetParser()

        if self.config.PARSERS_CONFIG.get('airsoftrus', {}).get('enabled', False):
            parsers['airsoftrus'] = AirsoftRusParser()

        if (self.config.PARSERS_CONFIG.get('vk', {}).get('enabled', False) and
                self.config.PARSERS_CONFIG['vk'].get('access_token')):
            parsers['vk'] = VKParser(self.config.PARSERS_CONFIG['vk']['access_token'])

        logger.info(f"✅ Инициализировано парсеров: {len(parsers)}")
        return parsers

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Команды для всех пользователей
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("prices", self.show_prices))
        self.application.add_handler(CommandHandler("products", self.show_our_products))

        # Команды для администраторов
        self.application.add_handler(CommandHandler("admin", self.admin_panel))
        self.application.add_handler(CommandHandler("update", self.update_prices))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        self.application.add_handler(CommandHandler("add_admin", self.add_admin))

        # Обработчики callback от inline клавиатур
        self.application.add_handler(CallbackQueryHandler(self.admin_handler.handle_callback, pattern="^admin_"))
        self.application.add_handler(CallbackQueryHandler(self.user_handler.handle_callback, pattern="^user_"))

        # Обработчики сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Обработчики ошибок
        self.application.add_error_handler(self.error_handler)

    async def setup_commands(self):
        """Настройка меню команд бота"""
        commands = [
            BotCommand("start", "Запустить бота"),
            BotCommand("prices", "Показать цены конкурентов"),
            BotCommand("products", "Наши товары"),
            BotCommand("help", "Помощь"),
        ]

        await self.application.bot.set_my_commands(commands)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} запустил бота")

        welcome_text = self.formatter.format_welcome_message(user.first_name)
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
🤖 *Помощь по боту*

*Команды для всех:*
/start - Запустить бота
/prices - Показать цены конкурентов  
/products - Наши товары
/help - Эта справка

*Команды для администраторов:*
/admin - Панель администратора
/update - Обновить цены вручную
/stats - Статистика
/add_admin - Добавить администратора

💡 *Для заказа:* Используйте кнопки под сообщениями с нашими товарами.
        """

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def show_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать цены конкурентов"""
        try:
            products = self.product_ops.get_all_competitor_products()

            if not products:
                await update.message.reply_text("📭 Цены конкурентов временно недоступны")
                return

            # Группируем по конкурентам
            competitors = {}
            for product in products:
                competitor = product['competitor']
                if competitor not in competitors:
                    competitors[competitor] = []
                competitors[competitor].append(product)

            # Формируем сообщения
            messages = self.formatter.format_competitor_prices(competitors)

            for message in messages:
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )

        except Exception as e:
            logger.error(f"Ошибка показа цен: {e}")
            await update.message.reply_text("❌ Ошибка при получении цен")

    async def show_our_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать наши товары"""
        try:
            products = self.product_ops.get_all_our_products()

            if not products:
                await update.message.reply_text("📭 Наши товары временно недоступны")
                return

            messages = self.formatter.format_our_products(products)

            for i, message in enumerate(messages):
                keyboard = self.user_handler.get_product_keyboard(products, i)
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )

        except Exception as e:
            logger.error(f"Ошибка показа наших товаров: {e}")
            await update.message.reply_text("❌ Ошибка при получении товаров")

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель администратора"""
        user_id = update.effective_user.id

        if not self.admin_ops.is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен.")
            return

        # Обновляем время входа
        self.admin_ops.update_admin_login(user_id)

        keyboard = await self.admin_handler.get_admin_keyboard()
        await update.message.reply_text(
            "👨‍💻 *Панель администратора*",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def update_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обновление цен вручную"""
        user_id = update.effective_user.id

        if not self.admin_ops.is_admin(user_id):
            await update.message.reply_text("❌ У вас нет прав для этой команды.")
            return

        await update.message.reply_text("🔄 Начинаю обновление цен...")

        try:
            success_count = await self.update_all_prices()

            if success_count > 0:
                # Публикуем обновление в группе
                await self.publish_price_update(context)
                await update.message.reply_text(f"✅ Цены успешно обновлены! Обработано: {success_count} товаров")
            else:
                await update.message.reply_text("⚠️ Не удалось обновить цены")

        except Exception as e:
            logger.error(f"Ошибка обновления цен: {e}")
            await update.message.reply_text("❌ Ошибка при обновлении цен")

    async def update_all_prices(self) -> int:
        """Обновление всех цен"""
        total_updated = 0

        # Парсинг StrikePlanet
        if 'strikeplanet' in self.parsers:
            try:
                products = self.parsers['strikeplanet'].parse_products()
                for product in products:
                    self.product_ops.add_competitor_product(product)
                total_updated += len(products)
                logger.info(f"StrikePlanet: обновлено {len(products)} товаров")
            except Exception as e:
                logger.error(f"Ошибка парсинга StrikePlanet: {e}")

        # Парсинг Airsoft-Rus
        if 'airsoftrus' in self.parsers:
            try:
                products = self.parsers['airsoftrus'].parse_products()
                for product in products:
                    self.product_ops.add_competitor_product(product)
                total_updated += len(products)
                logger.info(f"Airsoft-Rus: обновлено {len(products)} товаров")
            except Exception as e:
                logger.error(f"Ошибка парсинга Airsoft-Rus: {e}")

        # Парсинг VK товаров
        if 'vk' in self.parsers:
            try:
                products = self.parsers['vk'].parse_products()
                for product in products:
                    self.product_ops.add_our_product(product)
                total_updated += len(products)
                logger.info(f"VK: обновлено {len(products)} товаров")
            except Exception as e:
                logger.error(f"Ошибка парсинга VK: {e}")

        return total_updated

    async def publish_price_update(self, context: ContextTypes.DEFAULT_TYPE):
        """Публикация обновления цен в группе"""
        try:
            # Получаем последние изменения
            changes = self.product_ops.get_price_changes(1)  # За последний час

            message = self.formatter.format_price_update_message(changes)

            await context.bot.send_message(
                chat_id=self.config.GROUP_CHAT_ID,
                message_thread_id=self.config.PRICE_TOPIC_ID,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

        except Exception as e:
            logger.error(f"Ошибка публикации обновления: {e}")

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику"""
        user_id = update.effective_user.id

        if not self.admin_ops.is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен.")
            return

        try:
            stats = await self.admin_handler.get_system_stats()
            await update.message.reply_text(stats, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            await update.message.reply_text("❌ Ошибка получения статистики")

    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавление администратора"""
        user_id = update.effective_user.id

        if not self.admin_ops.is_admin(user_id):
            await update.message.reply_text("❌ Доступ запрещен.")
            return

        if not context.args:
            await update.message.reply_text("❌ Использование: /add_admin <user_id>")
            return

        try:
            new_admin_id = int(context.args[0])
            success = self.admin_ops.add_admin(
                new_admin_id,
                update.effective_user.username,
                update.effective_user.full_name
            )

            if success:
                await update.message.reply_text(f"✅ Пользователь {new_admin_id} добавлен как администратор")
            else:
                await update.message.reply_text("❌ Не удалось добавить администратора")

        except ValueError:
            await update.message.reply_text("❌ user_id должен быть числом")
        except Exception as e:
            logger.error(f"Ошибка добавления администратора: {e}")
            await update.message.reply_text("❌ Ошибка добавления администратора")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        # Здесь можно добавить обработку произвольных сообщений
        pass

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка: {context.error}", exc_info=context.error)

        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка. Попробуйте позже."
                )
        except Exception as e:
            logger.error(f"Ошибка в обработчике ошибок: {e}")

    async def on_startup(self, application):
        """Действия при запуске бота"""
        await self.setup_commands()
        await self.scheduler.start()

        # Добавляем администраторов по умолчанию из конфига
        for admin_id in self.config.ADMIN_IDS:
            existing_admin = self.admin_ops.get_admin(admin_id)
            if not existing_admin:
                self.admin_ops.add_admin(admin_id, "default_admin")
                logger.info(f"✅ Добавлен администратор по умолчанию: {admin_id}")

        logger.info("🤖 Бот запущен и готов к работе!")

    async def on_shutdown(self, application):
        """Действия при остановке бота"""
        await self.scheduler.stop()
        logger.info("🛑 Бот остановлен")

    def run(self):
        """Запуск бота"""
        # Добавляем обработчики запуска и остановки
        self.application.post_init = self.on_startup
        self.application.post_stop = self.on_shutdown

        logger.info("🚀 Запускаю бота...")

        try:
            # Запускаем бота
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            logger.info("Бот завершил работу")


if __name__ == "__main__":
    bot = AirsoftBot()
    bot.run()