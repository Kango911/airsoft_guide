from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Database


class AdminHandler:
    def __init__(self, db: Database):
        self.db = db

    async def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM admins WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None

    async def get_admin_keyboard(self):
        """Создает клавиатуру админ-панели"""
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить цены", callback_data="update_prices")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("➕ Добавить админа", callback_data="add_admin")],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def handle_callback(self, update, context):
        """Обрабатывает callback от админ-панели"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id

        if not await self.is_admin(user_id):
            await query.edit_message_text("Доступ запрещен.")
            return

        if query.data == "update_prices":
            # Здесь можно вызвать функцию обновления цен
            await query.edit_message_text("Обновление цен...")
        elif query.data == "stats":
            await self.show_stats(query)
        elif query.data == "add_admin":
            await query.edit_message_text("Введите ID пользователя для добавления в админы:")

    async def show_stats(self, query):
        """Показывает статистику"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM competitor_products")
        comp_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM our_products")
        our_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        message = f"📊 Статистика:\n\n"
        message += f"Товаров конкурентов: {comp_count}\n"
        message += f"Наших товаров: {our_count}"

        await query.edit_message_text(message)