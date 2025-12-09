# Modoya - Developer's Guide

**Date:** December 2025
**Author:** Vivian Hsu
**Course:** HCI 584

---

## 1. Overview
Modoya is a Flask-based web application serving as a furniture e-commerce platform. It supports dual ownership models (Rental vs. Buyout) and features an AI-powered "Style Analyzer" that utilizes OpenAI's GPT-4o model to interpret user-uploaded images and recommend matching furniture.

This document is intended for developers who need to maintain, extend, or debug the Modoya application.

### Tech Stack
* **Backend:** Python 3.8+, Flask
* **Frontend:** HTML5, CSS3 (Static/Inline), JavaScript (Vanilla), Jinja2 Templates
* **AI Integration:** OpenAI API (GPT-4o)
* **Image Processing:** Pillow (PIL)
* **Data Storage:** Local JSON metadata files (Simulated Database) & Flask Session (Cart State)

---

## 2. Project Structure & File Organization

The project follows a standard Flask directory structure with a separated logic module.

```text
modoya/
├── main.py             # ENTRY POINT: Controller, Routes, and Session Management
├── module.py           # MODEL/LOGIC: Data handling, Pricing logic, Helper functions
├── keys.py             # CONFIG: API Keys (Not verified in git)
├── templates/          # VIEW: HTML files (index, cart, orders)
├── Pictures/           # DATA: Furniture images and JSON metadata
├── docs/               # DOCUMENTATION: User & Dev guides
└── requirements.txt    # DEPENDENCIES
````

### Key Modules Description

  * **`main.py`**: The application server. It initializes the Flask app, configures the OpenAI client, loads initial data into memory, and defines all URL routes (`/`, `/cart`, `/analyze_style`, etc.).
  * **`module.py`**: A pure Python module containing the "business logic". It handles reading the file system, parsing JSON metadata, calculating dynamic prices (Rental vs. Buyout), and filtering lists.
  * **`Pictures/`**: Acts as a flat-file database. Each furniture item consists of an image file and a corresponding `.json` metadata file.

-----

## 3\. Installation & Admin Configuration

*Note: Basic installation steps are covered in the User Guide (README.md). This section covers developer-specific setup.*

### 3.1 Environment Setup

It is highly recommended to run this project in a virtual environment to avoid conflicting dependencies.

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 API Key Configuration

The application **will crash** on startup or during analysis if `keys.py` is missing or the OpenAI Key is invalid.

  * Ensure `keys.py` exists in the root directory.
  * Format: `OpenAI_key = "sk-..."`
  * **Security Note:** `keys.py` is listed in `.gitignore` and should never be committed to the repository.

### 3.3 Hardcoded Secrets

  * **Flask Secret Key:** Currently hardcoded in `main.py` line 18 (`app.secret_key = ...`). For production deployment, this must be moved to an environment variable or `keys.py`.

-----

## 4\. Code Flow & Architecture Walkthrough

### 4.1 Application Startup

1.  **Data Loading:** When `main.py` starts, it calls `module.get_all_items(FOLDER_PATH)`.
2.  **Indexing:** This function iterates through the `Pictures/` folder, pairs `.json` files with images, and loads all furniture metadata into the global variable `ALL_FURNITURE_ITEMS`.
      * *Note:* This means data is read-only during runtime. Adding new JSON files requires a server restart.

### 4.2 The "Style Analyzer" Workflow

This is the most complex part of the application, involving frontend-backend asynchronous communication.

1.  **Frontend (`index.html`):** User uploads 3 images. JavaScript collects them and sends a `POST` request to `/analyze_style` via `fetch()`.
2.  **Backend (`main.py` -\> `analyze_style()`):**
      * Images are Base64 encoded.
      * A prompt is constructed and sent to `client.chat.completions.create` (OpenAI API).
      * **Prompt Logic:** The system prompt (`AI_SYSTEM_PROMPT`) instructs the AI to return **strict JSON** containing "Style DNA", "Key Elements", and "Design Recommendations".
3.  **Filtering & Response:**
      * The AI's response is parsed to find the "Top Style" (e.g., "Minimalist").
      * `module.filter_furniture()` is called to find items in `ALL_FURNITURE_ITEMS` matching that style.
      * Results are returned as JSON to the frontend for dynamic rendering.

### 4.3 Shopping Cart Logic

The cart is not stored in a database but in the **Flask Session** (`session['cart']`).

  * **Structure:** The session dict stores `item_id` as keys and a dictionary of details as values (`duration`, `order_type`).
  * **Pricing:** Prices are **not** stored in the session. They are recalculated on every page load (`/cart`) using `module.calculate_rent()` and `module.calculate_buyout_price()`.
      * *Why?* This ensures that if base prices change in the code, the cart reflects the new price immediately.

-----

## 5\. Known Issues & Limitations

### 5.1 Major Issues

  * **Data Persistence:** Since the cart and order history are stored in `flask.session` (client-side cookies) and in-memory variables, **all data is lost** if the user clears their browser cache or if the server restarts.
  * **Scalability:** `get_all_items` loads *all* metadata into RAM at startup. This works for 100 items but will fail with 10,000 items.

### 5.2 Minor Issues / Computational Inefficiencies

  * **Image Serving:** Images are served via a custom route (`/Pictures/<path>`) rather than a dedicated static folder or CDN. This is inefficient for high traffic.
  * **AI Latency:** The `analyze_style` route blocks until OpenAI responds, which can take 5-10 seconds. There is no loading spinner on the button, which might confuse users.

-----

## 6\. Future Work

If this project were to be extended, the following roadmap is suggested:

1.  **Database Implementation:** Migrate from JSON files to SQLite or PostgreSQL. This would allow for inventory management and persistent order history.
2.  **User Authentication:** Implement `Flask-Login` to allow users to save their "Style DNA" results and cart across devices.
3.  **Payment Integration:** Replace the mock checkout with Stripe or PayPal API.
4.  **Asynchronous Tasks:** Use Celery or Redis to handle the OpenAI API call in the background to improve UI responsiveness.