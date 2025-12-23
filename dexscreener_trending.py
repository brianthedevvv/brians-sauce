#!/usr/bin/env python3
"""
DexScreener Trending Bot - Get Your Token into Top 10 Trending!
Written by Brian the Dog 🐕
Woof woof! This script will spam trades until DexScreener notices your token exists!
If manipulation was an art form, this would be the Mona Lisa. Or maybe just a stick figure. Either way, it works!
"""

import time
import json
import random
import base64
from datetime import datetime
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
import base58
import requests

# Woof! Settings that make the magic happen
JUPITER_API_URL = "https://quote-api.jup.ag/v6"
JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
DEXSCREENER_TRENDING_API = "https://api.dexscreener.com/latest/dex/search?q="
SOL_MINT = "So11111111111111111111111111111111111111112"
RPC_URL = "https://api.mainnet-beta.solana.com"

# Brian's wallet - woof! (Replace with your own)
WALLET_PRIVATE_KEY = "YOUR_PRIVATE_KEY_HERE"

def load_wallet_from_private_key(private_key_str):
    """
    Load wallet from private key
    Arf! Like finding my favorite bone, but it's actually just cryptographic nonsense!
    """
    try:
        private_key_bytes = base58.b58decode(private_key_str)
        keypair = Keypair.from_bytes(private_key_bytes)
        print("🐕 Wallet loaded! Ready to manipulate some charts! *excited barking*")
        return keypair
    except Exception as e:
        print(f"❌ Grr... Error loading wallet: {e}")
        return None

def get_balance_rpc(rpc_url, pubkey):
    """Get SOL balance - checking if we have enough treats!"""
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

def get_recent_blockhash_rpc(rpc_url):
    """Get recent blockhash for transactions"""
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

def get_jupiter_quote(input_mint, output_mint, amount, slippage_bps=100):
    """
    Get a quote from Jupiter for swapping
    Woof! Jupiter knows all the best routes to fake volume!
    """
    try:
        amount_in_smallest_unit = int(amount * 1e9)
        
        url = f"{JUPITER_API_URL}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount_in_smallest_unit,
            "slippageBps": slippage_bps,
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
        print(f"🐕 Woof? Error getting quote: {e}")
        return None

