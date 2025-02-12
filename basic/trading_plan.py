from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging
import os
import requests
from googleapiclient.errors import HttpError
from google.auth.exceptions import GoogleAuthError, TransportError
from socket import timeout
from typing import Dict, List, Optional
import yaml
from yaml.loader import SafeLoader  # for safe YAML loading

# setting this as an environment var was the only way it worked for me
# find your OpenAI API key at https://platform.openai.com/api-keys
# NOTE: just because you have a ChatGPT Plus account does NOT mean
# you automatically have a paid OpenAI API account. You will need to set up
# your OpenAI developer account (specifically the billing part) which you can
# do here: https://platform.openai.com/settings/organization/billing/overview 
os.environ["OPENAI_API_KEY"]="your OpenAI API Key"

# Define the scope for read-only access to the Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Path to your service account credentials JSON file
# If you don't have one, you'll need to create it using instructions here
# https://cloud.google.com/iam/docs/keys-create-delete#iam-service-account-keys-create-console
SERVICE_ACCOUNT_FILE = '/path/to/your/credentials.json'

# The ID of the spreadsheet (found in its URL)
SPREADSHEET_ID = 'your-spreadsheet-id'

# The range of cells you want to read (for example, Sheet1!A2:B for tickers in column A and prices in column B)
RANGE_NAME = 'Sheet1!A2:B'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_plan.log'),
        logging.StreamHandler()
    ]
)

def get_stock_prices():
    # Authenticate using the service account credentials
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Build the service object for the Sheets API
    service = build('sheets', 'v4', credentials=creds)
    
    # Call the Sheets API to get the values in the specified range
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])
    stock_dict = {}    

    if not values:
        print("No data found in the specified range.")
    else:
        for row in values:
            # Expecting ticker in the first column and price in the second column.
            ticker = row[0]
            price = row[1] if len(row) > 1 else "N/A"
            # print(f"Ticker: {ticker}, Price: {price}")
            stock_dict[ticker] = price

    return stock_dict


# --- ChatGPT API Call Setup ---
def get_trading_strategy(stock_prices):
    """
    Sends the stock prices to a ChatGPT endpoint (model 'gpt-4o') to get a trading strategy.
    """
    # Construct a prompt including the stock prices
    prompt = (
        f"Using the following stock prices: {stock_prices}, "
        "please develop a momentum-based trading strategy for a tech portfolio. "
        "Include clear entry and exit criteria, risk management guidelines, and performance expectations. "
        "Output the strategy in a structured, easy-to-follow format."
    )
    
    # Replace the URL and model with your specific ChatGPT endpoint details if different.
    api_key = os.getenv("OPENAI_API_KEY")  # Replace with your actual API key
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4o",  # Using the specified model
        "messages": [
            {"role": "system", "content": "You are a market analyst expert in momentum-based trading strategies."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }
   
    logging.debug(f"Sending POST {url}")

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        raise Exception(f"ChatGPT API call failed: {response.status_code} {response.text}")

class TradingPlan:
    def __init__(self):
        self.stock_prices = {}
        self.config = load_config()
        self.service = None
        self.connect_to_sheets()
    
    def connect_to_sheets(self):
        """
        Establishes connection to Google Sheets API.
        
        Returns:
            Resource: Google Sheets API service object
        
        Raises:
            Exception: If connection fails
        """
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.config['google_sheets']['service_account_file'], 
                scopes=self.config['google_sheets']['scopes']
            )
            self.service = build('sheets', 'v4', credentials=creds)
            return self.service
        except Exception as e:
            raise Exception(f"Failed to connect to Google Sheets: {str(e)}")

    def get_stock_prices(self):
        # Move the existing get_stock_prices function content here
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=RANGE_NAME).execute()
        values = result.get('values', [])
        self.stock_prices = {}    

        if not values:
            print("No data found in the specified range.")
        else:
            for row in values:
                ticker = row[0]
                price = row[1] if len(row) > 1 else "N/A"
                self.stock_prices[ticker] = price

        return self.stock_prices

    def get_trading_strategy(self):
        # Move the existing get_trading_strategy function here
        # Update to use self.stock_prices
        return get_trading_strategy(self.stock_prices)

    def validate_trading_data(self, data):
        # Move the existing validate_trading_data function here
        if not isinstance(data, dict):
            raise ValueError("Trading data must be a dictionary")
        required_fields = ['symbol', 'entry_price', 'stop_loss']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    def process_trade_data(self, trade_data: Dict[str, float], 
                          risk_percentage: float = 0.01) -> Optional[Dict[str, float]]:
        # Move the existing process_trade_data function here
        pass

    def calculate_risk(self, trade_data: dict) -> float:
        """
        Calculate the risk amount for a trade based on entry price, stop loss, and position size.
        
        Args:
            trade_data (dict): Dictionary containing:
                - entry_price (float): Entry price of the trade
                - stop_loss (float): Stop loss price
                - position_size (float): Size of the position
                
        Returns:
            float: The calculated risk amount in currency units
        """
        entry_price = float(trade_data['entry_price'])
        stop_loss = float(trade_data['stop_loss'])
        position_size = float(trade_data['position_size'])
        
        # Calculate the risk per share/unit
        risk_per_unit = abs(entry_price - stop_loss)
        
        # Calculate total risk (default risk percentage is 1% = 0.01)
        risk_amount = risk_per_unit * position_size * 0.01
        
        return risk_amount

def main():
    try:
        trading_plan = TradingPlan()
        # Step 1: Retrieve stock prices from Google Sheets
        try:
            stock_prices = trading_plan.get_stock_prices()
            if not stock_prices:
                print("No stock data retrieved. Check your sheet and range settings.")
                return
            print("Retrieved Stock Prices:")
            for ticker, price in stock_prices.items():
                print(f"  {ticker}: {price}")
        except (GoogleAuthError, HttpError) as api_err:
            logging.error(f"Google API error: {api_err}")
        except timeout as timeout_err:
            logging.error(f"Connection timeout: {timeout_err}")
        except Exception as e:
            logging.critical(f"Unexpected error: {e}")
        
        # Step 2: Get trading strategy
        strategy = trading_plan.get_trading_strategy()
        print("\nGenerated Trading Strategy:\n")
        print(strategy)
        
    except Exception as e:
        print("Error:", str(e))

def load_config():
    try:
        with open('config.yaml', 'r') as file:
            return yaml.load(file, Loader=SafeLoader)  # Using SafeLoader for security
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise

if __name__ == '__main__':
    main()

