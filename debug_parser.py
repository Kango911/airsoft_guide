#!/usr/bin/env python3
"""
Тестовый скрипт для отладки парсера
"""

import logging
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(__file__))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_strikeplanet_parser():
    """Тестирование парсера StrikePlanet"""
    from parsers.strikeplanet_parser import StrikePlanetParser

    print("🔍 Тестируем парсер StrikePlanet...")

    parser = StrikePlanetParser()

    # Сохраняем HTML для анализа
    html = parser.get_page(parser.catalog_url)
    if html:
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ HTML страница сохранена в debug_page.html")

    # Парсим товары
    products = parser.parse_products()

    print(f"📊 Найдено товаров: {len(products)}")

    for i, product in enumerate(products[:10]):  # Показываем первые 10
        print(f"\n--- Товар {i + 1} ---")
        print(f"Название: {product.get('name', 'Нет')}")
        print(f"Цена: {product.get('price', 'Нет')}")
        print(f"URL: {product.get('url', 'Нет')}")
        print(f"Вес: {product.get('weight', 'Нет')}")
        print(f"Упаковка: {product.get('package', 'Нет')}")

    return products


def analyze_html_structure():
    """Анализ структуры HTML"""
    from bs4 import BeautifulSoup

    with open('debug_page.html', 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    print("\n🔍 Анализ структуры HTML:")

    # Ищем все элементы с классами
    elements_with_classes = soup.find_all(class_=True)
    class_count = {}

    for element in elements_with_classes[:100]:  # Первые 100 элементов
        for class_name in element.get('class', []):
            class_count[class_name] = class_count.get(class_name, 0) + 1

    # Сортируем по частоте
    common_classes = sorted(class_count.items(), key=lambda x: x[1], reverse=True)[:20]

    print("📊 Самые частые классы:")
    for class_name, count in common_classes:
        print(f"  .{class_name}: {count} раз")

    # Ищем потенциальные товары
    print("\n🔍 Поиск товаров:")
    for class_name, count in common_classes:
        if any(keyword in class_name.lower() for keyword in ['product', 'item', 'card', 'goods', 'catalog']):
            elements = soup.select(f'.{class_name}')
            print(f"\n🎯 Класс .{class_name} ({count} элементов):")
            for i, elem in enumerate(elements[:3]):  # Показываем первые 3
                text = elem.get_text(strip=True)[:100]
                print(f"  {i + 1}. {text}")


if __name__ == "__main__":
    print("🚀 Запуск отладки парсера")
    print("=" * 50)

    products = test_strikeplanet_parser()

    if not products:
        print("\n❌ Товары не найдены, анализируем структуру...")
        analyze_html_structure()