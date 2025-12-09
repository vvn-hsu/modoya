# Modoya - Furniture Rental & Buyout Platform

**HCI 584 Final Project**

Modoya is a web-based furniture platform that offers flexible ownership options. Users can choose to rent high-quality furniture for a monthly fee or purchase items outright ("buyout"). The platform features an AI-powered **Style Analyzer**, which uses the OpenAI API to analyze user-uploaded room photos and recommend furniture that matches their personal interior design style.

## ✨ Features

* **Flexible Ownership:** Toggle between "Rent" (monthly payments) and "Buy" (one-time purchase) options.
* **AI Style Analyzer:** Upload 3 photos of your space, and our AI (powered by GPT-4o) will analyze your "Style DNA" and recommend matching furniture from our catalog.
* **Dynamic Cart System:** Real-time cart updates, mini-cart preview, and duration adjustments for rentals.
* **Order Management:** View past rental and buyout history.
* **Responsive Design:** Clean, modern interface optimized for desktop and tablet usage.

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
* [cite_start]**Python 3.8+** [cite: 126]
* **OpenAI API Key** (Required for the Style Analyzer feature)

## 📦 Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/modoya.git](https://github.com/your-username/modoya.git)
    cd modoya
    ```

2.  **Install Dependencies**
    [cite_start]Install the required Python packages using `requirements.txt`[cite: 52]:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Configuration (Important)**
    This project requires an API key to run. For security reasons, the key file is not included in the repository.
    
    * Create a new file named `keys.py` in the root directory.
    * Add your OpenAI API key inside it like this:
        ```python
        # keys.py
        OpenAI_key = "sk-your-actual-api-key-here"
        ```
    * *Note: `keys.py` is included in `.gitignore` to prevent accidental upload.*

## 🚀 Usage

1.  **Run the Application**
    Execute the main script from your terminal:
    ```bash
    python main.py
    ```
    *Note: The main entry point is `main.py`, not `run_cli.py` or `generate_csv_data.py`.* [cite: 29]

2.  **Access the Website**
    Open your web browser and navigate to:
    ```
    [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
    ```

## 📂 Project Structure

[cite_start]Here is a brief overview of the key files[cite: 12, 258]:

* `main.py`: The main Flask application entry point. Handles routing, API calls, and session management.
* `module.py`: Contains core logic for furniture data loading, filtering, and price calculations (Rent vs. Buyout logic).
* `templates/`: HTML files for the frontend (Index, Cart, Orders).
* `Pictures/`: Image assets for the furniture catalog.
* `requirements.txt`: List of Python dependencies.

## 📝 License

This project is created for educational purposes for the HCI 584 course at Iowa State University.

---
*Created by Vivian Hsu - Fall 2025*