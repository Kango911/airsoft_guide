#!/usr/bin/env python3
"""
Скрипт для добавления тестовых данных в базу
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))


def add_test_data():
    """Добавление тестовых данных"""
    try:
        from database.operations import ProductOperations

        product_ops = ProductOperations()

        # Тестовые данные
        test_products = [
            {
                'name': 'BB шары 0.25g Blaster (3000 шт)',
                'price': 450.0,
                'competitor': 'StrikePlanet',
                'url': 'https://strikeplanet.ru/catalog/raskhodniki/straykbolnye-shary/',
                'weight': '0.25g',
                'package': '3000 шт'
            },
            {
                'name': 'BB шары 0.30g Blaster (3000 шт)',
                'price': 550.0,
                'competitor': 'StrikePlanet',
                'url': 'https://strikeplanet.ru/catalog/raskhodniki/straykbolnye-shary/',
                'weight': '0.30g',
                'package': '3000 шт'
            },
            {
                'name': 'BB шары 0.25g Bio (5000 шт)',
                'price': 750.0,
                'competitor': 'StrikePlanet',
                'url': 'https://strikeplanet.ru/catalog/raskhodniki/straykbolnye-shary/',
                'weight': '0.25g',
                'package': '5000 шт'
            },
            {
                'name': 'BB шары 0.25g Premium',
                'price': 420.0,
                'competitor': 'Airsoft-Rus',
                'url': 'https://airsoft-rus.ru/catalog/1096/',
                'weight': '0.25g',
                'package': '3000 шт'
            },
            {
                'name': 'BB шары 0.28g Sniper',
                'price': 520.0,
                'competitor': 'Airsoft-Rus',
                'url': 'https://airsoft-rus.ru/catalog/1096/',
                'weight': '0.28g',
                'package': '3000 шт'
            }
        ]

        # Добавляем товары
        added_count = 0
        for product in test_products:
            try:
                product_ops.add_competitor_product(product)
                print(f"✅ Добавлен: {product['name']} - {product['price']} руб.")
                added_count += 1
            except Exception as e:
                print(f"❌ Ошибка добавления {product['name']}: {e}")

        print(f"\n🎉 Добавлено {added_count} тестовых товаров")
        print("\n💡 Теперь можно использовать команду /prices в боте")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("📋 Проверьте настройки базы данных в key/key.py")


if __name__ == "__main__":
    add_test_data()