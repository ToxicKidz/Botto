from datetime import datetime

import discord
from discord.ext import commands

from bot.bot import Bot

class ErrorHandler(commands.Cog):

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandOnCooldown):
            if ctx.bot.is_owner(ctx.author):
                await ctx.reinvoke()
                return

        await self.send_error_message(ctx, error)

    @staticmethod
    async def send_error_message(ctx, error: Exception):
        embed = discord.Embed(
            title="⚠️ Uh-Oh, an error happened.",
            description=error,
            timestamp = datetime.now(),
            colour=discord.Colour.red()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)

def setup(bot: Bot):
    bot.add_cog(ErrorHandler())
    print("Loaded ErrorHandler.")