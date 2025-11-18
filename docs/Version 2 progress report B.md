# Project Update: Furniture Rental Platform

This project is a furniture rental and buyout platform built using the Python Flask framework.

## Core Features

### Backend Server (Flask)
A Flask application (`app.py`) was established to serve as the backend for all routes, business logic, and APIs.

### Product Display
Implemented dynamic product loading. The system automatically reads images and JSON data from the `Pictures` folder to display all furniture items on the homepage (`index.html`). It also calculates and shows the monthly rent and buyout price for each item.

### Shopping Cart System
A complete cart system was implemented using Flask sessions.
* Users can add items to the cart.
* Users can view the cart (`cart.html`) to update rental duration, toggle between "rent" or "buy" status, or remove items.
* Users can proceed to checkout, which processes the items and clears that portion of the cart.

## New Feature: Advanced AI Function (Decor Style Analyzer)

### Frontend Interface
A floating button ("Find Your Style!") was added to the homepage. Clicking it opens a modal window that prompts the user to upload 3 images of interior designs they like.

### OpenAI API Integration
* When images are uploaded, the backend (`app.py`) converts them into Base64 format.
* The system sends this image data, along with a specific System Prompt, to the OpenAI GPT-4o Vision API.
* This prompt (`AI_SYSTEM_PROMPT`) instructs the AI to return a structured JSON object containing 1-3 relevant "Style DNA" profiles, several "Key Elements," and actionable "Design Recommendations".

### Dynamic Recommendations
* The system parses the AI's JSON response and extracts the top-ranked style (e.g., "Minimalist").
* It then uses this style keyword to filter our own furniture database using the `filter_furniture` function.
* Finally, the results page dynamically displays these AI-recommended products, and each item is tagged with the key style that it matches.

## Recent User Experience (UX) Optimizations

* **Asynchronous (AJAX) "Add to Cart"**: The "Add to Cart" button was refactored from a traditional page redirect to an asynchronous API call (`/api/add_to_cart`) using `fetch`.
* **Mini-Cart**: After adding an item, the page no longer reloads. Instead, a "mini-cart" window slides in from the top-right, showing the added item and a cart preview, significantly improving the browsing flow.
* **Split Carts**: The shopping cart was split into two separate sections for "Rent" and "Buy". Users can check out each cart independently.
* **AI State Persistence**: To ensure the AI analysis isn't lost, the browser's `sessionStorage` is used to store the AI's JSON response. When the user returns to the homepage, JavaScript automatically checks `sessionStorage` and restores the previous analysis results, achieving state persistence.

## Reflections

The main addition was the AI Style Analyzer. This feature came from the insight that some people need furniture but don't know where to start. I believe letting users upload photos of styles they like, and having an AI analyze them to provide recommendations, is a potential solution. (Professor, you can also try uploading your own favorite interior design photos to test it out!)

I also interviewed users (6 for initial requirements, 4 with a low-fidelity prototype). Here is the feedback and the changes I made:

* **Feedback:** "Don't redirect to the cart page immediately after adding an item; it interrupts the shopping flow."
    * **Solution:** Implemented the AJAX-powered Mini-Cart overlay.
* **Feedback:** "Renting and buying feel like different shopping behaviors. They should be in separate carts."
    * **Solution:** Split the cart and checkout process for "Rent" and "Buy".
* **Feedback:** "I want the style results to be saved so I can refer back to them while I'm shopping."
    * **Solution:** Used `sessionStorage` to persist the results until the user clicks "Start New Analysis".

## Next Steps

From here, I will likely only make minor update and bug fixes rather than adding major new features. I am also open to any suggestions you may have. Thank you!