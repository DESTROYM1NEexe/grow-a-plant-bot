# Grow a Plant Bot

A Telegram bot where players grow a plant, collect coins, open cases, manage a shared garden, and upgrade their garden through daily actions.

## Features
- Daily coin farming and plant growth
- Plant collection and mutations
- Garden upgrades and pets
- Shared cooperative garden invites
- Telegram payment flow support
- SQLite persistence

## Requirements
- Python 3.11+
- Telegram bot token

## Setup
1. Create a `.env` file from the example:
   ```bash
   copy .env.example .env
   ```
2. Fill in your Telegram values in `.env`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```bash
   python Bot.py
   ```

## Environment variables
- `BOT_TOKEN` — your Telegram bot token
- `SUPPORT_CONTACT` — support contact or username
- `ADMIN_IDS` — comma-separated Telegram user IDs
- `DB_PATH` — SQLite database path, defaults to `garden.db`

## License
MIT
