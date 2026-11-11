from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, jsonify, make_response, abort
import sys
import os
import io
import re
import math
import random
import secrets
import calendar
from datetime import datetime, date, timedelta
from werkzeug.security import safe_join

from module import (
    get_all_items, calculate_rent, calculate_buyout_price, get_item_by_id,
    RENTAL_TERMS, DEFAULT_TERM, normalize_term, term_months, term_label, rental_total,
    product_name, format_dimensions, stock_status, size_reference,
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-secret-key-for-modoya')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER_PATH = os.path.join(BASE_DIR, "Pictures")

try:
    ALL_FURNITURE_ITEMS = sorted(get_all_items(FOLDER_PATH), key=lambda i: i['metadata']['row_id'])
except FileNotFoundError:
    sys.exit(1)

# Orders live in the browser's session cookie (about 4 KB), so only the most
# recent ones are kept.
MAX_ORDERS = 10

# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

@app.template_filter('money')
def money(value):
    """$1,349 for whole amounts, $10.50 otherwise."""
    value = float(value)
    if value.is_integer():
        return f"${int(value):,}"
    return f"${value:,.2f}"

@app.template_filter('plural')
def plural(count, word):
    """1 item, 2 items."""
    return f"{count} {word}" if count == 1 else f"{count} {word}s"

@app.template_filter('nice_date')
def nice_date(value):
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return value.strftime("%b %-d, %Y")

@app.context_processor
def inject_globals():
    cart = session.get('cart', {})
    return {
        'cart_item_count': len(cart) if isinstance(cart, dict) else 0,
        'rental_terms': RENTAL_TERMS,
        'default_term': DEFAULT_TERM,
    }

def image_url(item, view=None):
    filename = item['image_path'].replace('\\', '/').split('/')[-1]
    if view:
        return url_for('serve_pictures', filename=filename, view=view)
    return url_for('serve_pictures', filename=filename)

def product_card(item):
    """Everything a template or the browser needs to show one product."""
    meta = item['metadata']
    stock_key, stock_label = stock_status(meta)
    dims = meta.get('dimensions')
    return {
        'id': str(meta['row_id']),
        'name': product_name(meta),
        'series': meta.get('series', ''),
        'style': meta.get('style', ''),
        'category': meta.get('category', 'Furniture'),
        'type': meta.get('type', ''),
        'color': meta.get('color', ''),
        'material': meta.get('material', ''),
        'description': meta.get('description', ''),
        'dimensions': format_dimensions(meta),
        'dims': dims,
        'size_reference': size_reference(dims['h']) if dims else None,
        'stock_key': stock_key,
        'stock_label': stock_label,
        'in_stock': stock_key != 'out',
        'image_url': image_url(item),
        'full_image_url': image_url(item, 'full') if meta.get('crop') else None,
        'url': url_for('product_detail', item_id=meta['row_id']),
        'monthly_rent': calculate_rent(meta),
        'buyout_price': calculate_buyout_price(meta),
    }

# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

# Images are shrunk and converted to WebP when requested, so the originals in
# Pictures/ can be replaced at any time without a separate compression step.
# A product whose JSON has a "crop" box is cropped to that part of the photo
# (used where the product shares the photo with other furniture).
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
PRODUCT_IMAGE_MAX = 640
BANNER_IMAGE_MAX = 1600
IMAGE_QUALITY = 80
_compressed_cache = {}
CROP_BY_FILENAME = {
    item['image_path'].replace('\\', '/').split('/')[-1]: item['metadata']['crop']
    for item in ALL_FURNITURE_ITEMS if item['metadata'].get('crop')
}

def compress_image(path, max_size, crop=None):
    from PIL import Image

    with Image.open(path) as im:
        im = im.convert('RGB')
        if crop:
            w, h = im.size
            im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
        im.thumbnail((max_size, max_size))
        buf = io.BytesIO()
        im.save(buf, 'WEBP', quality=IMAGE_QUALITY, method=4)
    return buf.getvalue()

@app.route('/Pictures/<path:filename>')
def serve_pictures(filename):
    path = safe_join(FOLDER_PATH, filename)
    if not path or not filename.lower().endswith(IMAGE_EXTENSIONS) or not os.path.isfile(path):
        return send_from_directory(FOLDER_PATH, filename)

    view = request.args.get('view')
    # The homepage hero shows a product photo larger and uncropped.
    max_size = BANNER_IMAGE_MAX if filename.startswith('banner') or view == 'hero' else PRODUCT_IMAGE_MAX
    crop = None if view in ('full', 'hero') else CROP_BY_FILENAME.get(filename)
    key = (path, os.path.getmtime(path), max_size, tuple(crop) if crop else None)
    if key not in _compressed_cache:
        _compressed_cache[key] = compress_image(path, max_size, crop)

    response = make_response(_compressed_cache[key])
    response.headers['Content-Type'] = 'image/webp'
    # Browsers keep it for a day; Vercel's CDN keeps it until the next deploy.
    response.headers['Cache-Control'] = 'public, max-age=86400, s-maxage=31536000'
    return response

# ---------------------------------------------------------------------------
# Catalogue and product pages
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if 'cart' not in session:
        session['cart'] = {}

    items = [product_card(item) for item in ALL_FURNITURE_ITEMS]
    categories = sorted({i['category'] for i in items})
    styles = sorted({i['style'] for i in items})
    return render_template('index.html', items=items, categories=categories, styles=styles)

@app.route('/product/<item_id>')
def product_detail(item_id):
    item = get_item_by_id(ALL_FURNITURE_ITEMS, item_id)
    if not item:
        abort(404)
    product = product_card(item)

    related = [
        product_card(i) for i in ALL_FURNITURE_ITEMS
        if i['metadata'].get('style') == product['style'] and str(i['metadata']['row_id']) != product['id']
    ][:4]
    return render_template('product.html', product=product, related=related)

# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

def get_full_cart_details():
    rent_items = []
    buy_items = []
    rent_total = 0
    rent_monthly_total = 0
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
        if not item:
            del session['cart'][item_id]
            session.modified = True
            continue

        # Older carts stored a month count in "duration".
        term = normalize_term(cart_item_data.get('term', cart_item_data.get('duration')))
        order_type = cart_item_data.get('order_type', 'RENT')

        details = product_card(item)
        details.update({
            'term': term,
            'term_label': term_label(term),
            'order_type': order_type,
        })

        if order_type == 'BUY':
            details['total_cost'] = details['buyout_price']
            buy_total += details['total_cost']
            buy_items.append(details)
        else:
            details['total_cost'] = rental_total(item['metadata'], term)
            rent_total += details['total_cost']
            rent_monthly_total += details['monthly_rent']
            rent_items.append(details)

    return {
        "rent_items": rent_items,
        "buy_items": buy_items,
        "rent_total": rent_total,
        "rent_monthly_total": rent_monthly_total,
        "buy_total": buy_total,
    }

@app.route('/cart')
def view_cart():
    return render_template('cart.html', **get_full_cart_details())

@app.route('/api/add_to_cart/<item_id>', methods=['POST'])
def api_add_to_cart(item_id):
    item = get_item_by_id(ALL_FURNITURE_ITEMS, item_id)
    if not item:
        return jsonify({"success": False, "error": "Item not found"}), 404
    if stock_status(item['metadata'])[0] == 'out':
        return jsonify({"success": False, "error": "This item is out of stock."}), 409

    order_type = request.args.get('type', 'RENT').upper()
    if order_type not in ['RENT', 'BUY']:
        order_type = 'RENT'
    term = normalize_term(request.args.get('term', DEFAULT_TERM))

    if 'cart' not in session:
        session['cart'] = {}
    session['cart'][str(item_id)] = {'term': term, 'order_type': order_type}
    session.modified = True

    cart_data = get_full_cart_details()
    all_items = cart_data['rent_items'] + cart_data['buy_items']
    cart_preview = [
        {
            'name': i['name'],
            'image_url': i['image_url'],
            'label': f"Rent · {i['term_label']}" if i['order_type'] == 'RENT' else "Buy",
        }
        for i in all_items[:3]
    ]

    name = product_name(item['metadata'])
    if order_type == 'BUY':
        message = f"Added {name} to your cart (Buy)."
    else:
        message = f"Added {name} to your cart (Rent, {term_label(term)})."

    return jsonify({
        "success": True,
        "message": message,
        "cart_item_count": len(all_items),
        "cart_preview": cart_preview,
    })

@app.route('/update_cart/<item_id>', methods=['POST'])
def update_cart(item_id):
    if item_id not in session.get('cart', {}):
        return redirect(url_for('view_cart'))

    action = request.form.get('action')
    entry = session['cart'][item_id]

    if action == 'remove':
        del session['cart'][item_id]
    elif action == 'update_term':
        entry['term'] = normalize_term(request.form.get('term'))
        entry.pop('duration', None)
    elif action == 'set_rent':
        entry['order_type'] = 'RENT'
    elif action == 'set_buy':
        entry['order_type'] = 'BUY'

    session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session['cart'] = {}
    session.modified = True
    return redirect(url_for('view_cart'))

# ---------------------------------------------------------------------------
# Checkout: cart -> review page -> "Place order" -> confirmation
# ---------------------------------------------------------------------------

def checkout_items(cart_type):
    """The cart section being checked out, with its total."""
    data = get_full_cart_details()
    if cart_type == 'RENT':
        return data['rent_items'], data['rent_total'], data['rent_monthly_total']
    if cart_type == 'BUY':
        return data['buy_items'], data['buy_total'], 0
    return [], 0, 0

def delivery_date_range():
    today = date.today()
    return today + timedelta(days=2), today + timedelta(days=60)

DELIVERY_WINDOWS = ["Morning (8 am – 12 pm)", "Afternoon (12 pm – 5 pm)", "Evening (5 pm – 8 pm)"]

@app.route('/checkout', methods=['POST'])
def checkout():
    """The cart's checkout buttons only open the review page. No order is created here."""
    cart_type = request.form.get('cart_type')
    if cart_type not in ('RENT', 'BUY'):
        return redirect(url_for('view_cart'))
    return redirect(url_for('checkout_review', cart_type=cart_type.lower()))

@app.route('/checkout/<cart_type>')
def checkout_review(cart_type, errors=None, form=None):
    cart_type = cart_type.upper()
    items, total, monthly_total = checkout_items(cart_type)
    if not items:
        return redirect(url_for('view_cart'))

    earliest, latest = delivery_date_range()
    return render_template(
        'checkout.html',
        cart_type=cart_type,
        items=items,
        total=total,
        monthly_total=monthly_total,
        earliest=earliest.isoformat(),
        latest=latest.isoformat(),
        windows=DELIVERY_WINDOWS,
        errors=errors or {},
        form=form or {},
    )

def validate_checkout(form):
    """Returns (cleaned values, errors). Card details are a mock and are never stored."""
    errors = {}
    values = {k: (form.get(k) or '').strip() for k in (
        'full_name', 'phone', 'address1', 'address2', 'city', 'state', 'zip',
        'delivery_date', 'delivery_window', 'card_name', 'card_number', 'card_expiry', 'card_cvc',
    )}

    for field, label in [('full_name', 'Full name'), ('address1', 'Street address'), ('city', 'City')]:
        if not values[field]:
            errors[field] = f"{label} is required."
    if not re.fullmatch(r'[A-Za-z]{2}', values['state']):
        errors['state'] = "Use the 2-letter state code, e.g. IA."
    if not re.fullmatch(r'\d{5}', values['zip']):
        errors['zip'] = "Enter a 5-digit ZIP code."
    if len(re.sub(r'\D', '', values['phone'])) != 10:
        errors['phone'] = "Enter a 10-digit phone number."

    earliest, latest = delivery_date_range()
    try:
        # Typed as MM/DD/YYYY on the form; YYYY-MM-DD is accepted too.
        typed = re.fullmatch(r'(\d{1,2})/?(\d{1,2})/?(\d{4})', values['delivery_date'])
        if typed:
            values['delivery_date'] = date(int(typed.group(3)), int(typed.group(1)), int(typed.group(2))).isoformat()
        chosen = date.fromisoformat(values['delivery_date'])
        if not earliest <= chosen <= latest:
            errors['delivery_date'] = f"Choose a date between {nice_date(earliest)} and {nice_date(latest)}."
    except ValueError:
        errors['delivery_date'] = "Choose a delivery date."
    if values['delivery_window'] not in DELIVERY_WINDOWS:
        errors['delivery_window'] = "Choose a delivery window."

    # MOCK PAYMENT: these checks only look at the format. Nothing is charged,
    # and only the last 4 digits are kept for the order record.
    if not values['card_name']:
        errors['card_name'] = "Name on card is required."
    if not re.fullmatch(r'\d{16}', re.sub(r'\s', '', values['card_number'])):
        errors['card_number'] = "Enter a 16-digit card number."
    match = re.fullmatch(r'(\d{2})\s*/\s*(\d{2})', values['card_expiry'])
    if not match or not 1 <= int(match.group(1)) <= 12:
        errors['card_expiry'] = "Use MM/YY."
    else:
        month, year = int(match.group(1)), 2000 + int(match.group(2))
        if (year, month) < (date.today().year, date.today().month):
            errors['card_expiry'] = "This card has expired."
    if not re.fullmatch(r'\d{3,4}', values['card_cvc']):
        errors['card_cvc'] = "Enter the 3 or 4 digit security code."

    return values, errors

@app.route('/place_order', methods=['POST'])
def place_order():
    """The only route that creates an order."""
    cart_type = (request.form.get('cart_type') or '').upper()
    items, total, _ = checkout_items(cart_type)
    if not items:
        return redirect(url_for('view_cart'))

    values, errors = validate_checkout(request.form)
    if any(not i['in_stock'] for i in items):
        errors['stock'] = "An item in this order is out of stock. Remove it from your cart to continue."
    if errors:
        form = {k: v for k, v in values.items() if not k.startswith('card_')}
        form['card_name'] = values['card_name']
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', form['delivery_date']):
            y, m, d = form['delivery_date'].split('-')
            form['delivery_date'] = f"{m}/{d}/{y}"  # show it back the way it is typed
        return checkout_review(cart_type.lower(), errors=errors, form=form), 400

    order_id = secrets.token_hex(4).upper()
    new_order = {
        'id': order_id,
        'type': cart_type,
        'placed': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'delivery': values['delivery_date'],
        'window': values['delivery_window'],
        'address': {
            'name': values['full_name'], 'phone': values['phone'],
            'line1': values['address1'], 'line2': values['address2'],
            'city': values['city'], 'state': values['state'].upper(), 'zip': values['zip'],
        },
        'card_last4': re.sub(r'\D', '', values['card_number'])[-4:],
        'cancelled': False,
        'items': [
            {
                'id': i['id'],
                'term': i['term'] if cart_type == 'RENT' else None,
                'rent': i['monthly_rent'],
                'buy': i['buyout_price'],
                'ext': 0,             # months added with "Extend"
                'return_date': None,  # set by "Schedule return"
                'bought_out': None,   # {'date', 'amount'} set by "Buy" on the orders page
            }
            for i in items
        ],
    }

    orders = session.get('orders', [])
    orders.append(new_order)
    session['orders'] = orders[-MAX_ORDERS:]

    checked_out = {i['id'] for i in items}
    session['cart'] = {k: v for k, v in session['cart'].items() if k not in checked_out}
    session.modified = True

    return redirect(url_for('order_confirmation', order_id=order_id))

@app.route('/order/<order_id>/confirmation')
def order_confirmation(order_id):
    order = find_order(order_id)
    if not order:
        return redirect(url_for('view_orders'))
    return render_template('checkout_complete.html', order=build_order_view(order))

@app.route('/checkout_complete')
def checkout_complete():
    return redirect(url_for('view_orders'))

# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def add_months(start, months):
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def rental_end(start, term, extra_months):
    if term == '2w':
        end = start + timedelta(days=14)
    else:
        end = add_months(start, int(term_months(term)))
    return add_months(end, extra_months) if extra_months else end

def months_between(start, end):
    """Billable months from start to end, rounded up (two weeks or less counts as half)."""
    days = max((end - start).days, 0)
    if days <= 14:
        return 0.5
    return math.ceil(days / 30.44)

def find_order(order_id):
    for order in session.get('orders', []):
        if isinstance(order, dict) and order.get('id') == order_id:
            return order
    return None

def build_order_view(order):
    """Turns a stored order into what the orders page shows, with dates, status and allowed actions."""
    today = date.today()
    delivery = date.fromisoformat(order['delivery'])
    delivered = today >= delivery
    is_rental = order['type'] == 'RENT'

    lines = []
    for entry in order['items']:
        item = get_item_by_id(ALL_FURNITURE_ITEMS, entry['id'])
        card = product_card(item) if item else {'name': 'Item no longer listed', 'image_url': '', 'url': '#'}
        # Prices come from the product data, so every page shows the same price for a product.
        # The values stored with the order are only used if the product is no longer listed.
        rent = card['monthly_rent'] if item else entry['rent']
        buy = card['buyout_price'] if item else entry['buy']
        line = {'index': len(lines), 'product': card, 'rent': rent, 'buy': buy}

        if is_rental:
            end = rental_end(delivery, entry['term'], entry['ext'])
            line.update({
                'term_label': term_label(entry['term']) + (f" + {plural(entry['ext'], 'month')}" if entry['ext'] else ''),
                'start': delivery, 'end': end,
            })
            if entry['bought_out']:
                bought_on = date.fromisoformat(entry['bought_out']['date'])
                rent_paid = rent * months_between(delivery, bought_on) if bought_on > delivery else 0
                line['total'] = rent_paid + entry['bought_out']['amount']
                line['status'] = f"Bought on {nice_date(bought_on)} — yours to keep"
                line['state'] = 'owned'
            elif entry['return_date']:
                pickup = date.fromisoformat(entry['return_date'])
                line['end'] = pickup
                line['total'] = rent * months_between(delivery, pickup)
                line['status'] = f"Return pickup scheduled for {nice_date(pickup)}"
                line['state'] = 'returning'
            else:
                line['total'] = rent * (term_months(entry['term']) + entry['ext'])
                if order['cancelled']:
                    line['status'], line['state'] = "Cancelled", 'cancelled'
                elif not delivered:
                    line['status'], line['state'] = f"Delivery on {nice_date(delivery)}", 'scheduled'
                elif today > end:
                    line['status'], line['state'] = "Rental ended", 'ended'
                else:
                    line['status'], line['state'] = f"Active until {nice_date(end)}", 'active'

            active = line['state'] in ('scheduled', 'active')
            months_used = months_between(delivery, today) if delivered else 0
            line['rent_paid'] = rent * months_used
            line['buyout_amount'] = max(buy - line['rent_paid'] * 0.5, 0)
            line['actions'] = {
                'extend': active,
                'buyout': active,
                'return': active,
                'return_min': max(today + timedelta(days=1), delivery + timedelta(days=1)).isoformat(),
                'return_max': end.isoformat(),
            }
        else:
            line['total'] = buy
            return_deadline = delivery + timedelta(days=30)
            if order['cancelled']:
                line['status'], line['state'] = "Cancelled", 'cancelled'
            elif entry['return_date']:
                line['status'], line['state'] = f"Return pickup scheduled for {nice_date(date.fromisoformat(entry['return_date']))}", 'returning'
            elif not delivered:
                line['status'], line['state'] = f"Delivery on {nice_date(delivery)}", 'scheduled'
            else:
                line['status'], line['state'] = "Delivered", 'owned'
            can_return = line['state'] in ('scheduled', 'owned') and today <= return_deadline
            line['actions'] = {
                'extend': False, 'buyout': False,
                'return': can_return,
                'return_min': max(today + timedelta(days=1), delivery + timedelta(days=1)).isoformat(),
                'return_max': return_deadline.isoformat(),
            }
        lines.append(line)

    if order['cancelled']:
        status = "Cancelled"
    elif not delivered:
        status = "Scheduled"
    else:
        status = "Delivered"

    return {
        'id': order['id'],
        'type': order['type'],
        'type_label': "Rental order" if is_rental else "Buy order",
        'placed': order['placed'],
        'delivery': delivery,
        'window': order.get('window', ''),
        'address': order['address'],
        'card_last4': order.get('card_last4', ''),
        'status': status,
        'cancelled': order['cancelled'],
        'can_cancel': not order['cancelled'] and not delivered,
        'lines': lines,
        'total': 0 if order['cancelled'] else sum(l['total'] for l in lines),
        'monthly_total': sum(l['rent'] for l in lines if l.get('state') in ('scheduled', 'active', 'returning')) if is_rental else 0,
    }

@app.route('/orders')
def view_orders():
    orders = [o for o in session.get('orders', []) if isinstance(o, dict) and 'delivery' in o]
    views = [build_order_view(o) for o in reversed(orders)]
    return render_template('orders.html', orders=views, max_orders=MAX_ORDERS,
                           message=session.pop('order_message', None))

@app.route('/orders/<order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    order = find_order(order_id)
    if order and build_order_view(order)['can_cancel']:
        order['cancelled'] = True
        session['order_message'] = f"Order #{order_id} was cancelled."
        session.modified = True
    return redirect(url_for('view_orders') + f"#order-{order_id}")

@app.route('/orders/<order_id>/items/<int:index>/<action>', methods=['POST'])
def manage_order_item(order_id, index, action):
    order = find_order(order_id)
    if not order or not 0 <= index < len(order['items']):
        return redirect(url_for('view_orders'))
    line = build_order_view(order)['lines'][index]
    entry = order['items'][index]
    name = line['product']['name']
    message = None

    if action == 'extend' and line['actions']['extend']:
        months = request.form.get('months', type=int)
        if months in (1, 3, 6, 12):
            entry['ext'] += months
            message = f"{name} extended by {plural(months, 'month')}."
    elif action == 'buyout' and line['actions']['buyout']:
        entry['bought_out'] = {'date': date.today().isoformat(), 'amount': line['buyout_amount']}
        message = f"You bought {name} for {money(line['buyout_amount'])}."
    elif action == 'return' and line['actions']['return']:
        try:
            pickup = date.fromisoformat(request.form.get('date', ''))
        except ValueError:
            pickup = None
        if pickup and line['actions']['return_min'] <= pickup.isoformat() <= line['actions']['return_max']:
            entry['return_date'] = pickup.isoformat()
            message = f"Return pickup for {name} scheduled on {nice_date(pickup)}."
        else:
            message = "Choose a pickup date within the allowed range."

    if message:
        session['order_message'] = message
    session.modified = True
    return redirect(url_for('view_orders') + f"#order-{order_id}")

# ---------------------------------------------------------------------------
# Style Analyzer
# ---------------------------------------------------------------------------

# MOCK ANALYSIS: the analyzer always returns this fixed result instead of
# calling an AI model. To plug in real analysis, replace analyze_photos()
# with a call that returns the same keys (the old GPT-4o version is in git
# history, commit 0510b81).
FIXED_STYLE_RESULT = {
    "confidence": 87,
    "explanation": "Light wood, low furniture and bare surfaces appear in all three photos, which puts Japandi "
                   "first (82%). Bright walls and pale textiles add Scandinavian (74%), and the open, "
                   "uncluttered layout adds Minimalist (61%).",
    "styleDNA": [
        {"name": "Japandi", "percentage": 82},
        {"name": "Scandinavian", "percentage": 74},
        {"name": "Minimalist", "percentage": 61},
    ],
    "keyElements": [
        "Neutral Color Palette", "Natural Light", "Wood Accents", "Clean Lines", "Functional Decor"
    ],
    "designRecommendations": [
        "Consider adding textured elements like a plush rug or cushions to enhance warmth.",
        "Introduce a statement floor lamp in a corner to create a focal point.",
        "Balance the wood tones with cool, neutral-colored textiles like a gray sofa.",
    ],
}

def analyze_photos(photos):
    """Where real image analysis plugs in. Currently returns the fixed mock result."""
    return FIXED_STYLE_RESULT

def recommend(weights, budget=None, count=4, exclude=()):
    """
    Picks products for a style mix, e.g. {"Japandi": 80, "Scandinavian": 40}.
    Slots are shared out in proportion to the weights; the order inside a
    style is fixed so the same settings always give the same picks.
    """
    weights = {s: w for s, w in weights.items() if w > 0}
    if not weights:
        return []

    pool = {}
    for style in weights:
        candidates = [
            i for i in ALL_FURNITURE_ITEMS
            if i['metadata'].get('style') == style
            and stock_status(i['metadata'])[0] != 'out'
            and (budget is None or calculate_rent(i['metadata']) <= budget)
            and str(i['metadata']['row_id']) not in exclude
        ]
        random.Random(style).shuffle(candidates)
        pool[style] = candidates

    total = sum(weights.values())
    shares = {s: count * w / total for s, w in weights.items()}
    slots = {s: int(shares[s]) for s in weights}
    for s in sorted(weights, key=lambda s: shares[s] - slots[s], reverse=True)[:count - sum(slots.values())]:
        slots[s] += 1

    picks = []
    for style in sorted(weights, key=weights.get, reverse=True):
        picks += pool[style][:slots[style]]
    # Fill any gap from the remaining candidates, strongest style first.
    for style in sorted(weights, key=weights.get, reverse=True):
        for item in pool[style]:
            if len(picks) >= count:
                break
            if item not in picks:
                picks.append(item)

    return [dict(product_card(i), match_reason=i['metadata']['style']) for i in picks[:count]]

def people_like_you(exclude):
    """
    MOCK COMMUNITY DATA: there is no rental history yet, so "people like you"
    is approximated with popular picks from the result's secondary styles.
    """
    secondary = {s['name']: s['percentage'] for s in FIXED_STYLE_RESULT['styleDNA'][1:]}
    return recommend(secondary, count=4, exclude=exclude)

@app.route('/analyze_style', methods=['POST'])
def analyze_style():
    photos = [request.files.get(f'image{n}') for n in (1, 2, 3)]
    if not all(photos):
        return jsonify({"error": "Please add 3 photos."}), 400

    result = analyze_photos(photos)
    weights = {s['name']: s['percentage'] for s in result['styleDNA']}
    recommendations = recommend(weights)
    return jsonify({
        **result,
        "recommendations": recommendations,
        "peopleLikeYou": people_like_you({r['id'] for r in recommendations}),
    })

@app.route('/api/style_recommendations', methods=['POST'])
def api_style_recommendations():
    data = request.get_json(silent=True) or {}
    known_styles = {i['metadata'].get('style') for i in ALL_FURNITURE_ITEMS}
    weights = {
        s: max(0, min(100, int(w)))
        for s, w in (data.get('weights') or {}).items()
        if s in known_styles and isinstance(w, (int, float))
    }
    budget = data.get('budget')
    budget = int(budget) if isinstance(budget, (int, float)) and budget > 0 else None
    return jsonify({"recommendations": recommend(weights, budget)})

@app.errorhandler(404)
def not_found(error):
    return render_template('not_found.html'), 404

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
