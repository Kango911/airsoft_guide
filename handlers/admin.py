from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import logging
from typing import Dict, List
from database.models import Database
from database.operations import AdminOperations, ProductOperations

logger = logging.getLogger(__name__)


class AdminHandler:
    def __init__(self, db: Database, admin_ops: AdminOperations, product_ops: ProductOperations):
        self.db = db
        self.admin_ops = admin_ops
        self.product_ops = product_ops

    async def get_admin_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру админ-панели"""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Обновить цены", callback_data="admin_update_prices"),
                InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("👥 Администраторы", callback_data="admin_list_admins"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")
            ],
            [
                InlineKeyboardButton("📈 История цен", callback_data="admin_price_history"),
                InlineKeyboardButton("🛠 Тех. операции", callback_data="admin_tech_ops")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает callback от админ-панели"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id

        if not self.admin_ops.is_admin(user_id):
            await query.edit_message_text("❌ Доступ запрещен.")
            return

        callback_data = query.data

        try:
            if callback_data == "admin_update_prices":
                await self.handle_update_prices(query, context)
            elif callback_data == "admin_stats":
                await self.handle_show_stats(query)
            elif callback_data == "admin_list_admins":
                await self.handle_list_admins(query)
            elif callback_data == "admin_settings":
                await self.handle_settings(query)
            elif callback_data == "admin_price_history":
                await self.handle_price_history(query)
            elif callback_data == "admin_tech_ops":
                await self.handle_tech_ops(query)
            elif callback_data.startswith("admin_setting_"):
                await self.handle_setting_change(query, callback_data)
            elif callback_data == "admin_back":
                await self.handle_back_to_main(query)

        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            await query.edit_message_text("❌ Произошла ошибка")

    async def handle_update_prices(self, query, context):
        """Обработка обновления цен"""
        await query.edit_message_text("🔄 Начинаю обновление цен...")

        try:
            # Создаем временное сообщение о прогрессе
            progress_message = await query.message.reply_text("⏳ Парсинг сайтов...")

            # Обновляем цены
            from main import AirsoftBot  # Импортируем здесь чтобы избежать циклического импорта
            bot = context.application
            success_count = await bot.update_all_prices()

            await progress_message.edit_text(f"✅ Обновление завершено!\nОбработано товаров: {success_count}")

            # Публикуем в группе
            await bot.publish_price_update(context)

            # Возвращаемся в главное меню
            keyboard = await self.get_admin_keyboard()
            await query.edit_message_text(
                "👨‍💻 *Панель администратора*\n\n"
                f"✅ Цены успешно обновлены!\n"
                f"📊 Обработано товаров: {success_count}",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Ошибка обновления цен: {e}")
            await query.edit_message_text("❌ Ошибка при обновлении цен")

    async def handle_show_stats(self, query):
        """Показ статистики"""
        stats_text = await self.get_system_stats()

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
        ]])

        await query.edit_message_text(stats_text, reply_markup=keyboard, parse_mode='Markdown')

    async def get_system_stats(self) -> str:
        """Получение системной статистики"""
        try:
            # Статистика товаров
            comp_products = self.product_ops.get_all_competitor_products()
            our_products = self.product_ops.get_all_our_products()

            # Статистика по конкурентам
            competitors = {}
            for product in comp_products:
                competitor = product['competitor']
                if competitor not in competitors:
                    competitors[competitor] = 0
                competitors[competitor] += 1

            # Администраторы
            admins = self.admin_ops.get_all_admins()

            # История цен
            recent_changes = self.product_ops.get_price_changes(24)  # За 24 часа

            stats_text = "📊 *Системная статистика*\n\n"
            stats_text += f"*Наши товары:* {len(our_products)} шт.\n"

            for competitor, count in competitors.items():
                stats_text += f"*{competitor}:* {count} шт.\n"

            stats_text += f"\n*Администраторов:* {len(admins)}\n"
            stats_text += f"*Изменений цен за 24ч:* {len(recent_changes)}\n"

            # Средние цены
            if comp_products:
                avg_price = sum(p['price'] for p in comp_products if p['price']) / len(comp_products)
                stats_text += f"*Средняя цена конкурентов:* {avg_price:.2f} руб.\n"

            if our_products:
                our_avg_price = sum(p['price'] for p in our_products if p['price']) / len(our_products)
                stats_text += f"*Наша средняя цена:* {our_avg_price:.2f} руб.\n"

            return stats_text

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return "❌ Ошибка получения статистики"

    async def handle_list_admins(self, query):
        """Список администраторов"""
        admins = self.admin_ops.get_all_admins()

        if not admins:
            text = "👥 *Администраторы*\n\nСписок администраторов пуст."
        else:
            text = "👥 *Администраторы*\n\n"
            for admin in admins:
                last_login = admin['last_login'].strftime('%d.%m.%Y %H:%M') if admin['last_login'] else 'Никогда'
                text += f"• ID: {admin['user_id']}\n"
                text += f"  Имя: {admin['full_name'] or 'Не указано'}\n"
                text += f"  Последний вход: {last_login}\n\n"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
        ]])

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def handle_settings(self, query):
        """Настройки бота"""
        settings = [
            ('price_update_interval', 'Интервал обновления цен (сек)'),
            ('max_products_per_message', 'Товаров в сообщении'),
            ('notification_enabled', 'Уведомления о ценах'),
        ]

        text = "⚙️ *Настройки бота*\n\n"
        for key, description in settings:
            value = self.db.get_setting(key)
            text += f"{description}: `{value}`\n"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Интервал обновления", callback_data="admin_setting_interval")
        ], [
            InlineKeyboardButton("📝 Товаров в сообщении", callback_data="admin_setting_max_products")
        ], [
            InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
        ]])

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def handle_setting_change(self, query, callback_data):
        """Изменение настроек"""
        setting_key = callback_data.replace('admin_setting_', '')

        setting_names = {
            'interval': 'price_update_interval',
            'max_products': 'max_products_per_message'
        }

        actual_key = setting_names.get(setting_key)
        if not actual_key:
            await query.edit_message_text("❌ Неизвестная настройка")
            return

        current_value = self.db.get_setting(actual_key)

        await query.edit_message_text(
            f"⚙️ Изменение настройки\n\n"
            f"Текущее значение: `{current_value}`\n"
            f"Отправьте новое значение:",
            parse_mode='Markdown'
        )

        # Сохраняем состояние для обработки следующего сообщения
        from main import AirsoftBot
        context = query.message._bot_data
        context['awaiting_setting'] = actual_key
        context['setting_message_id'] = query.message.message_id

    async def handle_price_history(self, query):
        """История изменений цен"""
        changes = self.product_ops.get_price_changes(24)  # За 24 часа

        if not changes:
            text = "📈 *История цен*\n\nЗа последние 24 часов изменений цен не было."
        else:
            text = "📈 *История цен за 24 часа*\n\n"
            for change in changes[:10]:  # Последние 10 изменений
                product_name = change['product_name'] or 'Неизвестный товар'
                price = change['price']
                change_time = change['change_date'].strftime('%H:%M')
                text += f"• {change_time} - {product_name}: {price} руб.\n"

            if len(changes) > 10:
                text += f"\n... и еще {len(changes) - 10} изменений"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
        ]])

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def handle_tech_ops(self, query):
        """Технические операции"""
        text = "🛠 *Технические операции*\n\nВыберите операцию:"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧹 Очистить историю цен", callback_data="admin_clear_history")],
            [InlineKeyboardButton("📋 Экспорт товаров", callback_data="admin_export_products")],
            [InlineKeyboardButton("🔧 Проверить соединение с БД", callback_data="admin_check_db")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def handle_back_to_main(self, query):
        """Возврат в главное меню"""
        keyboard = await self.get_admin_keyboard()
        await query.edit_message_text(
            "👨‍💻 *Панель администратора*",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )