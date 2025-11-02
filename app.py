from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
import sys
import os
import random

from module import get_all_items, filter_furniture, calculate_rent, calculate_buyout_price

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_for_modoya' 

FOLDER_PATH = "Pictures"

try:
    ALL_FURNITURE_ITEMS = get_all_items(FOLDER_PATH)
except FileNotFoundError:
    print(f"Error: Could not find data in folder '{FOLDER_PATH}'. Check FOLDER_PATH in app.py")
    sys.exit(1)

@app.route('/Pictures/<path:filename>')
def serve_pictures(filename):
    return send_from_directory(FOLDER_PATH, filename)

@app.route('/')
def index():
    if 'cart' not in session:
        session['cart'] = {}

    items_for_render = []
    for item in ALL_FURNITURE_ITEMS:
        
        img_url_path = item['image_path'].replace('\\', '/') 
        filename_only = img_url_path.split('/')[-1]
        
        monthly_rent = calculate_rent(item['metadata'])
        buyout_price = calculate_buyout_price(item['metadata'])
        
        item_data = item.copy()
        item_data['id'] = item['metadata']['row_id']
        item_data['image_url'] = url_for('serve_pictures', filename=filename_only)
        item_data['monthly_rent'] = monthly_rent
        item_data['buyout_price'] = buyout_price
        items_for_render.append(item_data)
        
    return render_template('index.html', 
                           items=items_for_render,
                           cart_item_count=sum(session['cart'].values()))

if __name__ == '__main__':
    app.run(debug=True)