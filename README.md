# Modoya - Furniture Rental & Buyout Platform

**HCI 584 Final Project - Fall 2025**

Modoya is a web-based furniture platform that offers flexible ownership options. Users can choose to rent high-quality furniture for a monthly fee or purchase items outright ("buyout"). The platform features an AI-powered **Style Analyzer**, which uses the OpenAI API to analyze user-uploaded room photos and recommend furniture that matches their personal interior design style.

![Modoya Homepage Screenshot]( 這裡填入圖片路徑: 例如 docs/images/homepage.png )
> **建議圖片 1：首頁截圖**
> *這裡放一張網站首頁（index.html）的完整截圖，最好能看到 Banner 和下面的家具列表，讓這份文件一打開就很有視覺衝擊力。*

## ✨ Key Features

* **Flexible Ownership:** Seamlessly toggle between "Rent" (monthly payments) and "Buy" (one-time purchase) options for every item.
* **AI Style Analyzer:** Upload 3 photos of your space, and our AI (powered by GPT-4o) will analyze your "Style DNA" and recommend matching furniture.
* **Dynamic Cart:** Real-time updates for rental duration and order types.
* **Order Tracking:** View rental and purchase history with generated order IDs.

![Style Analyzer Feature]( 這裡填入圖片路徑: 例如 docs/images/analyzer_result.png )
> **建議圖片 2：AI 風格分析結果**
> *這裡建議放「Style Analyzer」分析完成後的畫面（彈跳視窗顯示 Style DNA 長條圖和推薦家具的那一頁）。這是你專案最酷的技術亮點，一定要秀出來。*

## 🛠️ Prerequisites

* Python 3.8+
* OpenAI API Key (Required for Style Analyzer)

## 📦 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/modoya.git](https://github.com/your-username/modoya.git)
    cd modoya
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key**
    For security reasons, the API key is not included in the repository. You must create a configuration file locally:
    * Create a file named `keys.py` in the root directory.
    * Add your OpenAI API key:
        ```python
        # keys.py
        OpenAI_key = "sk-your-actual-api-key-here"
        ```

## 🚀 How to Run

1.  Start the Flask server:
    ```bash
    python main.py
    ```

2.  Open your browser and navigate to:
    `http://127.0.0.1:5000/`

![Cart and Checkout]( 這裡填入圖片路徑: 例如 docs/images/cart_checkout.png )
> **建議圖片 3：購物車或結帳畫面**
> *這裡可以放購物車頁面（顯示 Rent/Buy 不同選項）或是結帳完成的 "Order Placed" 畫面，證明你的交易邏輯是會動的。*

## 📂 Project Structure

* `main.py`: Main application entry point and Flask routes.
* `module.py`: Core logic for data handling, filtering, and price calculations.
* `templates/`: HTML frontend files.
* `Pictures/`: Furniture image assets.
* `requirements.txt`: Python dependencies.

## 📝 License

Created by Viv Hsu for HCI 584 at Iowa State University.