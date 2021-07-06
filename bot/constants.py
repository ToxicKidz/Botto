import json
from enum import Enum
from os import environ
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")

BOT_TOKEN = environ["BOT_TOKEN"]
DATABASE_URL = environ["DATABASE_URL"]
DEFAULT_PREFIX = environ.get("DEFAULT_PREFIX", "bot ")
EXT_PATH = Path("bot/exts")
SQL_PATH = Path("postgres/init.sql")

with open("bot/setup.json") as f:
    SETUP = json.load(f)

class Emojis(str, Enum):
    FIRST = "⏮️"
    PREVIOUS = "⏪"
    NEXT = "⏩"
    LAST = "⏭️"
    TRASH = "🗑️"
