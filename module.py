import os
import json
import random
from PIL import Image

def load_metadata(folder):
    data_list = []
    for file in os.listdir(folder):
        if file.endswith(".json"):
            with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                data_list.append(data)
    return data_list

def load_image(file_path):
    return Image.open(file_path)

def get_all_items(folder):
    items = []
    metadata_list = load_metadata(folder)
    for data in metadata_list:
        img_file = data["image_file"] 
        
        items.append({
            "image_path": img_file,
            "metadata": data
        })
    return items

def filter_furniture(items, category=None, style=None, color=None, season=None):
    """
    Filters the list of furniture items based on multiple criteria. (Case-insensitive)
    Returns: A new list of filtered item dictionaries.
    """
    filtered_items = items

    if category:
        filtered_items = [item for item in filtered_items if item['metadata']['category'].lower() == category.lower()]
    
    if style:
        filtered_items = [item for item in filtered_items if item['metadata']['style'].lower() == style.lower()]
    
    if color:
        filtered_items = [item for item in filtered_items if item['metadata']['color'].lower() == color.lower()]
        
    if season:
        filtered_items = [item for item in filtered_items if item['metadata']['season'].lower() == season.lower()]

    return filtered_items


def calculate_price(item_metadata):
    price_map = {
        "Sofa": 1200, "Chair": 800, "Storage": 700, "Lamp": 350
    }
    
    base_price = price_map.get(item_metadata.get('category'), 500)
    
    adjustment = 0
    if item_metadata.get('material') in ['Velvet', 'Leather', 'Marble']:
        adjustment += 300
    if item_metadata.get('style') in ['Mid-Century Modern', 'Art Deco']:
        adjustment += 150

    final_price = base_price + adjustment
    
    return {
        "price": final_price,
        "base": base_price,
        "adjustment": adjustment
    }

def place_order(item, price_details):
    metadata = item['metadata']
    price = price_details['price']
    
    print("\n========================================")
    print(f"CONFIRMATION: You are about to order the following item:")
    print(f"   Item: {metadata['series']} ({metadata['style']})")
    print(f"   Price: ${price:.2f}")
    
    user_confirm = input("Confirm order (Type 'yes' to proceed): ").strip().lower()

    if user_confirm == 'yes':
        print("\nORDER PLACED SUCCESSFULLY!")
        print(f"Order ID: {hash(metadata['row_id'])}")
        print(f"Total Charged: ${price:.2f}")
        print(f"Delivery: Estimated 5-7 business days.")
        print("========================================\n")
        return True
    else:
        print("\nOrder cancelled by user.\n")
        return False

def get_available_options(items):
    """
    Extracts all unique values for key attributes for display to the user.
    """
    options = {
        'style': set(),
        'color': set(),
        'season': set(),
        'category': set()
    }
    for item in items:
        metadata = item['metadata']
        options['style'].add(metadata.get('style', 'N/A'))
        options['color'].add(metadata.get('color', 'N/A'))
        options['season'].add(metadata.get('season', 'N/A'))
        options['category'].add(metadata.get('category', 'N/A'))
    return {k: sorted(list(v)) for k, v in options.items()}

def display_recommendations(recommendations):
    if not recommendations:
        print("Sorry, no furniture items match your criteria.")
        return

    print(f"\nFound {len(recommendations)} items matching your preferences.")
    
    print("--- AVAILABLE ITEMS FOR ORDER ---")
    
    display_limit = 5
    selectable_items = recommendations[:display_limit]
    
    for i, item in enumerate(selectable_items):
        price_details = calculate_price(item['metadata'])
        
        print(f"[{i+1}] Item: {item['metadata']['series']} | Style: {item['metadata']['style']} | Price: ${price_details['price']:.2f}")
        
    print("---------------------------------")
    
    selection = input(f"Enter the number of the item you want to order (1-{min(len(recommendations), display_limit)}), or type '0' to exit: ").strip()

    try:
        selection_index = int(selection)
        if selection_index == 0:
            print("Selection exited.")
            return

        if 1 <= selection_index <= len(selectable_items):
            selected_item = selectable_items[selection_index - 1]
            selected_price = calculate_price(selected_item['metadata'])
            place_order(selected_item, selected_price)
        else:
            print("Invalid selection number. Please try again.")

    except ValueError:
        print("Invalid input. Please enter a number.")