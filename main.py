import os
import json
import random
import sys
from module import *
FOLDER_PATH = "Pictures"

if __name__ == "__main__":
    
    print("\n--- Modoya Furniture Recommendation System (Non-UI Version) ---")
    
    try:
        all_items = get_all_items(FOLDER_PATH)
    except FileNotFoundError:
        print(f"Error: Could not find data in folder '{FOLDER_PATH}'. Please check the path.")
        sys.exit(1)
    
    print(f"System loaded {len(all_items)} furniture items.")

    available_options = get_available_options(all_items)
    print("\nAvailable Styles:", ', '.join(available_options['style']))
    print("Available Colors:", ', '.join(available_options['color']))
    print("Available Seasons:", ', '.join(available_options['season']))
    print("Available Categories:", ', '.join(available_options['category']))
    
    
    print("\n--- Please enter your preferences (Leave blank to skip a filter) ---")

    user_style = input("Enter preferred Style (e.g., Scandinavian, Japandi): ").strip()
    user_color = input("Enter preferred Color (e.g., Brown, Green, White): ").strip()
    user_season = input("Enter preferred Season (e.g., summer, winter): ").strip()
    user_category = input("Enter preferred Category (e.g., Sofa, Lamp, Storage): ").strip()

    recommendations = filter_furniture(
        all_items,
        category=user_category,
        style=user_style,
        color=user_color,
        season=user_season
    )

    print("\n--- Final Recommendation Output ---")
    display_recommendations(recommendations)