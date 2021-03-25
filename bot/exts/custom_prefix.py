import discord
from discord.ext import commands
from discord.utils import find
from asyncpg import Record
import asyncio
import typing as t

from bot.bot import Bot

class CustomPrefix(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.default_prefix = 'bot '
        self.prefixes: t.Optional[t.List[Record]] = None

    def get_prefix(self, bot: commands.Bot, message: discord.Message):
        try:
            prefix = None
            if self.prefixes is not None:

                guild = find(
                    lambda record: record.get("guild_id") == message.guild.id,
                    self.prefixes,
                )
                if guild is not None:
                    if guild["insensitive"]:
                        if message.content.lower().startswith(guild["prefix"]):
                            prefix = message.content[: len(guild["prefix"])]
                    else:
                        prefix = guild["prefix"]
            if prefix is None:
                return self.default_prefix
            else:
                return prefix
        except AttributeError:
            return self.default_prefix

    @commands.Cog.listener()
    async def on_prefix_change(self):
        async with self.bot.db.acquire() as connection:
            self.prefixes = await connection.fetch(
                "SELECT * FROM guilds WHERE prefix IS NOT NULL"
            )

def setup(bot: Bot):
    cog = CustomPrefix(bot)

    bot.add_cog(cog)

    bot.command_prefix = cog.get_prefix

    print("Loaded CustomPrefix")