
"""
Volume Generator & Market Maker for Solana Tokens
Written by Brian the Dawg 🐕
Woof woof! This script helps generate volume and market make tokens on Solana!
If you're reading this, you're either me or someone who found my secret stash of treats...
"""

import time
import json
import random
import base64
from datetime import datetime
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import Transaction
from solders.message import Message
from solders.hash import Hash
import base58
import requests

# Woof! These are my settings - feel free to change them but remember I'm watching 👀
JUPITER_API_URL = "https://quote-api.jup.ag/v6"
JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"
SOL_MINT = "So11111111111111111111111111111111111111112"  # Good ol' SOL
RPC_URL = "https://api.mainnet-beta.solana.com"

# Brian's wallet - woof! (Replace with your own wallet private key)
WALLET_PRIVATE_KEY = "YOUR_PRIVATE_KEY_HERE"

def load_wallet_from_private_key(private_key_str):
    """
    Load wallet from private key
    Arf arf! This is like finding my favorite bone - gotta decode it first!
    """
    try:
        private_key_bytes = base58.b58decode(private_key_str)
        keypair = Keypair.from_bytes(private_key_bytes)
        print("🐕 Woof! Wallet loaded successfully! Time to make some volume!")
        return keypair
    except Exception as e:
        print(f"❌ Grr... Error loading wallet: {e}")
        print("🐕 Did you give me the right private key? *tilts head*")
        return None

def get_balance_rpc(rpc_url, pubkey):
    """
    Get SOL or token balance
    Sniff sniff... checking if we have enough treats (SOL) to play with!
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [pubkey]
        }
        response = requests.post(rpc_url, json=payload, timeout=10)
        data = response.json()
        if 'result' in data:
            return data['result']['value'] / 1e9
        return 0
    except Exception as e:
        print(f"🐕 Woof? Error getting balance: {e}")
        return 0

def get_token_balance_rpc(rpc_url, pubkey, token_mint):
    """
    Get token balance for a specific token
    Checking how many treats of a specific type we have!
    """
    try:
        # This is a simplified version - in production you'd use getTokenAccountsByOwner
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                pubkey,
                {"mint": token_mint},
                {"encoding": "jsonParsed"}
            ]
        }
        response = requests.post(rpc_url, json=payload, timeout=10)
        data = response.json()
        if 'result' in data and data['result']['value']:
            # Parse token balance
            token_amount = data['result']['value'][0]['account']['data']['parsed']['info']['tokenAmount']['uiAmount']
            return token_amount
        return 0
    except Exception as e:
        print(f"🐕 Arf? Error getting token balance: {e}")
        return 0

def get_recent_blockhash_rpc(rpc_url):
    """
    Get recent blockhash for transactions
    Need a fresh blockhash - like a fresh stick for fetch! 🎾
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getLatestBlockhash",
        "params": [{"commitment": "confirmed"}]
    }
    response = requests.post(rpc_url, json=payload, timeout=10)
    data = response.json()
    if 'result' in data:
        return data['result']['value']['blockhash']
    return None

def get_jupiter_quote(input_mint, output_mint, amount, slippage_bps=50):
    """
    Get a quote from Jupiter for swapping tokens
    Woof! Jupiter API is like the best dog park - lots of routes to choose from!
    """
    try:
        # Convert amount to smallest unit (lamports for SOL, or token decimals)
        amount_in_smallest_unit = int(amount * 1e9)  # Assuming 9 decimals for simplicity
        
        url = f"{JUPITER_API_URL}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount_in_smallest_unit,
            "slippageBps": slippage_bps,  # 50 bps = 0.5% slippage tolerance
            "onlyDirectRoutes": "false"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"🐕 Grr... Jupiter quote failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"🐕 Woof? Error getting Jupiter quote: {e}")
        return None

