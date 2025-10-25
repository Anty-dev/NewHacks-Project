import os
import time
from pathlib import Path
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.api_client import ApiClient
from plaid.configuration import Configuration
from datetime import date, timedelta
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
import google.generativeai as genai
from datetime import date
import json



dotenv_path = Path("Keys.env")
load_dotenv(dotenv_path)

## Section 1

client_id = os.getenv("PLAID_CLIENT_ID")
secret = os.getenv("PLAID_APIKEY")
e = os.getenv('PLAID_ENV')
keyG = os.getenv('G')
print(keyG)

configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={"clientId": client_id, "secret": secret}
)

client = plaid_api.PlaidApi(ApiClient(configuration))

# print("test")
#print("client_id:", client_id)
# print("secret:", secret)

#report section 1 works as intended

## Section 2

request = SandboxPublicTokenCreateRequest(
    institution_id="ins_109508",
    initial_products=[Products("transactions")]
    
)

response = client.sandbox_public_token_create(request)
public_token = response.public_token
#print("Public token:", public_token)

#Report: Im pretty sure this works as intended

# #section 3

from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
exchange_response = client.item_public_token_exchange(exchange_request)
access_token = exchange_response.access_token
# #print("Access token:", access_token)

# # works i think again

# #Section 4

start_date = (date.today() - timedelta(days=30))
end_date = date.today()

request = TransactionsGetRequest(
    access_token=access_token,
    start_date=start_date,
    end_date=end_date
)

time.sleep(5)

response = client.transactions_get(request)

transactions = response.transactions  # list of transaction objects
transactions_dict = [t.to_dict() for t in transactions]

print(f"Fetched {len(transactions)} transactions")

def convert_dates(obj):
    if isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates(i) for i in obj]
    elif isinstance(obj, date):
        return obj.isoformat()  # convert date to string
    else:
        return obj


transactions_serializable = convert_dates(transactions_dict)


#Report: Code works above tis point 

#Section 5 data cleaning

def remove_nulls(obj):
    if isinstance(obj, dict):
        return {k: remove_nulls(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [remove_nulls(item) for item in obj if item is not None]
    else:
        return obj

transactions_dict = [txn.to_dict() for txn in transactions]  
cleaned_transactions = [remove_nulls(txn) for txn in transactions_dict]


transactions_to_print = convert_dates(cleaned_transactions)
#print(json.dumps(transactions_to_print, indent=2))


genai.configure(api_key=keyG)

def total_spending(transactions_to_print):
    return sum(t["amount"] for t in transactions_to_print)

def spending_by_merchant(transactions_to_print):
    category_totals = {}
    for t in transactions_to_print:
        cat = t["merchant_name"][0] if t.get("merchant_name") else "Uncategorized"
        category_totals[cat] = category_totals.get(cat, 0) + t["amount"]
    return category_totals

spending1 = spending_by_merchant(transactions_to_print)



prompt = f"""
Spending summary:
The spending by category is: {spending1}.

1. Identify spending patterns.
2. Suggest 5 concrete ways to reduce or optimize spending.
3. Estimate potential monthly savings.
"""

model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content(prompt)

print("The response is ")
print("---------------------")
print(response.text)