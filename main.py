from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, jsonify, make_response
import sys
import os
import random
import time
import base64
import io
import json
from datetime import datetime
from werkzeug.security import safe_join

from module import get_all_items, filter_furniture, calculate_rent, calculate_buyout_price, get_item_by_id

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-secret-key-for-modoya')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER_PATH = os.path.join(BASE_DIR, "Pictures")

try:
    ALL_FURNITURE_ITEMS = get_all_items(FOLDER_PATH)
except FileNotFoundError:
    sys.exit(1)

def encode_image(image_file):
    try:
        img_bytes = image_file.read()
        b64_string = base64.b64encode(img_bytes).decode('utf-8')
        return b64_string
    except Exception as e:
        return None

def format_recommendations(items_list, match_reason=""):
    items_for_render = []
    sample_size = min(len(items_list), 4)
    recommended_items = random.sample(items_list, sample_size)
    
    for item in recommended_items:
        img_url_path = item['image_path'].replace('\\', '/')
        filename_only = img_url_path.split('/')[-1]
        items_for_render.append({
            'id': item['metadata']['row_id'],
            'series': item['metadata']['series'],
            'style': item['metadata']['style'],
            'category': item['metadata'].get('category', 'Furniture'),
            'image_url': url_for('serve_pictures', filename=filename_only),
            'monthly_rent': "%.2f" % calculate_rent(item['metadata']),
            'buyout_price': "%.2f" % calculate_buyout_price(item['metadata']),
            'match_reason': match_reason
        })
    return items_for_render

# Fixed Style Analyzer result (no AI call). Every upload gets this same analysis.
FIXED_STYLE_RESULT = {
    "styleDNA": [
        {"name": "Japandi", "percentage": 82},
        {"name": "Scandinavian", "percentage": 74},
        {"name": "Minimalist", "percentage": 61}
    ],
    "keyElements": [
        "Neutral Color Palette", "Natural Light", "Wood Accents", "Clean Lines", "Functional Decor"
    ],
    "designRecommendations": [
        "Consider adding textured elements like a plush rug or cushions to enhance warmth.",
        "Introduce a statement floor lamp in a corner to create a focal point.",
        "Balance the wood tones with cool, neutral-colored textiles like a gray sofa."
    ]
}

# Images are shrunk and converted to WebP when requested, so the originals in
# Pictures/ can be replaced at any time without a separate compression step.
# The banner is wider than it is tall, so it gets a larger limit.
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
PRODUCT_IMAGE_MAX = 640
BANNER_IMAGE_MAX = 1600
IMAGE_QUALITY = 80
_compressed_cache = {}

def compress_image(path, max_size):
    from PIL import Image

    with Image.open(path) as im:
        im = im.convert('RGB')
        im.thumbnail((max_size, max_size))
        buf = io.BytesIO()
        im.save(buf, 'WEBP', quality=IMAGE_QUALITY, method=4)
    return buf.getvalue()

@app.route('/Pictures/<path:filename>')
def serve_pictures(filename):
    path = safe_join(FOLDER_PATH, filename)
    if not path or not filename.lower().endswith(IMAGE_EXTENSIONS) or not os.path.isfile(path):
        return send_from_directory(FOLDER_PATH, filename)

    max_size = BANNER_IMAGE_MAX if filename.startswith('banner') else PRODUCT_IMAGE_MAX
    key = (path, os.path.getmtime(path), max_size)
    if key not in _compressed_cache:
        _compressed_cache[key] = compress_image(path, max_size)

    response = make_response(_compressed_cache[key])
    response.headers['Content-Type'] = 'image/webp'
    # Browsers keep it for a day; Vercel's CDN keeps it until the next deploy.
    response.headers['Cache-Control'] = 'public, max-age=86400, s-maxage=31536000'
    return response

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

