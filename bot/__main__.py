import asyncio

import asyncpg
from discord import AllowedMentions, Intents

from . import constants
from .bot import Bot
from .help_command import Help

db = asyncpg.create_pool(constants.DATABASE_URL)

intents = Intents.default()
intents.members = True
intents.typing = False
intents.voice_states = False

bot = Bot(
    db, intents=intents, allowed_mentions=AllowedMentions(everyone=False), help_command=Help()
)
bot.load_extensions()
bot.load_extension("jishaku")

if __name__ == '__main__':
    bot.loop.run_until_complete(bot.start(constants.BOT_TOKEN))