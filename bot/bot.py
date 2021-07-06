import json
import pkgutil

import aiohttp
import asyncpg
from discord.ext import commands
from dotenv import load_dotenv

from . import constants, exts

load_dotenv()

class Bot(commands.Bot):
    def __init__(self, db: asyncpg.pool.Pool, **kwargs):
        self.db = db
        self.http_session = aiohttp.ClientSession()
        command_prefix = 'bot '
        super().__init__(command_prefix, **kwargs)

    async def initialize_database(self):
        await self.db
        async with self.db.acquire() as conn:
            await conn.execute(constants.SQL_PATH.read_text())


    async def start(self, token: str):
        await self.initialize_database()
        await super().start(token)

    async def logout(self):
        await self.http_session.close()
        await self.db.close()
        await super().logout()

    def load_extensions(self):
        for ext in pkgutil.walk_packages(exts.__path__, "bot.exts."):
            if not ext.ispkg:
                self.load_extension(ext.name)
