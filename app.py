from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
import sys
import os
import random
import time

from module import get_all_items, filter_furniture, calculate_rent, calculate_buyout_price, get_item_by_id

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
        
    cart_item_count = len(session.get('cart', {}))
    return render_template('index.html', 
                           items=items_for_render,
                           cart_item_count=cart_item_count)

@app.route('/add_to_cart/<item_id>', methods=['GET'])
def add_to_cart(item_id):
    item = get_item_by_id(ALL_FURNITURE_ITEMS, item_id)
    if not item:
        return redirect(url_for('index'))

    duration = 12
    
    if 'cart' not in session:
        session['cart'] = {}
    
    session['cart'][item_id] = {
        'duration': duration,
        'order_type': 'RENT' 
    }
    session.modified = True
    return redirect(url_for('view_cart'))

def get_full_cart_details():
    cart_items_details = []
    
    if 'cart' not in session:
        session['cart'] = {}
        return []

    for item_id in list(session['cart'].keys()):
        cart_item_data = session['cart'].get(item_id)
        
        if not isinstance(cart_item_data, dict):
            print(f"DEBUG: Removing invalid cart item ID: {item_id}")
            del session['cart'][item_id]
            session.modified = True
            continue 

        item = get_item_by_id(ALL_FURNITURE_ITEMS, item_id)

        if item:
            img_url_path = item['image_path'].replace('\\', '/')
            filename_only = img_url_path.split('/')[-1]
            image_url = url_for('serve_pictures', filename=filename_only)

            monthly_rent = calculate_rent(item['metadata'])
            buyout_price = calculate_buyout_price(item['metadata'])
            duration = int(cart_item_data.get('duration', 12)) 
            order_type = cart_item_data.get('order_type', 'RENT') 

            if order_type == 'RENT':
                total_cost = monthly_rent * duration
            elif order_type == 'BUY':
                total_cost = buyout_price
            else:
                total_cost = 0 

            cart_items_details.append({
                'id': item_id,
                'series': item['metadata']['series'],
                'style': item['metadata']['style'],
                'image_url': image_url,
                'monthly_rent': monthly_rent,
                'buyout_price': buyout_price,
                'duration': duration,
                'order_type': order_type,
                'total_cost': total_cost
            })
        else:
            del session['cart'][item_id] 
            session.modified = True
    
    return cart_items_details

@app.route('/cart')
def view_cart():
    cart_items_details = get_full_cart_details()
    cart_total = sum(item['total_cost'] for item in cart_items_details)

    return render_template('cart.html', 
                           cart_items=cart_items_details,
                           cart_total=cart_total)

@app.route('/update_cart/<item_id>', methods=['POST'])
def update_cart(item_id):
    if item_id not in session.get('cart', {}):
        return redirect(url_for('view_cart'))

    action = request.form.get('action')
    
    if action == 'remove':
        del session['cart'][item_id]
    elif action == 'update_duration':
        try:
            new_duration = int(request.form.get('duration'))
            if new_duration > 0:
                session['cart'][item_id]['duration'] = new_duration
        except (ValueError, TypeError):
            pass 
    elif action == 'set_rent':
        session['cart'][item_id]['order_type'] = 'RENT'
    elif action == 'set_buy':
        session['cart'][item_id]['order_type'] = 'BUY'

    session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    if not session.get('cart'):
        return redirect(url_for('view_cart'))

    cart_details = get_full_cart_details()
    cart_total = sum(item['total_cost'] for item in cart_details)

    order_id = abs(hash(f"{time.time()}{random.randint(1, 1000)}")) 
    
    session['cart'] = {}
    session.modified = True
    
    return render_template('checkout_complete.html', order_id=order_id, cart_total=cart_total)

@app.route('/checkout_complete')
def checkout_complete():
    return render_template('checkout_complete.html')

@app.route('/clear_cart')
def clear_cart():
    session['cart'] = {}
    session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/remove_item/<item_id>')
def remove_item(item_id):
    if item_id in session['cart']:
        del session['cart'][item_id]
        session.modified = True
    return redirect(url_for('view_cart'))

if __name__ == '__main__':
    app.run(debug=True)