import difflib
import traceback
from datetime import datetime


import discord
from discord.ext import commands

from bot.bot import Bot

class ErrorHandler(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        error: Exception = getattr(error, 'original', error)

        if not isinstance(error, commands.CommandError):
            traceback.print_exception(type(error), error, error.__traceback__)
            return

        if isinstance(error, commands.CommandOnCooldown):
            if ctx.bot.is_owner(ctx.author):
                await ctx.reinvoke()
                return
        elif isinstance(error, commands.CommandNotFound):
            await self.send_close_match(ctx)
            return

        await self.send_error_message(ctx, error)

    @staticmethod
    async def send_error_message(ctx: commands.Context, error: Exception):
        embed = discord.Embed(
            title="⚠️ Uh-Oh, an error happened.",
            description=str(error),
            timestamp = datetime.now(),
            colour=discord.Colour.red()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)
    
    @staticmethod
    async def send_close_match(ctx):
        similar_command_name = difflib.get_close_matches(ctx.invoked_with, map(str, ctx.bot.commands))
        if not similar_command_name:
            return

        similar_command = ctx.bot.get_command(similar_command_name[0])

        if not similar_command:
            return
        try:
            if not await similar_command.can_run(ctx):
                return
        except commands.CommandError:
            return
        
        embed = discord.Embed(
            title="Did you mean...",
            description=f"{ctx.prefix}{similar_command_name[0]}",
            colour=discord.Colour.red()
        )
        await ctx.send(embed=embed)

def setup(bot: Bot):
    bot.add_cog(ErrorHandler(bot))
    print("Loaded ErrorHandler")