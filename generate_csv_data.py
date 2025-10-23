import pandas as pd
import random

def generate_furniture_columns(num_rows=100):

    styles = [
        'Mid-Century Modern', 'Minimalist', 'Scandinavian', 'Bauhaus', 'Traditional', 
        'Farmhouse', 'Rustic', 'Art Deco', 'Bohemian (Bojo)', 'Japandi', 
        'Wabi-Sabi', 'Coastal', 'Industrial', 'Retro'
    ]
    category_series_map = {
        'Chair': ['Eames Lounge Chair', 'Wassily Chair', 'Barcelona Chair', 'Womb Chair', 'Egg Chair', 'Wishbone Chair (Y-Chair)', 'Adirondack Chair', 'Panton Chair'],
        'Sofa': ['Chesterfield Sofa', 'Togo Sofa', 'LC2 Sofa', 'Noguchi Freeform Sofa', 'Sectional Sofa', 'Loveseat'],
        'Table': ['Noguchi Coffee Table', 'Saarinen Tulip Table', 'Parsons Table', 'Dining Table', 'Side Table', 'Coffee Table'],
        'Lamp': ['Arco Floor Lamp', 'PH Artichoke Lamp', 'Nesso Table Lamp', 'Floor Lamp', 'Desk Lamp'],
        'Storage': ['Bookshelf', 'Dresser', 'Sideboard', 'TV Stand', 'Cabinet']
    }
    materials_map = {
        'Chair': ['Walnut Wood', 'Light Oak', 'Bouclé Fabric', 'Velvet', 'Tweed', 'Linen', 'Black Leather', 'Brown Leather', 'Polished Chrome', 'Brushed Brass', 'Matte Black Steel', 'Rattan'],
        'Sofa': ['Bouclé Fabric', 'Velvet', 'Tweed', 'Linen', 'Black Leather', 'Brown Leather', 'Vegan Leather', 'Suede', 'Walnut Wood base'],
        'Table': ['Walnut Wood', 'Light Oak', 'Teak', 'Bent Plywood', 'Carrara Marble', 'Terrazzo', 'Smoked Glass', 'Polished Chrome', 'Matte Black Steel'],
        'Lamp': ['Brushed Brass', 'Matte Black Steel', 'Copper', 'Carrara Marble base', 'Smoked Glass', 'Acrylic', 'Linen shade'],
        'Storage': ['Walnut Wood', 'Light Oak', 'Teak', 'Bent Plywood', 'Matte Black Steel', 'Rattan', 'Cane']
    }
    colors = [
        'Beige', 'Off-white', 'Light Gray', 'Charcoal Gray', 'Warm Taupe', 'Terracotta', 
        'Olive Green', 'Mustard Yellow', 'Walnut Brown', 'Deep Teal', 'Emerald Green', 
        'Burnt Orange', 'Navy Blue', 'Black', 'White', 'Natural Wood', ''
    ]
    attributes = [
        'Plush', 'Soft', 'Textured', 'Distressed', 'High-gloss', 'Matte finish', 
        'Curvy', 'Geometric', 'Organic shape', 'Modular', 'Elegant', 
        'Playful', 'Statement piece', 'Airy', 'Vintage look', ''
    ]
    locations = ['rural', 'urban', 'suburban', '']
    seasons = ['spring', 'summer', 'autumn', 'winter', '']

    categories_list = []
    series_list = []
    styles_list = []
    materials_list = []
    colors_list = []
    attributes_list = []
    locations_list = []
    seasons_list = []
    
    categories_keys = list(category_series_map.keys())

    for _ in range(num_rows):
        category = random.choice(categories_keys)
        series = random.choice(category_series_map[category])
        material = random.choice(materials_map[category])
        style = random.choice(styles)
        color = random.choice(colors)
        attribute = random.choice(attributes)
        location = random.choice(locations)
        season = random.choice(seasons)

        categories_list.append(category)
        series_list.append(series)
        styles_list.append(style)
        materials_list.append(material)
        colors_list.append(color)
        attributes_list.append(attribute)
        locations_list.append(location)
        seasons_list.append(season)

    print("--- Copy data for 'category' column ---")
    for item in categories_list:
        print(item)
    print("\n" + "="*40 + "\n")

    print("--- Copy data for 'series' column ---")
    for item in series_list:
        print(item)
    print("\n" + "="*40 + "\n")

    print("--- Copy data for 'style' column ---")
    for item in styles_list:
        print(item)
    print("\n" + "="*40 + "\n")

    print("--- Copy data for 'material' column ---")
    for item in materials_list:
        print(item)
    print("\n" + "="*40 + "\n")
        
    print("--- Copy data for 'color' column ---")
    for item in colors_list:
        print(item)
    print("\n" + "="*40 + "\n")

    print("--- Copy data for 'attributes' column ---")
    for item in attributes_list:
        print(item)
    print("\n" + "="*40 + "\n")

    print("--- Copy data for 'location' column ---")
    for item in locations_list:
        print(item)
    print("\n" + "="*40 + "\n")

    print("--- Copy data for 'season' column ---")
    for item in seasons_list:
        print(item)
    print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    generate_furniture_columns(100)