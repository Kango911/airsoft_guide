from .base_parser import BaseParser
from bs4 import BeautifulSoup


class AirsoftRusParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.base_url = "https://airsoft-rus.ru"
        self.catalog_url = "https://airsoft-rus.ru/catalog/1096/"

    def parse_products(self):
        html = self.get_page(self.catalog_url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Ищем товары (селекторы нужно уточнить)
        product_items = soup.find_all('div', class_='item')  # уточнить класс

        for item in product_items:
            try:
                name_elem = item.find('a', class_='name')
                price_elem = item.find('span', class_='price')

                if name_elem and price_elem:
                    name = name_elem.text.strip()
                    price_text = price_elem.text.strip()
                    price = self.clean_price(price_text)
                    url = name_elem['href'] if name_elem.get('href') else ''
                    if url and not url.startswith('http'):
                        url = self.base_url + url

                    products.append({
                        'name': name,
                        'price': price,
                        'url': url,
                        'competitor': 'Airsoft-Rus'
                    })
            except Exception as e:
                print(f"Error parsing product: {e}")
                continue

        return products

    def clean_price(self, price_text):
        import re
        clean = re.sub(r'[^\d,.]', '', price_text.replace(' ', ''))
        clean = clean.replace(',', '.')
        try:
            return float(clean)
        except:
            return 0