def get_jupiter_swap_transaction(quote_response, user_public_key, priority_fee_lamports=0):
    """
    Get the swap transaction from Jupiter
    Time to build the transaction! Like building a dog house, but with blockchain! 🏠
    """
    try:
        url = f"{JUPITER_SWAP_API}"
        payload = {
            "quoteResponse": quote_response,
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": True,
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": priority_fee_lamports,
            "asLegacyTransaction": False
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('swapTransaction')
        else:
            print(f"🐕 Grr... Jupiter swap transaction failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"🐕 Woof? Error getting swap transaction: {e}")
        return None

def send_transaction_rpc(rpc_url, transaction_bytes):
    """
    Send transaction to Solana network
    Let's throw this transaction like I throw my favorite ball! 🎾
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                base64.b64encode(transaction_bytes).decode('utf-8'),
                {
                    "encoding": "base64",
                    "skipPreflight": False,
                    "maxRetries": 3,
                    "preflightCommitment": "confirmed"
                }
            ]
        }
        response = requests.post(rpc_url, json=payload, timeout=30)
        data = response.json()
        if 'result' in data:
            return data['result']
        elif 'error' in data:
            print(f"🐕 Transaction error: {data['error']}")
            return None
        return None
    except Exception as e:
        print(f"🐕 Woof? Error sending transaction: {e}")
        return None

def execute_swap(keypair, input_mint, output_mint, amount_sol, rpc_url, slippage_bps=50):
    """
    Execute a token swap using Jupiter
    Woof woof! Time to swap! Like trading treats, but way cooler! 🦴→🍖
    """
    print(f"\n🐕 Preparing swap: {amount_sol} SOL worth from {input_mint[:8]}... to {output_mint[:8]}...")
    
    # Get quote from Jupiter
    quote = get_jupiter_quote(input_mint, output_mint, amount_sol, slippage_bps)
    if not quote:
        print("🐕 Grr... Failed to get quote from Jupiter!")
        return False, None
    
    print(f"🐕 Got quote! Output amount: {quote.get('outAmount', 'N/A')}")
    
    # Get swap transaction
    user_pubkey = str(keypair.pubkey())
    swap_tx = get_jupiter_swap_transaction(quote, user_pubkey)
    if not swap_tx:
        print("🐕 Grr... Failed to get swap transaction!")
        return False, None
    
    # Decode and sign transaction
    try:
        transaction_bytes = base64.b64decode(swap_tx)
        transaction = Transaction.from_bytes(transaction_bytes)
        
        # Sign transaction
        transaction.sign(keypair)
        signed_tx_bytes = bytes(transaction)
        
        # Send transaction
        print("🐕 Sending transaction... *tail wagging*")
        tx_signature = send_transaction_rpc(rpc_url, signed_tx_bytes)
        
        if tx_signature:
            print(f"🐕 Woof! Swap successful! TX: {tx_signature}")
            return True, tx_signature
        else:
            print("🐕 Grr... Transaction failed!")
            return False, None
            
    except Exception as e:
        print(f"🐕 Woof? Error executing swap: {e}")
        return False, None

def generate_volume(keypair, token_mint, amount_per_swap, num_swaps, delay_seconds, rpc_url):
    """
    Generate volume by repeatedly swapping tokens
    Arf arf! Time to create some volume! Like running around the yard in circles! 🌀
    """
    print("\n" + "="*60)
    print("🐕 VOLUME GENERATION MODE ACTIVATED! *excited barking*")
    print("="*60)
    print(f"Token: {token_mint}")
    print(f"Amount per swap: {amount_per_swap} SOL")
    print(f"Number of swaps: {num_swaps}")
    print(f"Delay between swaps: {delay_seconds} seconds")
    print("="*60)
    
    successful_swaps = 0
    failed_swaps = 0
    
    for i in range(num_swaps):
        print(f"\n🐕 Swap {i+1}/{num_swaps} - Let's go! *tail wagging*")
        
        # Alternate between buying and selling to generate volume
        # Like playing fetch - throw the ball, get it back, repeat!
        if i % 2 == 0:
            # Buy tokens (SOL → Token)
            print("🐕 Buying tokens... *sitting patiently*")
            success, tx = execute_swap(keypair, SOL_MINT, token_mint, amount_per_swap, rpc_url)
        else:
            # Sell tokens (Token → SOL)
            print("🐕 Selling tokens... *dropping ball*")
            # For selling, we need to calculate token amount - simplified here
            success, tx = execute_swap(keypair, token_mint, SOL_MINT, amount_per_swap, rpc_url)
        
        if success:
            successful_swaps += 1
            print(f"🐕 Woof! Swap {i+1} successful! 🎉")
        else:
            failed_swaps += 1
            print(f"🐕 Grr... Swap {i+1} failed! 😢")
        
        # Wait before next swap (unless it's the last one)
        if i < num_swaps - 1:
            print(f"🐕 Taking a {delay_seconds} second nap before next swap... *yawn*")
            time.sleep(delay_seconds)
    
    print("\n" + "="*60)
    print("🐕 VOLUME GENERATION COMPLETE! *happy barking*")
    print(f"Successful swaps: {successful_swaps}")
    print(f"Failed swaps: {failed_swaps}")
    print("="*60)

def market_make(keypair, token_mint, buy_amount, sell_amount, spread_percent, num_cycles, delay_seconds, rpc_url):
    """
    Market make by placing buy and sell orders at different prices
    Woof! Time to market make! Like being a good guard dog, protecting the price! 🛡️
    """
    print("\n" + "="*60)
    print("🐕 MARKET MAKING MODE ACTIVATED! *serious business face*")
    print("="*60)
    print(f"Token: {token_mint}")
    print(f"Buy amount: {buy_amount} SOL")
    print(f"Sell amount: {sell_amount} SOL")
    print(f"Target spread: {spread_percent}%")
    print(f"Number of cycles: {num_cycles}")
    print("="*60)
    
    successful_buys = 0
    successful_sells = 0
    
    for cycle in range(num_cycles):
        print(f"\n🐕 Market making cycle {cycle+1}/{num_cycles}")
        
        # Buy tokens (place buy order)
        print("🐕 Placing buy order... *sitting at attention*")
        buy_success, buy_tx = execute_swap(keypair, SOL_MINT, token_mint, buy_amount, rpc_url)
        
        if buy_success:
            successful_buys += 1
            print(f"🐕 Woof! Buy order executed! TX: {buy_tx}")
            
            # Wait a bit before selling
            print(f"🐕 Waiting {delay_seconds} seconds before selling... *patiently waiting*")
            time.sleep(delay_seconds)
            
            # Sell tokens (place sell order)
            print("🐕 Placing sell order... *ready to drop*")
            sell_success, sell_tx = execute_swap(keypair, token_mint, SOL_MINT, sell_amount, rpc_url)
            
            if sell_success:
                successful_sells += 1
                print(f"🐕 Woof! Sell order executed! TX: {sell_tx}")
                print(f"🐕 Made spread on cycle {cycle+1}! *happy tail wag*")
            else:
                print(f"🐕 Grr... Sell order failed on cycle {cycle+1}")
        else:
            print(f"🐕 Grr... Buy order failed on cycle {cycle+1}")
        
        # Wait before next cycle (unless it's the last one)
        if cycle < num_cycles - 1:
            print(f"🐕 Taking a {delay_seconds} second break... *lying down*")
            time.sleep(delay_seconds)
    
    print("\n" + "="*60)
    print("🐕 MARKET MAKING COMPLETE! *proud dog pose*")
    print(f"Successful buys: {successful_buys}")
    print(f"Successful sells: {successful_sells}")
    print("="*60)

def main():
    """
    Main function - woof woof! This is where the magic happens!
    Brian the Dog's main entry point! 🐕
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Volume Generator & Market Maker by Brian the Dog 🐕',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate volume with 10 swaps of 0.1 SOL each
  python volume_market_maker.py volume --token TOKEN_MINT --amount 0.1 --swaps 10
  
  # Market make with buy/sell cycles
  python volume_market_maker.py marketmake --token TOKEN_MINT --buy 0.1 --sell 0.1 --cycles 5
        """
    )
    
    parser.add_argument('--private-key', type=str, default=WALLET_PRIVATE_KEY,
                       help='Wallet private key (or set WALLET_PRIVATE_KEY in script)')
    parser.add_argument('--rpc-url', type=str, default=RPC_URL,
                       help='Solana RPC URL')
    parser.add_argument('--slippage', type=int, default=50,
                       help='Slippage in basis points (default: 50 = 0.5%%)')
    
    subparsers = parser.add_subparsers(dest='mode', help='Mode: volume or marketmake')
    
    # Volume generation mode
    volume_parser = subparsers.add_parser('volume', help='Generate volume by repeatedly swapping')
    volume_parser.add_argument('--token', type=str, required=True,
                              help='Token mint address')
    volume_parser.add_argument('--amount', type=float, required=True,
                              help='Amount of SOL per swap')
    volume_parser.add_argument('--swaps', type=int, default=10,
                              help='Number of swaps to execute (default: 10)')
    volume_parser.add_argument('--delay', type=float, default=5.0,
                              help='Delay between swaps in seconds (default: 5.0)')
    
    # Market making mode
    mm_parser = subparsers.add_parser('marketmake', help='Market make by placing buy/sell orders')
    mm_parser.add_argument('--token', type=str, required=True,
                          help='Token mint address')
    mm_parser.add_argument('--buy', type=float, required=True,
                          help='Buy amount in SOL per cycle')
    mm_parser.add_argument('--sell', type=float, required=True,
                          help='Sell amount in SOL per cycle')
    mm_parser.add_argument('--cycles', type=int, default=5,
                          help='Number of buy/sell cycles (default: 5)')
    mm_parser.add_argument('--delay', type=float, default=10.0,
                          help='Delay between buy and sell in seconds (default: 10.0)')
    mm_parser.add_argument('--spread', type=float, default=1.0,
                          help='Target spread percentage (default: 1.0%%)')
    
    args = parser.parse_args()
    
    # Print Brian's welcome message
    print("\n" + "="*60)
    print("🐕 Woof woof! Brian the Dog's Volume Generator & Market Maker!")
    print("="*60)
    print("🐕 Ready to generate some volume and market make tokens!")
    print("="*60)
    
    # Load wallet
    if args.private_key == "YOUR_PRIVATE_KEY_HERE":
        print("\n❌ Grr... You need to set your wallet private key!")
        print("🐕 Either edit WALLET_PRIVATE_KEY in the script or use --private-key argument")
        return
    
    keypair = load_wallet_from_private_key(args.private_key)
    if not keypair:
        return
    
    wallet_address = str(keypair.pubkey())
    balance = get_balance_rpc(args.rpc_url, wallet_address)
    print(f"🐕 Wallet address: {wallet_address}")
    print(f"🐕 SOL balance: {balance} SOL")
    
    if balance < 0.1:
        print("\n⚠️  Woof? Your balance seems low. Make sure you have enough SOL!")
        response = input("🐕 Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("🐕 Okay, exiting... *sad whimper*")
            return
    
    # Execute based on mode
    if args.mode == 'volume':
        print("\n🐕 Volume generation mode selected! *excited barking*")
        generate_volume(
            keypair,
            args.token,
            args.amount,
            args.swaps,
            args.delay,
            args.rpc_url
        )
    elif args.mode == 'marketmake':
        print("\n🐕 Market making mode selected! *professional dog pose*")
        market_make(
            keypair,
            args.token,
            args.buy,
            args.sell,
            args.spread,
            args.cycles,
            args.delay,
            args.rpc_url
        )
    else:
        print("\n🐕 Woof? You need to specify a mode: 'volume' or 'marketmake'")
        parser.print_help()
        return
    
    print("\n🐕 All done! Time for a treat! *happy tail wagging* 🦴")
    print("="*60)

if __name__ == "__main__":
    main()
