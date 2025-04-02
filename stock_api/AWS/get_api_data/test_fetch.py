from get_api_data import get_api_data  # update this with the correct filename
from dotenv import load_dotenv
import json

load_dotenv()  # loads your .env file with ALPHAVANTAGE_API_KEY

data = get_api_data()

# Pretty print the result
print(json.dumps(data, indent=2))
