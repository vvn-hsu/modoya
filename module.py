import os
import json
import random

def load_metadata(folder):
    """
    Loads JSON metadata files from the specified folder.
    
    Args:
        folder (str): Path to the directory containing JSON files.
        
    Returns:
        list: A list of dictionaries containing the loaded metadata.
    """
    data_list = []
    for file in os.listdir(folder):
        if file.endswith(".json"):
            with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                data_list.append(data)
    return data_list

def load_image(file_path):
    """
    Opens an image file using PIL.
    
    Args:
        file_path (str): Path to the image file.
        
    Returns:
        Image: A PIL Image object.
    """
    from PIL import Image
    return Image.open(file_path)

def get_all_items(folder):
    """
    Aggregates all furniture items (images and metadata) from the folder.
    
    Args:
        folder (str): Directory containing the assets.
        
    Returns:
        list: A list of dictionaries, each containing 'image_path' and 'metadata'.
    """
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
    """
    Filters furniture items based on provided criteria.
    
    Args:
        items (list): The list of furniture items.
        category (str, optional): Filter by category.
        style (str, optional): Filter by style.
        color (str, optional): Filter by color.
        season (str, optional): Filter by season.
        
    Returns:
        list: A filtered list of furniture items.
    """
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
    """
    Returns the monthly rental price of an item.

    Uses the item's own "monthly_rent" from its JSON file. Items added later
    without that field fall back to a price based on category and material.

    Args:
        item_metadata (dict): Metadata dictionary of the item.

    Returns:
        float: Monthly rent.
    """
    if item_metadata.get('monthly_rent') is not None:
        return item_metadata['monthly_rent']

    base_rent_map = {
        "Sofa": 60, "Chair": 40, "Storage": 35, "Table": 25, "Lamp": 20
    }
    base_rent = base_rent_map.get(item_metadata.get('category'), 25)

    adjustment = 0
    if any(word in item_metadata.get('material', '') for word in ['Velvet', 'Leather', 'Marble']):
        adjustment += 15
    if item_metadata.get('style') in ['Mid-Century Modern', 'Art Deco']:
        adjustment += 10

    return base_rent + adjustment

def calculate_buyout_price(item_metadata):
    """
    Returns the buyout (purchase) price of an item.

    Uses the item's own "buyout_price" from its JSON file, with the same kind
    of fallback as calculate_rent for items that do not have one.

    Args:
        item_metadata (dict): Metadata dictionary of the item.

    Returns:
        float: Buyout price.
    """
    if item_metadata.get('buyout_price') is not None:
        return item_metadata['buyout_price']

    buyout_map = {
        "Sofa": 1200, "Chair": 800, "Storage": 700, "Table": 500, "Lamp": 350
    }
    base_buyout_price = buyout_map.get(item_metadata.get('category'), 500)

    adjustment = 0
    if any(word in item_metadata.get('material', '') for word in ['Velvet', 'Leather', 'Marble']):
        adjustment += 300
    if item_metadata.get('style') in ['Mid-Century Modern', 'Art Deco']:
        adjustment += 150

    return base_buyout_price + adjustment

# ---------------------------------------------------------------------------
# Rental terms
# ---------------------------------------------------------------------------

# (key, length in months, label). Two weeks counts as half a month.
RENTAL_TERMS = [
    ("2w", 0.5, "2 weeks"),
    ("1m", 1, "1 month"),
    ("3m", 3, "3 months"),
    ("6m", 6, "6 months"),
    ("12m", 12, "12 months"),
    ("18m", 18, "18 months"),
    ("24m", 24, "24 months"),
]
DEFAULT_TERM = "12m"
_TERM_MONTHS = {key: months for key, months, _ in RENTAL_TERMS}
_TERM_LABELS = {key: label for key, _, label in RENTAL_TERMS}

def normalize_term(term):
    """Returns a valid term key. Accepts a key ("6m") or a month count (6)."""
    if term in _TERM_MONTHS:
        return term
    try:
        months = int(term)
    except (TypeError, ValueError):
        return DEFAULT_TERM
    key = f"{months}m"
    return key if key in _TERM_MONTHS else DEFAULT_TERM

def term_months(term):
    return _TERM_MONTHS[normalize_term(term)]

def term_label(term):
    return _TERM_LABELS[normalize_term(term)]

def rental_total(item_metadata, term):
    """Total rent for the whole term."""
    return calculate_rent(item_metadata) * term_months(term)

# ---------------------------------------------------------------------------
# Product display helpers
# ---------------------------------------------------------------------------

def product_name(item_metadata):
    """The unique display name, falling back to the generic series name."""
    return item_metadata.get('name') or item_metadata.get('series', 'Furniture')

def format_dimensions(item_metadata):
    """Returns 'W 84 x D 36 x H 33 in (213 x 91 x 84 cm)', or None if missing."""
    dims = item_metadata.get('dimensions')
    if not dims:
        return None
    w, d, h = dims['w'], dims['d'], dims['h']
    cm = lambda inches: round(inches * 2.54)
    return f"W {w} × D {d} × H {h} in ({cm(w)} × {cm(d)} × {cm(h)} cm)"

def stock_status(item_metadata):
    """Returns (key, label): key is 'in', 'low' or 'out'."""
    stock = item_metadata.get('stock')
    if stock is None:
        return ("in", "In stock")
    if stock <= 0:
        return ("out", "Out of stock")
    if stock <= 2:
        return ("low", f"Only {stock} left")
    return ("in", "In stock")

def size_reference(height_in):
    """A common object of similar height, so the size is easy to picture."""
    references = [
        (17, "about the height of a sofa seat (17 in)"),
        (24, "about the height of a nightstand (24 in)"),
        (31, "about the height of a dining table (30 in)"),
        (40, "about the height of a kitchen counter (36 in)"),
        (60, "about the height of a dresser top to an adult's shoulder"),
        (70, "a little shorter than an average adult (5 ft 7 in)"),
        (79, "about the height of an average adult (5 ft 7 in) or a bit taller"),
    ]
    for limit, text in references:
        if height_in <= limit:
            return text
    return "about the height of a standard door (80 in)"

def get_available_options(items):
    """
    Extracts all unique filter options (style, color, season, category) from items.
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

def get_item_by_id(items, item_id):
    """Retrieves a single item from the list by its row_id."""
    for item in items:
        if str(item['metadata'].get('row_id')) == str(item_id):
            return item
    return None

# The following functions (place_order, display_recommendations) 
# appear to be CLI-related but are kept for compatibility.

def place_order(item, rental_details, order_type="RENT"):
    """Handles the CLI logic for placing an order."""
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
    """Displays recommended items in the CLI."""
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