from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import logging
from database.models import Database
from database.operations import ProductOperations

logger = logging.getLogger(__name__)


class UserHandler:
    def __init__(self, db: Database, product_ops: ProductOperations):
        self.db = db
        self.product_ops = product_ops

    def get_product_keyboard(self, products: list, page: int = 0) -> InlineKeyboardMarkup:
        """Создает клавиатуру для товаров"""
        max_per_page = 5
        start_idx = page * max_per_page
        end_idx = start_idx + max_per_page

        keyboard = []

        # Кнопки товаров для текущей страницы
        for product in products[start_idx:end_idx]:
            product_name = product['name'][:30] + "..." if len(product['name']) > 30 else product['name']
            keyboard.append([
                InlineKeyboardButton(
                    f"🛒 {product_name} - {product['price']} руб.",
                    callback_data=f"user_order_{product['id']}"
                )
            ])

        # Кнопки навигации
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"user_page_{page - 1}"))

        if end_idx < len(products):
            nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"user_page_{page + 1}"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        # Кнопка заказа через менеджера
        keyboard.append([
            InlineKeyboardButton("📞 Связаться с менеджером", url="https://t.me/your_manager")
        ])

        return InlineKeyboardMarkup(keyboard)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает callback от пользовательских кнопок"""
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        try:
            if callback_data.startswith("user_order_"):
                await self.handle_product_order(query)
            elif callback_data.startswith("user_page_"):
                await self.handle_page_change(query, callback_data)

        except Exception as e:
            logger.error(f"Ошибка обработки пользовательского callback: {e}")
            await query.edit_message_text("❌ Произошла ошибка")

    async def handle_product_order(self, query):
        """Обработка заказа товара"""
        product_id = int(query.data.replace('user_order_', ''))

        # Получаем информацию о товаре
        products = self.product_ops.get_all_our_products()
        product = next((p for p in products if p['id'] == product_id), None)

        if not product:
            await query.edit_message_text("❌ Товар не найден")
            return

        order_text = (
            f"🛒 *Заказ товара*\n\n"
            f"*Товар:* {product['name']}\n"
            f"*Цена:* {product['price']} руб.\n\n"
            f"Для завершения заказа свяжитесь с менеджером:\n"
            f"👉 @your_manager\n\n"
            f"Или перейдите в топик заказов:\n"
            f"📋 https://t.me/c/airsoft_guide/6"
        )

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📞 Связаться с менеджером", url="https://t.me/your_manager"),
            InlineKeyboardButton("📋 Топик заказов", url="https://t.me/c/airsoft_guide/6")
        ]])

        await query.edit_message_text(
            order_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def handle_page_change(self, query, callback_data):
        """Обработка смены страницы"""
        page = int(callback_data.replace('user_page_', ''))

        products = self.product_ops.get_all_our_products()

        if not products:
            await query.edit_message_text("📭 Наши товары временно недоступны")
            return

        from utils.helpers import MessageFormatter
        formatter = MessageFormatter()
        messages = formatter.format_our_products(products)

        # Показываем ту же страницу что и была
        message_index = min(page, len(messages) - 1)
        message_text = messages[message_index]

        keyboard = self.get_product_keyboard(products, page)

        await query.edit_message_text(
            message_text,
            reply_markup=keyboard,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )