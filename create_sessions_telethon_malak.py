#!/usr/bin/env python3
"""
================================================================================
🌟🌟🌟 TELEGRAM SESSION CREATOR BY KING306 (version_malk) 🌟🌟🌟
================================================================================
🛡️ Developed by: KING306 (@Mohamed_306)
📅 Last Updated: July 14, 2024
🎯 Features: Enhanced UI, Better Error Handling, Premium Look
================================================================================
"""

import os
import sys
from telethon import TelegramClient
from telethon.errors import FloodWaitError, PhoneNumberInvalidError, SessionPasswordNeededError
from colorama import init, Fore, Style
import sqlite3
import logging
import asyncio
import time
from datetime import datetime

# Initialize colorama
init()

# API Configuration - Updated as requested
API_ID = 27940100
API_HASH = "36c96063af90e06dfe60b8906d2af418"

# Path Configuration
HOME_DIR = os.path.expanduser('~')
SESSION_DIR = os.path.join(HOME_DIR, 'telethon_sessions')
TELETHON_ACCOUNTS_FILE = os.path.join(SESSION_DIR, 'accounts.txt')
DB_PATH = os.path.join(SESSION_DIR, 'accounts.db')
LOG_FILE = os.path.join(SESSION_DIR, 'session_creator.log')

# Create session directory if not exists
os.makedirs(SESSION_DIR, exist_ok=True)

# Enhanced logging setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Database initialization
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
                    (phone TEXT PRIMARY KEY, status TEXT, name TEXT, 
                    created_at TEXT, last_attempt TEXT)''')
    conn.commit()
    return conn, cursor

# Load accounts from file
def load_accounts_from_file():
    accounts = {}
    if os.path.exists(TELETHON_ACCOUNTS_FILE):
        with open(TELETHON_ACCOUNTS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ',' in line:
                    phone, name = line.split(',', 1)
                    phone = phone.strip()
                    name = name.strip()
                    if phone and name:
                        accounts[phone] = name
    return accounts

# Print with beautiful formatting
def pretty_print(message, color=Fore.WHITE, style=Style.NORMAL, box_char='#'):
    border = box_char * (len(message) + 6)
    print(f"{style}{color}{border}")
    print(f"{box_char}  {message}  {box_char}")
    print(f"{border}{Style.RESET_ALL}")

# Enhanced login function with progress tracking
async def create_telethon_session(phone, name, session_name, conn, cursor):
    session_path = os.path.join(SESSION_DIR, session_name)
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            pretty_print(f"Starting authorization for: {phone} ({name})", Fore.CYAN)
            
            # Send code request
            try:
                await client.send_code_request(phone)
                pretty_print("Verification code sent successfully", Fore.GREEN)
            except FloodWaitError as e:
                wait_time = e.seconds
                pretty_print(f"Flood wait: Please wait {wait_time} seconds", Fore.YELLOW)
                cursor.execute("UPDATE accounts SET status=?, last_attempt=? WHERE phone=?", 
                              (f"flood_wait_{wait_time}s", current_time, phone))
                conn.commit()
                return
            
            # Code input with retry
            for attempt in range(1, 4):
                code = input(f"{Fore.YELLOW}Enter verification code for {phone} (Attempt {attempt}/3): {Style.RESET_ALL}")
                try:
                    await client.sign_in(phone, code)
                    break
                except SessionPasswordNeededError:
                    # Handle 2FA
                    password = input(f"{Fore.YELLOW}Enter 2FA password for {phone}: {Style.RESET_ALL}")
                    await client.sign_in(password=password)
                    break
                except Exception as e:
                    if attempt == 3:
                        raise Exception(f"Failed after 3 attempts: {str(e)}")
                    pretty_print(f"Invalid code. Please try again ({2-attempt} attempts left)", Fore.RED)
            
            # Get user info after successful login
            me = await client.get_me()
            pretty_print(f"Successfully logged in as: {me.first_name} ({me.phone})", Fore.GREEN, Style.BRIGHT)
            
            # Update database
            cursor.execute("INSERT OR REPLACE INTO accounts VALUES (?, ?, ?, ?, ?)", 
                          (phone, "authorized", name, current_time, current_time))
            conn.commit()
            
        else:
            me = await client.get_me()
            pretty_print(f"Session already exists for: {me.first_name} ({me.phone})", Fore.BLUE)
            
    except Exception as e:
        error_msg = f"Error for {phone}: {str(e)}"
        pretty_print(error_msg, Fore.RED)
        logging.error(error_msg)
        cursor.execute("INSERT OR REPLACE INTO accounts VALUES (?, ?, ?, ?, ?)", 
                      (phone, f"error_{str(e)}", name, current_time, current_time))
        conn.commit()
    finally:
        await client.disconnect()

# Main function with enhanced UI
async def main():
    # Clear screen and show header
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{'🌟 TELEGRAM SESSION CREATOR (PREMIUM EDITION) 🌟'.center(60)}")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}API ID: {API_ID}")
    print(f"API HASH: {API_HASH}{Style.RESET_ALL}\n")
    
    # Initialize database
    conn, cursor = init_db()
    
    # Load accounts
    accounts = load_accounts_from_file()
    if not accounts:
        pretty_print(f"No accounts found in {TELETHON_ACCOUNTS_FILE}", Fore.RED)
        pretty_print("Please create the file with format: +1234567890,AccountName", Fore.YELLOW)
        conn.close()
        return
    
    pretty_print(f"Loaded {len(accounts)} accounts for processing", Fore.GREEN)
    
    # Process each account
    for phone, name in accounts.items():
        session_name = f"session_{phone[1:]}_{name.lower().replace(' ', '_')}"
        
        # Check if account exists in DB
        cursor.execute("SELECT status FROM accounts WHERE phone=?", (phone,))
        result = cursor.fetchone()
        status = result[0] if result else None
        
        if status not in ["authorized"]:
            pretty_print(f"\nProcessing: {phone} ({name})", Fore.CYAN, Style.BRIGHT, '*')
            await create_telethon_session(phone, name, session_name, conn, cursor)
        else:
            pretty_print(f"Session already exists for {phone} ({name})", Fore.BLUE)
    
    # Final summary
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE status='authorized'")
    success_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE status LIKE 'error%'")
    error_count = cursor.fetchone()[0]
    
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{' PROCESSING SUMMARY '.center(60, '─')}")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Successful sessions: {success_count}")
    print(f"{Fore.RED}Failed sessions: {error_count}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total accounts processed: {len(accounts)}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    conn.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pretty_print("Process interrupted by user", Fore.YELLOW)
        sys.exit(0)