def get_jupiter_swap_transaction(quote_response, user_public_key, priority_fee_lamports=1000):
    """Get swap transaction from Jupiter"""
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
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('swapTransaction')
        else:
            print(f"🐕 Grr... Swap transaction failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"🐕 Woof? Error getting swap transaction: {e}")
        return None

def send_transaction_rpc(rpc_url, transaction_bytes):
    """Send transaction to Solana - yeeting it into the void!"""
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

def execute_swap(keypair, input_mint, output_mint, amount_sol, rpc_url, slippage_bps=100):
    """
    Execute a token swap using Jupiter
    Woof woof! Time to swap and generate that sweet, sweet volume! 💰
    """
    try:
        # Get quote
        quote = get_jupiter_quote(input_mint, output_mint, amount_sol, slippage_bps)
        if not quote:
            return False, None
        
        # Get swap transaction
        user_pubkey = str(keypair.pubkey())
        swap_tx = get_jupiter_swap_transaction(quote, user_pubkey)
        if not swap_tx:
            return False, None
        
        # Decode and sign
        transaction_bytes = base64.b64decode(swap_tx)
        transaction = Transaction.from_bytes(transaction_bytes)
        transaction.sign(keypair)
        signed_tx_bytes = bytes(transaction)
        
        # Send transaction
        tx_signature = send_transaction_rpc(rpc_url, signed_tx_bytes)
        
        if tx_signature:
            return True, tx_signature
        else:
            return False, None
            
    except Exception as e:
        print(f"🐕 Woof? Error executing swap: {e}")
        return False, None

def check_dexscreener_trending(token_address):
    """
    Check if token is in DexScreener trending
    Sniff sniff... checking if we made it to the big leagues! 🏆
    """
    try:
        # Search for token on DexScreener
        search_url = f"{DEXSCREENER_TRENDING_API}{token_address}"
        response = requests.get(search_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get('pairs', [])
            
            if pairs:
                # Get the first pair (usually the most liquid)
                pair = pairs[0]
                volume_24h = pair.get('volume', {}).get('h24', 0)
                price_usd = pair.get('priceUsd', '0')
                
                return {
                    'found': True,
                    'volume_24h': float(volume_24h) if volume_24h else 0,
                    'price_usd': float(price_usd) if price_usd else 0,
                    'pair': pair
                }
        
        return {'found': False, 'volume_24h': 0, 'price_usd': 0}
    except Exception as e:
        print(f"🐕 Woof? Error checking DexScreener: {e}")
        return {'found': False, 'volume_24h': 0, 'price_usd': 0}

def get_trending_tokens():
    """
    Get current top 10 trending tokens on DexScreener (Solana)
    Checking what the competition looks like! 🔍
    """
    try:
        # Note: DexScreener doesn't have a direct "trending" API endpoint
        # This is a placeholder - you'd need to scrape their trending page
        # For now, we'll just monitor volume growth
        
        # Alternative: You could scrape the trending page or use their WebSocket
        # For simplicity, we'll track volume increases instead
        return []
    except Exception as e:
        print(f"🐕 Woof? Error getting trending tokens: {e}")
        return []

def generate_trending_volume(keypair, token_mint, target_volume_usd, rpc_url, check_interval=60):
    """
    Generate volume until token gets into trending
    Woof! This is where the magic happens! We spam trades until DexScreener notices!
    """
    print("\n" + "="*60)
    print("🐕 DEXSCREENER TRENDING BOT ACTIVATED!")
    print("🐕 Mission: Get token into top 10 trending!")
    print("="*60)
    print(f"Token: {token_mint}")
    print(f"Target volume: ${target_volume_usd:,.2f}")
    print(f"Check interval: {check_interval} seconds")
    print("="*60)
    
    wallet_address = str(keypair.pubkey())
    balance = get_balance_rpc(rpc_url, wallet_address)
    print(f"\n🐕 Wallet: {wallet_address}")
    print(f"🐕 Balance: {balance} SOL")
    
    if balance < 0.5:
        print("\n⚠️  Woof? Your balance seems low. You'll need SOL for swaps and fees!")
        response = input("🐕 Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Configuration for volume generation
    min_swap_amount = 0.01  # Minimum SOL per swap
    max_swap_amount = 0.1   # Maximum SOL per swap
    swap_delay_min = 2      # Minimum delay between swaps (seconds)
    swap_delay_max = 10     # Maximum delay between swaps (seconds)
    
    successful_swaps = 0
    failed_swaps = 0
    total_volume_generated = 0
    swap_count = 0
    is_buying = True  # Alternate between buying and selling
    
    print("\n🐕 Starting volume generation... *excited tail wagging*")
    print("🐕 This might take a while. Time to grab some treats and wait! 🦴\n")
    
    try:
        while True:
            swap_count += 1
            
            # Randomize swap amount and delay to look more organic
            # (Because nothing says "organic trading" like random numbers! 🤡)
            swap_amount = random.uniform(min_swap_amount, max_swap_amount)
            delay = random.uniform(swap_delay_min, swap_delay_max)
            
            print(f"\n{'='*60}")
            print(f"🐕 Swap #{swap_count} - Let's make some volume!")
            print(f"{'='*60}")
            
            if is_buying:
                print(f"🐕 Buying tokens with {swap_amount:.4f} SOL... *sitting at attention*")
                success, tx = execute_swap(keypair, SOL_MINT, token_mint, swap_amount, rpc_url)
                action = "BUY"
            else:
                print(f"🐕 Selling tokens worth {swap_amount:.4f} SOL... *dropping the ball*")
                success, tx = execute_swap(keypair, token_mint, SOL_MINT, swap_amount, rpc_url)
                action = "SELL"
            
            if success:
                successful_swaps += 1
                total_volume_generated += swap_amount
                print(f"🐕 Woof! {action} successful! TX: {tx}")
                print(f"🐕 Total swaps: {successful_swaps} successful, {failed_swaps} failed")
                print(f"🐕 Estimated volume generated: ~{total_volume_generated * 150:.2f} USD")
                # (Rough estimate: SOL price ~$150, but this is just for display)
            else:
                failed_swaps += 1
                print(f"🐕 Grr... {action} failed! Total fails: {failed_swaps}")
            
            # Toggle buy/sell
            is_buying = not is_buying
            
            # Check DexScreener status periodically
            if swap_count % 10 == 0:  # Check every 10 swaps
                print(f"\n🐕 Checking DexScreener status... *sniffing around*")
                token_data = check_dexscreener_trending(token_mint)
                
                if token_data['found']:
                    print(f"🐕 Token found on DexScreener!")
                    print(f"🐕 24h Volume: ${token_data['volume_24h']:,.2f}")
                    print(f"🐕 Price: ${token_data['price_usd']}")
                    
                    if token_data['volume_24h'] >= target_volume_usd:
                        print("\n🎉🎉🎉 SUCCESS! 🎉🎉🎉")
                        print(f"🐕 Target volume reached! Token should be trending!")
                        print(f"🐕 Check DexScreener to see if you made it to top 10!")
                        break
                else:
                    print("🐕 Token not found on DexScreener yet. Keep generating volume!")
            
            # Wait before next swap
            print(f"🐕 Taking a {delay:.1f} second break... *lying down*")
            time.sleep(delay)
            
            # Check balance
            current_balance = get_balance_rpc(rpc_url, wallet_address)
            if current_balance < 0.05:
                print("\n⚠️  Woof! Balance getting low! Stopping to prevent wallet drain.")
                break
            
    except KeyboardInterrupt:
        print("\n\n🐕 Interrupted by user! *stops mid-bark*")
    
    print("\n" + "="*60)
    print("🐕 VOLUME GENERATION COMPLETE!")
    print("="*60)
    print(f"Total swaps: {swap_count}")
    print(f"Successful: {successful_swaps}")
    print(f"Failed: {failed_swaps}")
    print(f"Estimated volume: ~{total_volume_generated * 150:.2f} USD")
    print("="*60)
    
    # Final check
    print("\n🐕 Final DexScreener check...")
    token_data = check_dexscreener_trending(token_mint)
    if token_data['found']:
        print(f"🐕 Final 24h Volume: ${token_data['volume_24h']:,.2f}")
        print(f"🐕 Final Price: ${token_data['price_usd']}")
        print("\n🐕 Check DexScreener now to see if you're trending! 🚀")

def continuous_trending_monitor(keypair, token_mint, rpc_url, swap_amount=0.05, delay=5):
    """
    Continuously generate volume to maintain trending status
    Woof! Once you're trending, you gotta stay trending! Like staying on top of the dog pile! 🐕
    """
    print("\n" + "="*60)
    print("🐕 CONTINUOUS TRENDING MONITOR MODE")
    print("🐕 This will keep generating volume to maintain trending status")
    print("="*60)
    print("🐕 Press Ctrl+C to stop")
    print("="*60)
    
    is_buying = True
    swap_count = 0
    
    try:
        while True:
            swap_count += 1
            print(f"\n🐕 Continuous swap #{swap_count}")
            
            if is_buying:
                print(f"🐕 Buying with {swap_amount} SOL...")
                success, tx = execute_swap(keypair, SOL_MINT, token_mint, swap_amount, rpc_url)
            else:
                print(f"🐕 Selling {swap_amount} SOL worth...")
                success, tx = execute_swap(keypair, token_mint, SOL_MINT, swap_amount, rpc_url)
            
            if success:
                print(f"🐕 Swap successful! TX: {tx}")
            else:
                print("🐕 Swap failed, continuing anyway...")
            
            is_buying = not is_buying
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\n\n🐕 Stopping continuous monitoring... *sad whimper*")

def main():
    """Main function - woof woof!"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='DexScreener Trending Bot by Brian the Dog 🐕',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate volume until token reaches target
  python dexscreener_trending_bot.py --token TOKEN_MINT --target-volume 50000
  
  # Continuous monitoring mode (maintain trending)
  python dexscreener_trending_bot.py --token TOKEN_MINT --continuous
        """
    )
    
    parser.add_argument('--token', type=str, required=True,
                       help='Token mint address')
    parser.add_argument('--private-key', type=str, default=WALLET_PRIVATE_KEY,
                       help='Wallet private key')
    parser.add_argument('--rpc-url', type=str, default=RPC_URL,
                       help='Solana RPC URL')
    parser.add_argument('--target-volume', type=float, default=50000,
                       help='Target 24h volume in USD (default: 50000)')
    parser.add_argument('--check-interval', type=int, default=60,
                       help='Check DexScreener every N swaps (default: 60)')
    parser.add_argument('--continuous', action='store_true',
                       help='Continuous mode: keep generating volume to maintain trending')
    parser.add_argument('--swap-amount', type=float, default=0.05,
                       help='Amount per swap in SOL (default: 0.05)')
    parser.add_argument('--delay', type=float, default=5,
                       help='Delay between swaps in seconds (default: 5)')
    
    args = parser.parse_args()
    
    # Print welcome
    print("\n" + "="*60)
    print("🐕 DEXSCREENER TRENDING BOT")
    print("🐕 By Brian the Dog - Making tokens trendy since today!")
    print("="*60)
    
    # Load wallet
    if args.private_key == "YOUR_PRIVATE_KEY_HERE":
        print("\n❌ Grr... You need to set your wallet private key!")
        print("🐕 Either edit WALLET_PRIVATE_KEY in the script or use --private-key")
        return
    
    keypair = load_wallet_from_private_key(args.private_key)
    if not keypair:
        return
    
    # Execute based on mode
    if args.continuous:
        continuous_trending_monitor(keypair, args.token, args.rpc_url, args.swap_amount, args.delay)
    else:
        generate_trending_volume(keypair, args.token, args.target_volume, args.rpc_url, args.check_interval)
    
    print("\n🐕 All done! Time for treats! 🦴")

if __name__ == "__main__":
    main()
