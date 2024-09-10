import requests
import re
from web3 import Web3

PANCAKE_FACTORY_ADDRESS = Web3.to_checksum_address('0xca143ce32fe78f1f7019d7d551a6402fc5350c73')
UNISWAP_FACTORY_ADDRESS = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
BASE_WETH_ADDRESS = '0x4200000000000000000000000000000000000006'
WBNB_ADDRESS = Web3.to_checksum_address('0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c')
WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
infura_url = 'https://mainnet.infura.io/v3/9a7cbdec6fb8401b99acf17aac6ad0d3'
bsc_url = 'https://bsc-dataseed.binance.org/'
PANCAKESWAP_FACTORY_ABI = '''
[
    {
        "constant": true,
        "inputs": [
            {
                "internalType": "address",
                "name": "tokenA",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "tokenB",
                "type": "address"
            }
        ],
        "name": "getPair",
        "outputs": [
            {
                "internalType": "address",
                "name": "pair",
                "type": "address"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''
UNISWAP_FACTORY_ABI = '''
[
    {
        "constant": true,
        "inputs": [
            {
                "internalType": "address",
                "name": "tokenA",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "tokenB",
                "type": "address"
            }
        ],
        "name": "getPair",
        "outputs": [
            {
                "internalType": "address",
                "name": "pair",
                "type": "address"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''
ERC_20_ABI = '''
[
    {
        "constant": true,
        "inputs": [],
        "name": "name",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "internalType": "uint8",
                "name": "",
                "type": "uint8"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''
CONTRACT_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "balance",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]
PAIR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0In", "type": "uint256"},
            {"indexed": False, "name": "amount1In", "type": "uint256"},
            {"indexed": False, "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "name": "amount1Out", "type": "uint256"},
            {"indexed": True, "name": "to", "type": "address"}
        ],
        "name": "Swap",
        "type": "event"
    }
]

web3 = Web3(Web3.HTTPProvider(infura_url))
bsc_web3 = Web3(Web3.HTTPProvider(bsc_url))
uniswap_factory_contract = web3.eth.contract(address=UNISWAP_FACTORY_ADDRESS, abi=UNISWAP_FACTORY_ABI)




def get_token_price(addr, pair):
    # Fetch and return token price from an API
    pass

def get_weth_price_in_usd():
    # Fetch and return WETH price in USD from an API
    pass

def special_format(number):
    return "{:,.2f}".format(number)

def format_market_cap(market_cap):
    if market_cap >= 1_000_000:
        return f"{market_cap / 1_000_000:.2f}M"
    elif market_cap >= 1_000:
        return f"{market_cap / 1_000:.2f}K"
    else:
        return f"{market_cap:.2f}"



async def get_pair_address(token_address):
    pair_address = uniswap_factory_contract.functions.getPair(token_address, WETH_ADDRESS).call()
    return pair_address
async def is_valid_ethereum_address(address: str) -> bool:
    return re.match(r'^0x[a-fA-F0-9]{40}$', address) is not None
async def get_pair_address_bsc(token_address):
    factory_contract = bsc_web3.eth.contract(address=PANCAKE_FACTORY_ADDRESS, abi=PANCAKESWAP_FACTORY_ABI)
    pair_address = factory_contract.functions.getPair(token_address, WBNB_ADDRESS).call()
    return pair_address

async def get_token_details(token_address):
    token_contract = web3.eth.contract(address=token_address, abi=ERC_20_ABI)
    name = token_contract.functions.name().call()
    symbol = token_contract.functions.symbol().call()
    decimal= token_contract.functions.decimals().call()
    return name, symbol,decimal




    
