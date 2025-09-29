import logging
from typing import List, Dict
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class MessageFormatter:
    """Форматирование сообщений"""

    def __init__(self):
        self.max_products_per_message = 10

    def format_welcome_message(self, user_name: str) -> str:
        """Форматирование приветственного сообщения"""
        return f"""
🤖 *Добро пожаловать, {user_name}!*

Я - бот для мониторинга цен на airsoft шары.

*Что я умею:*
• 📊 Показывать актуальные цены конкурентов
• 🛒 Показывать наши товары с возможностью заказа
• 🔄 Автоматически обновлять цены
• 📈 Отслеживать изменения цен

*Основные команды:*
/prices - Показать цены конкурентов
/products - Наши товары с ценами
/help - Получить справку

💡 *Совет:* Для быстрого заказа используйте кнопки под нашими товарами!
        """

    def format_competitor_prices(self, competitors: Dict) -> List[str]:
        """Форматирование цен конкурентов"""
        messages = []

        for competitor, products in competitors.items():
            if not products:
                continue

            message = f"🏷 *{competitor}* - Цены на шары\n\n"

            # Сортируем по цене
            sorted_products = sorted(products, key=lambda x: x['price'])

            for i, product in enumerate(sorted_products[:self.max_products_per_message]):
                price_text = f"~~{product['old_price']}~~ ➡️ {product['price']}" if product.get(
                    'old_price') else f"{product['price']}"

                message += f"{i + 1}. {product['name']}\n"
                message += f"   💰 *{price_text}* руб."

                if product.get('weight'):
                    message += f" | ⚖️ {product['weight']}"
                if product.get('package'):
                    message += f" | 📦 {product['package']}"

                message += "\n\n"

            if len(sorted_products) > self.max_products_per_message:
                message += f"*... и еще {len(sorted_products) - self.max_products_per_message} товаров*"

            message += f"\n🕒 *Обновлено:* {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            messages.append(message)

        return messages

    def format_our_products(self, products: List[Dict]) -> List[str]:
        """Форматирование наших товаров"""
        if not products:
            return ["🛒 *Наши товары*\n\nВ настоящее время товары недоступны."]

        # Разбиваем на сообщения
        messages = []
        current_message = "🛒 *Наши товары*\n\n"

        for i, product in enumerate(products):
            product_text = f"*{i + 1}. {product['name']}*\n"
            product_text += f"💰 *Цена:* {product['price']} руб."

            if product.get('old_price'):
                product_text += f" (~~{product['old_price']}~~ 🔥)"

            if product.get('weight'):
                product_text += f"\n⚖️ *Вес:* {product['weight']}"

            if product.get('package'):
                product_text += f"\n📦 *Упаковка:* {product['package']}"

            if product.get('description'):
                desc = product['description'][:100] + "..." if len(product['description']) > 100 else product[
                    'description']
                product_text += f"\n📝 {desc}"

            product_text += "\n\n"

            # Проверяем не превысит ли сообщение лимит
            if len(current_message + product_text) > 4000:
                messages.append(current_message)
                current_message = "🛒 *Наши товары* (продолжение)\n\n"

            current_message += product_text

        if current_message:
            messages.append(current_message)

        return messages

    def format_price_update_message(self, changes: List[Dict]) -> str:
        """Форматирование сообщения об обновлении цен"""
        if not changes:
            return "🔄 *Обновление цен*\n\nИзменений не обнаружено."

        message = "🔄 *ОБНОВЛЕНИЕ ЦЕН*\n\n"

        # Группируем изменения по типу товара
        our_changes = [c for c in changes if c['product_type'] == 'our']
        comp_changes = [c for c in changes if c['product_type'] == 'competitor']

        if our_changes:
            message += "*Наши товары:*\n"
            for change in our_changes[:5]:
                message += f"• {change['product_name']}: {change['price']} руб.\n"
            message += "\n"

        if comp_changes:
            message += "*Конкуренты:*\n"
            for change in comp_changes[:5]:
                message += f"• {change['product_name']}: {change['price']} руб.\n"
            message += "\n"

        message += f"📊 *Всего изменений:* {len(changes)}\n"
        message += f"🕒 *Время обновления:* {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        message += "🛒 *Наши товары:* https://t.me/c/airsoft_guide/6"

        return message


class Scheduler:
    """Планировщик задач"""

    def __init__(self, bot):
        self.bot = bot
        self.tasks = []
        self.is_running = False

    async def start(self):
        """Запуск планировщика"""
        self.is_running = True

        # Задача обновления цен
        update_interval = int(self.bot.db.get_setting('price_update_interval') or 3600)
        update_task = asyncio.create_task(self.schedule_price_updates(update_interval))
        self.tasks.append(update_task)

        logger.info(f"🕒 Планировщик запущен. Интервал обновления: {update_interval} сек.")

    async def stop(self):
        """Остановка планировщика"""
        self.is_running = False

        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("🕒 Планировщик остановлен")

    async def schedule_price_updates(self, interval: int):
        """Планирование обновления цен"""
        while self.is_running:
            try:
                await asyncio.sleep(interval)

                logger.info("🔄 Запуск автоматического обновления цен")

                # Обновляем цены
                success_count = await self.bot.update_all_prices()
                logger.info(f"✅ Автоматическое обновление завершено. Обработано: {success_count} товаров")

                # Публикуем обновление в группе если есть изменения
                if success_count > 0:
                    from telegram.ext import ContextTypes
                    context = ContextTypes.DEFAULT_TYPE
                    await self.bot.publish_price_update(context)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике: {e}")
                await asyncio.sleep(60)  # Ждем перед повторной попыткой


def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )