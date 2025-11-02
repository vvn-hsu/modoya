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
        img_file = data.get("image_file") 
        
        items.append({
            "image_path": img_file,
            "metadata": data
        })
    return items

def filter_furniture(items, category=None, style=None, color=None, season=None):
    filtered_items = items

    if category:
        filtered_items = [item for item in filtered_items if item['metadata'].get('category', '').lower() == category.lower()]
    
    if style:
        filtered_items = [item for item in filtered_items if item['metadata'].get('style', '').lower() == style.lower()]
    
    if color:
        filtered_items = [item for item in filtered_items if item['metadata'].get('color', '').lower() == color.lower()]
        
    if season:
        filtered_items = [item for item in filtered_items if item['metadata'].get('season', '').lower() == season.lower()]

    return filtered_items

def calculate_rent(item_metadata):
    base_rent_map = {
        "Sofa": 60, "Chair": 40, "Storage": 35, "Lamp": 20
    }
    
    base_rent = base_rent_map.get(item_metadata.get('category'), 25)
    
    adjustment = 0
    if item_metadata.get('material') in ['Velvet', 'Leather', 'Marble']:
        adjustment += 15
    if item_metadata.get('style') in ['Mid-Century Modern', 'Art Deco']:
        adjustment += 10

    monthly_rent = base_rent + adjustment
    
    return monthly_rent

def calculate_buyout_price(item_metadata):
    buyout_map = {
        "Sofa": 1200, "Chair": 800, "Storage": 700, "Lamp": 350
    }
    
    base_buyout_price = buyout_map.get(item_metadata.get('category'), 500)
    
    adjustment = 0
    if item_metadata.get('material') in ['Velvet', 'Leather', 'Marble']:
        adjustment += 300
    if item_metadata.get('style') in ['Mid-Century Modern', 'Art Deco']:
        adjustment += 150

    final_buyout_price = base_buyout_price + adjustment
    
    return final_buyout_price

def get_available_options(items):
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

def get_item_by_id(items, item_id):
    """Retrieves a single item from the list by its row_id."""
    for item in items:
        if str(item['metadata'].get('row_id')) == str(item_id):
            return item
    return None

def place_order(item, rental_details, order_type="RENT"):
    metadata = item['metadata']
    duration = rental_details.get('duration', 0)
    monthly_rent = rental_details.get('monthly_rent', 0)
    buyout_price = rental_details.get('buyout_price', 0)

    print("\n========================================")
    print(f"CONFIRMATION: You are about to proceed with the following:")
    print(f"   Item: {metadata['series']} ({metadata['style']})")
    
    if order_type == "RENT":
        total_cost = monthly_rent * duration
        print(f"   Action: RENT for {duration} months")
        print(f"   Monthly Rent: ${monthly_rent:.2f}")
        print(f"   Total Rental Fee: ${total_cost:.2f} (Pre-paid)")
        
    elif order_type == "BUY":
        total_cost = buyout_price
        print(f"   Action: BUYOUT")
        print(f"   Total Buyout Price: ${total_cost:.2f}")

    user_confirm = input("Confirm order (Type 'yes' to proceed): ").strip().lower()

    if user_confirm == 'yes':
        print("\nORDER PLACED SUCCESSFULLY!")
        print(f"Order Type: {order_type}")
        print(f"Order ID: {hash(metadata['row_id'])}")
        print(f"Total Charged: ${total_cost:.2f}")
        print(f"Delivery: Estimated 5-7 business days.")
        print("========================================\n")
        return True
    else:
        print("\nOrder cancelled by user.\n")
        return False

def display_recommendations(recommendations, duration):
    if not recommendations:
        print("Sorry, no furniture items match your criteria.")
        return

    print(f"\nFound {len(recommendations)} items matching your preferences.")
    
    print("--- AVAILABLE ITEMS FOR RENTAL/PURCHASE ---")
    
    display_limit = 5
    selectable_items = recommendations[:display_limit]
    
    for i, item in enumerate(selectable_items):
        monthly_rent = calculate_rent(item['metadata'])
        buyout_price = calculate_buyout_price(item['metadata'])
        total_rental_cost = monthly_rent * duration
        
        print(f"[{i+1}] Item: {item['metadata']['series']} | Style: {item['metadata']['style']}")
        print(f"      Monthly Rent: ${monthly_rent:.2f} | Total Rent ({duration}M): ${total_rental_cost:.2f} | Buyout Price: ${buyout_price:.2f}")
        
    print("---------------------------------------------")
    
    selection = input(f"Enter the number of the item you want to proceed with (1-{min(len(recommendations), display_limit)}), or type '0' to exit: ").strip()

    try:
        selection_index = int(selection)
        if selection_index == 0:
            print("Selection exited.")
            return

        if 1 <= selection_index <= len(selectable_items):
            selected_item = selectable_items[selection_index - 1]
            
            rental_details = {
                "duration": duration,
                "monthly_rent": calculate_rent(selected_item['metadata']),
                "buyout_price": calculate_buyout_price(selected_item['metadata'])
            }
            
            action = input("Select action (Type 'RENT' or 'BUY'): ").strip().upper()
            
            if action in ["RENT", "BUY"]:
                place_order(selected_item, rental_details, order_type=action)
            else:
                print("Invalid action. Please enter 'RENT' or 'BUY'.")

        else:
            print("Invalid selection number. Please try again.")

    except ValueError:
        print("Invalid input. Please enter a number.")