@app.route('/orders')
def view_orders():
    orders = session.get('orders', [])
    orders.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('orders.html', orders=orders)

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
    rent_items = []
    buy_items = []
    rent_total = 0
    buy_total = 0
    
    if 'cart' not in session:
        session['cart'] = {}

    for item_id in list(session['cart'].keys()):
        cart_item_data = session['cart'].get(item_id)
        
        if not isinstance(cart_item_data, dict):
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

            item_details = {
                'id': item_id,
                'series': item['metadata']['series'],
                'style': item['metadata']['style'],
                'category': item['metadata'].get('category', 'Furniture'),
                'image_url': image_url,
                'monthly_rent': monthly_rent,
                'buyout_price': buyout_price,
                'duration': duration,
                'order_type': order_type,
                'total_cost': 0
            }

            if order_type == 'RENT':
                total_cost = monthly_rent * duration
                item_details['total_cost'] = total_cost
                rent_total += total_cost
                rent_items.append(item_details)
            elif order_type == 'BUY':
                total_cost = buyout_price
                item_details['total_cost'] = total_cost
                buy_total += total_cost
                buy_items.append(item_details)
        else:
            del session['cart'][item_id] 
            session.modified = True
    
    return {
        "rent_items": rent_items,
        "buy_items": buy_items,
        "rent_total": rent_total,
        "buy_total": buy_total
    }

@app.route('/cart')
def view_cart():
    cart_data = get_full_cart_details()
    return render_template(
        'cart.html', 
        rent_items=cart_data['rent_items'],
        buy_items=cart_data['buy_items'],
        rent_total=cart_data['rent_total'],
        buy_total=cart_data['buy_total']
    )

@app.route('/api/add_to_cart/<item_id>', methods=['POST'])
def api_add_to_cart(item_id):
    item = get_item_by_id(ALL_FURNITURE_ITEMS, item_id)
    if not item:
        return jsonify({"success": False, "error": "Item not found"}), 404

    order_type = request.args.get('type', 'RENT').upper()
    if order_type not in ['RENT', 'BUY']:
        order_type = 'RENT'

    duration = 12
    if 'cart' not in session:
        session['cart'] = {}
    
    session['cart'][item_id] = {
        'duration': duration,
        'order_type': order_type 
    }
    session.modified = True
    
    cart_data = get_full_cart_details()
    all_items = cart_data['rent_items'] + cart_data['buy_items']
    
    cart_preview = all_items[:3]
    cart_item_count = len(all_items)
    
    message = f"Added {item['metadata']['series']} to cart ({'Buyout' if order_type == 'BUY' else 'Rental'})."

    return jsonify({
        "success": True,
        "message": message,
        "cart_item_count": cart_item_count,
        "cart_preview": cart_preview
    })

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
    cart_type = request.form.get('cart_type')

    if not session.get('cart') or not cart_type:
        return redirect(url_for('view_cart'))

    all_cart_data = get_full_cart_details()
    
    items_to_checkout = []
    items_to_keep = []
    cart_total = 0

    if cart_type == 'RENT':
        items_to_checkout = all_cart_data['rent_items']
        items_to_keep = all_cart_data['buy_items']
        cart_total = all_cart_data['rent_total']
    elif cart_type == 'BUY':
        items_to_checkout = all_cart_data['buy_items']
        items_to_keep = all_cart_data['rent_items']
        cart_total = all_cart_data['buy_total']
    else:
        return redirect(url_for('view_cart'))

    if not items_to_checkout:
        return redirect(url_for('view_cart'))

    order_id = abs(hash(f"{time.time()}{random.randint(1, 1000)}")) 
    
    new_order = {
        'id': order_id,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'timestamp': time.time(),
        'items': items_to_checkout,
        'total': cart_total,
        'type': cart_type
    }
    
    if 'orders' not in session:
        session['orders'] = []
    
    session['orders'].append(new_order)
    
    new_session_cart = {}
    for item in items_to_keep:
        item_id = str(item['id'])
        if item_id in session['cart']:
            new_session_cart[item_id] = session['cart'][item_id]
    
    session['cart'] = new_session_cart
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

@app.route('/analyze_style', methods=['POST'])
def analyze_style():
    file1 = request.files.get('image1')
    file2 = request.files.get('image2')
    file3 = request.files.get('image3')

    if not file1 or not file2 or not file3:
        return jsonify({"error": "Missing one or more images"}), 400

    top_style = FIXED_STYLE_RESULT["styleDNA"][0]["name"]
    recommended_items_data = filter_furniture(ALL_FURNITURE_ITEMS, style=top_style)
    formatted_recommendations = format_recommendations(recommended_items_data, top_style)

    return jsonify({
        **FIXED_STYLE_RESULT,
        "recommendations": formatted_recommendations
    })

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')