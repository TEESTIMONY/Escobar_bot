import requests
import random
import time
proxies_list = [
    {"http": "http://nejpopbg:zdtwx7to1lgq@199.187.190.42:7145", "https": "http://nejpopbg:zdtwx7to1lgq@199.187.190.42:7145"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@103.4.248.119:6427", "https": "http://nejpopbg:zdtwx7to1lgq@103.4.248.119:6427"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@207.228.35.249:6924", "https": "http://nejpopbg:zdtwx7to1lgq@207.228.35.249:6924"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@198.145.102.125:5481", "https": "http://nejpopbg:zdtwx7to1lgq@198.145.102.125:5481"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@192.46.186.229:5578", "https": "http://nejpopbg:zdtwx7to1lgq@192.46.186.229:5578"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@63.246.151.5:5336", "https": "http://nejpopbg:zdtwx7to1lgq@63.246.151.5:5336"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@69.30.74.116:5826", "https": "http://nejpopbg:zdtwx7to1lgq@69.30.74.116:5826"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@207.228.8.72:5158", "https": "http://nejpopbg:zdtwx7to1lgq@207.228.8.72:5158"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@192.46.186.124:5473", "https": "http://nejpopbg:zdtwx7to1lgq@192.46.186.124:5473"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@63.246.151.165:5496", "https": "http://nejpopbg:zdtwx7to1lgq@63.246.151.165:5496"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@103.196.8.15:5415", "https": "http://nejpopbg:zdtwx7to1lgq@103.196.8.15:5415"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@69.30.76.103:6499", "https": "http://nejpopbg:zdtwx7to1lgq@69.30.76.103:6499"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@62.164.241.211:8444", "https": "http://nejpopbg:zdtwx7to1lgq@62.164.241.211:8444"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@45.117.52.230:6267", "https": "http://nejpopbg:zdtwx7to1lgq@45.117.52.230:6267"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@69.30.74.38:5748", "https": "http://nejpopbg:zdtwx7to1lgq@69.30.74.38:5748"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@192.53.64.186:5464", "https": "http://nejpopbg:zdtwx7to1lgq@192.53.64.186:5464"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@130.180.239.17:6656", "https": "http://nejpopbg:zdtwx7to1lgq@130.180.239.17:6656"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@103.196.8.52:5452", "https": "http://nejpopbg:zdtwx7to1lgq@103.196.8.52:5452"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@207.228.8.77:5163", "https": "http://nejpopbg:zdtwx7to1lgq@207.228.8.77:5163"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@207.228.35.202:6877", "https": "http://nejpopbg:zdtwx7to1lgq@207.228.35.202:6877"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@199.187.190.72:7175", "https": "http://nejpopbg:zdtwx7to1lgq@199.187.190.72:7175"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@69.30.77.184:6924", "https": "http://nejpopbg:zdtwx7to1lgq@69.30.77.184:6924"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@168.158.184.231:6242", "https": "http://nejpopbg:zdtwx7to1lgq@168.158.184.231:6242"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@130.180.255.8:9699", "https": "http://nejpopbg:zdtwx7to1lgq@130.180.255.8:9699"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@82.140.159.172:6172", "https": "http://nejpopbg:zdtwx7to1lgq@82.140.159.172:6172"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@45.196.42.35:5424", "https": "http://nejpopbg:zdtwx7to1lgq@45.196.42.35:5424"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@207.228.35.131:6806", "https": "http://nejpopbg:zdtwx7to1lgq@207.228.35.131:6806"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@103.73.34.136:5536", "https": "http://nejpopbg:zdtwx7to1lgq@103.73.34.136:5536"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@5.182.198.82:5658", "https": "http://nejpopbg:zdtwx7to1lgq@5.182.198.82:5658"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@207.135.196.39:6954", "https": "http://nejpopbg:zdtwx7to1lgq@207.135.196.39:6954"},
]


def get_solana_price():
    
    url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"

    # Randomly choose a proxy from the list
    proxy = random.choice(proxies_list)
    
    try:
        response = requests.get(url, proxies=proxy)
        response.raise_for_status()  # Check if the request was successful
        data = response.json()
        return data.get('solana', {}).get('usd', 'Price not available')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price data:\n{e}")
        return None
# Example usage
while True:
    price = get_solana_price()
    if price is not None:
        print(f"The current price of Solana is ${price}")
    else:
        print("Failed to retrieve the price.")
