from .base_parser import BaseParser
from bs4 import BeautifulSoup


class StrikePlanetParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.base_url = "https://strikeplanet.ru"
        self.catalog_url = "https://strikeplanet.ru/catalog/raskhodniki/straykbolnye-shary/"

    def parse_products(self):
        html = self.get_page(self.catalog_url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Ищем товары в каталоге (селекторы нужно уточнить)
        product_cards = soup.find_all('div', class_='product-card')  # уточнить класс

        for card in product_cards:
            try:
                name_elem = card.find('a', class_='product-name')
                price_elem = card.find('span', class_='price')

                if name_elem and price_elem:
                    name = name_elem.text.strip()
                    price_text = price_elem.text.strip()
                    price = self.clean_price(price_text)
                    url = self.base_url + name_elem['href'] if name_elem.get('href') else ''

                    products.append({
                        'name': name,
                        'price': price,
                        'url': url,
                        'competitor': 'StrikePlanet'
                    })
            except Exception as e:
                print(f"Error parsing product: {e}")
                continue

        return products

    def clean_price(self, price_text):
        # Убираем все нецифровые символы кроме точки и запятой
        import re
        clean = re.sub(r'[^\d,.]', '', price_text.replace(' ', ''))
        clean = clean.replace(',', '.')
        try:
            return float(clean)
        except:
            return 0