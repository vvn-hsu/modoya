# Modoya - Furniture Rental & Buyout Platform

**HCI 584 Final Project - Fall 2025**

Modoya is a web-based furniture platform that offers flexible ownership options. Users can choose to rent high-quality furniture for a monthly fee or purchase items outright ("buyout"). The platform features an AI-powered **Style Analyzer**, which uses the OpenAI API to analyze user-uploaded room photos and recommend furniture that matches their personal interior design style.

![Modoya Home Page](docs/demo_image/home1.jpg)

## Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.8** or higher
* **Git** (for cloning the repository)
* An active **OpenAI API Key** (Required for the Style Analyzer feature)

## Installation & Setup

Follow these steps to get Modoya running on your local machine.

### 1. Clone the repository
Open your terminal and run the following commands:
```bash
git clone https://github.com/vvn-hsu/modoya.git
cd modoya
````

### 2\. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3\. Configure API Key (Crucial Step\!)

For security reasons, the API key file is **not** included in the repository. You must create it manually:

1.  Create a new file named `keys.py` in the root directory of the project.
2.  Paste the following code into the file and replace the text with your actual OpenAI API key:

<!-- end list -->

```python
# keys.py
OpenAI_key = "sk-your-actual-api-key-here"
```

## How to Run

1.  Start the Flask server:
    ```bash
    python main.py
    ```
2.  Open your browser and navigate to:
    `http://127.0.0.1:5000/`

-----

## User Guide: Step-by-Step

### 1\. Browse the Collection

Upon launching, you will see the featured furniture collection. You can toggle between viewing Rental prices (monthly) and Buyout prices.

### 2\. AI Style Analyzer

Click the "Find My Style" button. Upload three reference photos of interior spaces you love, and our AI (powered by GPT-4o) will analyze your aesthetic preferences.

### 3\. Analysis & Recommendations

The AI will generate your personalized "Style DNA" breakdown and curate a list of furniture from our catalog that matches your specific taste.

### 4\. Dynamic Cart Management

Add items to your cart. The system separates rental and buyout items to prevent confusion. You can easily switch between "Rent" and "Buy" modes for any item and customize your rental duration (e.g., 6 months vs 12 months).

### 5\. Order Confirmation

Once you proceed to checkout, your order is confirmed with a unique transaction ID. You can view your order history in the "Orders" tab.

-----

## Caveats & Troubleshooting

  * **API Key Error:** If you see a "500 Internal Server Error" when analyzing styles, please double-check that your `keys.py` file is correctly set up and your OpenAI key has credits.
  * **Data Persistence:** This project uses local session storage. If you restart the server (`main.py`), your cart and login session will be reset.
  * **Performance:** The AI analysis may take 5-10 seconds to process depending on the OpenAI API response time.

## Project Structure (For Developers)

  * `main.py`: Main application entry point and Flask routes.
  * `module.py`: Core logic for data handling, filtering, and price calculations.
  * `keys.py`: User configuration for API keys (Not tracked by Git).
  * `templates/`: HTML frontend files.
  * `Pictures/`: Furniture image assets.
  * `docs/`: Documentation files (Sketches, Specs, User Guide).

## License

Created by Vivian Hsu for HCI 584 at Iowa State University.