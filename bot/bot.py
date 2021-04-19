import asyncio
from datetime import datetime
import json
import os

import aiohttp
from dotenv import load_dotenv
import asyncpg

import discord
from discord.ext import commands

from .help_command import Help

load_dotenv()

async def run(token):
    description = "A useful bot for moderation, leveling, and more!."

    credentials = {
        "user": "owner",
        "password": os.getenv("DB_PASS"),
        "database": "owner",
        "host": "127.0.0.1",
    }

    extensions = (
        "moderation",
        "admin",
        "fun",
        "info",
        "level",
        "image",
        "games",
        "math",
        "owner",
        "custom_prefix",
        "misc",
        "error_handler",
    )

    db = await asyncpg.create_pool(**credentials)

    intents = discord.Intents.all()

    bot = Bot(db, description=description, intents=intents, help_command=Help(), allowed_mentions=discord.AllowedMentions(everyone=False))

    bot.start_time = datetime.now()

    bot.load_extension("jishaku")

    bot.load_extensions(*extensions)

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        await bot.logout()


class Bot(commands.Bot):
    def __init__(self, db: asyncpg.pool.Pool, **kwargs):
        self.db = db
        self.http_session = aiohttp.ClientSession()
        command_prefix = 'bot '
        super().__init__(command_prefix, **kwargs)

        with open("bot/setup.json") as f:
            self.setup_config = json.load(f)

    async def logout(self):
        await self.http_session.close()
        await self.db.close()
        await super().logout()

    def load_extensions(self, *extensions: str):
        for ext in extensions:
            self.load_extension(f"bot.exts.{ext}")

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        def check(reaction, user):
            return str(reaction.emoji) == "🔁" and user == after.author and \
                reaction.message == after

        before_ctx = await self.get_context(before)
        after_ctx = await self.get_context(after)
        if not after_ctx.command:
            return
        if (after_ctx.command.name in self.setup_config["whitelisted_commands"] or await self.is_owner(after.author)) \
        and before_ctx.command is after_ctx.command and after_ctx.command:
            try:
                await after.add_reaction("🔁")
                reaction, user = await self.wait_for("reaction_add", check=check, timeout=20)
                try:
                    await after.clear_reaction(reaction.emoji)
                except discord.HTTPException:
                    await after.remove_reaction(reaction.emoji, self.user)
                await self.process_commands(after)
            except asyncio.TimeoutError:
                await after.clear_reaction(reaction.emoji)

if __name__ == '__main__':
    asyncio.run(run(os.getenv("TOKEN")))
