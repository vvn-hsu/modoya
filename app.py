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

@app.route('/add_to_cart/<int:item_id>')
def add_to_cart(item_id):
    item_id_str = str(item_id)
    
    item = next((i for i in ALL_FURNITURE_ITEMS if i['metadata']['row_id'] == item_id), None)
    
    if item:
        session['cart'][item_id_str] = session['cart'].get(item_id_str, 0) + 1
        session.modified = True

    return redirect(url_for('index'))

@app.route('/cart')
def view_cart():
    cart_details = []
    total_rent = 0
    total_buyout = 0
    
    for item_id_str, quantity in session['cart'].items():
        item_id = int(item_id_str)
        
        item = next((i for i in ALL_FURNITURE_ITEMS if i['metadata']['row_id'] == item_id), None)
        
        if item:
            monthly_rent = calculate_rent(item['metadata'])
            buyout_price = calculate_buyout_price(item['metadata'])
            
            cart_details.append({
                'item': item,
                'quantity': quantity,
                'monthly_rent': monthly_rent,
                'subtotal_rent': monthly_rent * quantity,
                'buyout_price': buyout_price * quantity
            })
            total_rent += monthly_rent * quantity
            total_buyout += buyout_price * quantity
            
    return render_template('cart.html', 
                           cart_details=cart_details,
                           total_rent=total_rent,
                           total_buyout=total_buyout)

@app.route('/checkout', methods=['POST'])
def checkout():
    session['cart'] = {}
    session.modified = True
    
    return redirect(url_for('checkout_complete'))

@app.route('/checkout_complete')
def checkout_complete():
    return render_template('checkout_complete.html')

@app.route('/clear_cart')
def clear_cart():
    session['cart'] = {}
    session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/remove_item/<int:item_id>')
def remove_item(item_id):
    item_id_str = str(item_id)
    if item_id_str in session['cart']:
        del session['cart'][item_id_str]
        session.modified = True
    return redirect(url_for('view_cart'))

if __name__ == '__main__':
    app.run(debug=True)