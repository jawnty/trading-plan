from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging
import os
import requests

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
   


    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        raise Exception(f"ChatGPT API call failed: {response.status_code} {response.text}")

def main():
    try:
        # Step 1: Retrieve stock prices from Google Sheets.
        stock_prices = get_stock_prices()
        if not stock_prices:
            print("No stock data retrieved. Check your sheet and range settings.")
            return
        print("Retrieved Stock Prices:")
        for ticker, price in stock_prices.items():
            print(f"  {ticker}: {price}")
        
        # Step 2: Feed these prices to the ChatGPT endpoint to build a trading strategy.
        strategy = get_trading_strategy(stock_prices)
        print("\nGenerated Trading Strategy:\n")
        print(strategy)
        
    except Exception as e:
        print("Error:", str(e))


if __name__ == '__main__':
    main()

