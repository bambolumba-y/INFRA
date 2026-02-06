#!/usr/bin/env python3
"""Generate a Telethon StringSession for use in .env.

Usage:
    python scripts/generate_session.py

You will need your Telegram API ID and API Hash from https://my.telegram.org.
The script will guide you through the login process and print the session string.
"""

from __future__ import annotations

import asyncio
import sys

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("Telethon is required. Install it with: pip install telethon")
    sys.exit(1)


async def main() -> None:
    print("=" * 60)
    print("  INFRA — Telethon StringSession Generator")
    print("=" * 60)
    print()
    print("Get your API credentials at https://my.telegram.org")
    print()

    api_id_str = input("Enter your API ID: ").strip()
    try:
        api_id = int(api_id_str)
    except ValueError:
        print("Error: API ID must be a number.")
        sys.exit(1)

    api_hash = input("Enter your API Hash: ").strip()
    if not api_hash:
        print("Error: API Hash cannot be empty.")
        sys.exit(1)

    print()
    print("Starting Telethon login flow...")
    print("You will receive a code on Telegram. Enter it when prompted.")
    print()

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()

    session_string = client.session.save()
    await client.disconnect()

    print()
    print("=" * 60)
    print("  SUCCESS! Your StringSession is:")
    print("=" * 60)
    print()
    print(session_string)
    print()
    print("Add this to your .env file as:")
    print(f'TELEGRAM_SESSION_STRING={session_string}')
    print()


if __name__ == "__main__":
    asyncio.run(main())
