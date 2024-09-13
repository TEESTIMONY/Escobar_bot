import requests
import time
from dotenv import load_dotenv
import os
import json
# Load environment variables from .env file
load_dotenv()

# Initialize a global API count
api_count = 0

# Helper function to handle API limit wait
def api_limit_wait():
    time.sleep(1)  # Adjust the sleep time according to your API rate limits

# Create an Axios-like instance using requests.Session with predefined headers
class AxiosInstance:
    def __init__(self, base_url):
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json'
        })
        self.base_url = base_url

    def get(self, endpoint):
        try:
            response = self.session.get(self.base_url + endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {self.base_url + endpoint}:\n", e)
            return False

# Create instances for each base URL
axios_instance = AxiosInstance("https://api.geckoterminal.com/api/v2/")
# axios_instance_ton_viewer = AxiosInstance("https://tonapi.io/v2/")

# Function to get token information by address
def get_token(address):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/sui/tokens/{address}/info")

# Function to get token pools by token address
def get_token_pools(address, page="1"):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/sui-network/pools/{address}")


# https://api.geckoterminal.com/api/v2/
# # Function to get the last pool trades by pool address
# def get_last_pools_trades(address):
#     global api_count
#     api_count += 1
#     api_limit_wait()
#     return axios_instance.get(f"networks/ton/pools/{address}/trades")

# Function to get all token holders by token address
# def get_token_holders(address):
#     global api_count
#     api_count += 1
#     api_limit_wait()
#     return axios_instance_ton_viewer.get(f"jettons/{address}/holders?limit=1&offset=0")

# Set the API limit
api_limit = 29


if __name__ == "__main__":
    # Example token address
    token_address = "0x2e041f3fd93646dcc877f783c1f2b7fa62d30271bdef1f21ef002cebf857bded"
    # Fetch token information
    # token_info = get_token(token_address)
    # if token_info:
    #     # print("Token Information:", token_info)
    #     pass
    # else:
    #     print("Failed to retrieve token information.")
    # Fetch token pools
    token_pools = get_token_pools(token_address, page="1")
    if token_pools:
        print(token_pools)
        # print("Token Pools:", token_pools)
        # pair_address = token_pools['data'][0]['attributes']['address']
        # mkt = token_pools['data'][-1]['attributes']['market_cap_usd']
        # print(pair_address)
        # print(mkt)
    else:
        print("Failed to retrieve token pools.")

    # # Example pool address
    # pool_address = pair_address

    # # Fetch last pool trades
    # last_trades = get_last_pools_trades(pool_address)
    # if last_trades:
    #     with open('fav.json','w')as file:
    #         json.dump(last_trades,file,indent=4)
    #     swap_event = last_trades['data'][-1]
    #     signature = swap_event['attributes']['tx_hash']
    #     swap_kind = swap_event['attributes']['kind']
    # else:
    #     print("Failed to retrieve last pool trades.")

    # # Fetch token holders
    # token_holders = get_token_holders(token_address)
    # if token_holders:
    #     print("Token Holders:", token_holders)
    # else:
    #     print("Failed to retrieve token holders.")
