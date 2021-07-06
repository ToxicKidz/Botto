from contextlib import redirect_stdout
from io import StringIO
import json
from os import listdir, _exit as exit
from textwrap import indent
from traceback import format_exc
import typing as t

import discord
from discord.ext import commands

from bot.utils.converters import CodeBlockConverter, ExtensionConverter

from bot.command import group


class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    async def run_eval(code, env) -> str:
        try:
            exec(f"async def coro():\n{indent(code, '   ')}", env)
        except BaseException:
            return format_exc()
        output = StringIO()
        with redirect_stdout(output):
            try:
                ret = await env["coro"]()
            except BaseException:
                return f"{output.getvalue()}\n{format_exc()}"
        return str(ret) or output.getvalue()

    @group()
    @commands.is_owner()
    async def owner(self, ctx: commands.Context):
        """Commands limited to this bot's owner."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @owner.command(name='eval')
    async def _eval(self, ctx: commands.Context, *, code: CodeBlockConverter):
        code = code[-1]
        env = {
            "ctx": ctx,
            "author": ctx.author,
            "bot": ctx.bot,
            "guild": ctx.guild,
            "channel": ctx.channel,
            "command": ctx.command,
            "discord": discord,
            "commands": commands,
        }
        output = await self.run_eval(code, env)
        output = output.replace('`', '`\u200B')
        await ctx.send(f"```py\n{output}\n```")

    @owner.command()
    async def load(self, ctx: commands.Context, ext: t.Union[ExtensionConverter, str]):
        """Load one extension, or use "*" to reload all of them."""
        exts = []
        if ext == "*":
            for file in listdir('bot/exts'):
                if file.endswith('py') and file not in ('__init__.py', 'command.py'):
                    ext = f"bot.exts.{file[:-3]}"
                    if ext in self.bot.extensions:
                        continue
                    exts.append(f"bot.exts.{file[:-3]}")
        else:
            exts.append(ext)

        if 'jishaku' not in self.bot.extensions:
            exts.append('jishaku')

        msg = await ctx.send(f"Loading extension{('s', '')[len(exts) == 1]}...")
        counter = failed =  skipped = 0

        for ext in exts:
            try:
                self.bot.load_extension(ext)
                counter += 1
                string = msg.content
                string += f"\n\U0001f4e5 `{ext}`"
                await msg.edit(content=string)
            except commands.ExtensionAlreadyLoaded:
                skipped += 1
            except commands.ExtensionError:
                failed += 1
                string = msg.content
                string += f"\n\u274c `{ext}`"
                await msg.edit(content=string)
        string = f"Loaded `{counter}` extensions{', ' if any((skipped, failed)) else '.'}"
        if failed:
            string +=  f"`{failed}` failed{' out of `{len(exts)}` extensions.' if not skipped else ', '}"
        if skipped:
            string += f"and skipped `{skipped}` out of `{len(exts)}` extensions."
        await ctx.send(content=string)
        
    @owner.command()
    async def unload(self, ctx: commands.Context, ext: t.Union[ExtensionConverter, str]):
        """Unload an extension. If `*` is used then it will unload all extensions except this one (owner)."""
        exts = []
        if ext == "*":
            for file in listdir('bot/exts'):
                if file.endswith('py') and file not in ('__init__.py', 'command.py', 'owner.py'):
                    ext = f"bot.exts.{file[:-3]}"
                    if ext not in self.bot.extensions:
                        continue
                    exts.append(f"bot.exts.{file[:-3]}")
        else:
            exts.append(ext)

        if 'jishaku' not in self.bot.extensions:
            exts.append('jishaku')

        msg = await ctx.send(f"Unloading extension{('s', '')[len(exts) == 1]}...")
        counter = failed =  skipped = 0

        for ext in exts:
            try:
                self.bot.unload_extension(ext)
                counter += 1
                string = msg.content
                string += f"\n\U0001f4e4 `{ext}`"
                await msg.edit(content=string)

            except commands.ExtensionError:
                failed += 1
                string = msg.content
                string += f"\n\u274c `{ext}`"
                await msg.edit(content=string)
        string = f"Unloaded `{counter}` extensions{', ' if any((skipped, failed)) else '.'}"
        if failed:
            string +=  f"`{failed}` failed out of `{len(exts)}` extensions."
        await ctx.send(content=string)


    @owner.command()
    async def reload(self, ctx: commands.Context, ext: t.Union[ExtensionConverter, str]):
        """Reload one extension, or use "*" to reload all of them."""
        exts = []
        if ext == "*":
            for file in listdir('bot/exts'):
                if file.endswith('py') and not file in ('__init__.py', 'command.py'):
                    ext = f"bot.exts.{file[:-3]}"
                    if ext not in self.bot.extensions:
                        continue
                    exts.append(f"bot.exts.{file[:-3]}")
        else:
            exts.append(ext)

        if 'jishaku' in self.bot.extensions and len(exts) - 1:
            exts.append('jishaku')

        msg = await ctx.send(f"Reoading extension{('s', '')[len(exts) == 1]}...")
        counter = failed =  skipped = 0

        for ext in exts:
            try:
                self.bot.reload_extension(ext)
                counter += 1
                string = msg.content
                string += f"\n\U0001f501 `{ext}`"
                await msg.edit(content=string)

            except commands.ExtensionNotLoaded:
                try:
                    self.bot.load_extension(ext)
                except commands.ExtensionError:
                    failed += 1
                    string = msg.content
                    string += f"\n\u274c `{ext}`"
                    await msg.edit(content=string)    
                else:
                    counter += 1
                    string = msg.content
                    string += f"\n\U0001f4e5 `{ext}`"
                    await msg.edit(content=string)

            except commands.ExtensionError:
                failed += 1
                string = msg.content
                string += f"\n\u274c `{ext}`"
                await msg.edit(content=string)
        string = f"Reloaded `{counter}` extensions{', ' if any((skipped, failed)) else '.'}"
        if failed:
            string +=  f"`{failed}` failed out of `{len(exts)}` extensions."

        await ctx.send(content=string)

    @owner.group(name="status")
    async def status_group(self, ctx: commands.Context):
        """Change the bot's activity to Playing, Streaming, Watching, or Listening with these subcommands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @status_group.command(name="playing")
    async def _playing(self, ctx: commands.Context, *, text: str):
        """Change the bot's activity to `Playing` with the text you give."""
        await self.bot.change_presence(activity=discord.Game(text))
        await ctx.send(
            embed=discord.Embed(
            title="Successfully changed status to Playing.",
            colour=discord.Colour.green()
            )
        )

    @status_group.command(name="streaming")
    async def _streaming(self, ctx: commands.Context, url: str, *, text: str):
        """Change the bot's activity to `Streaming` with the text you give."""
        await self.bot.change_presence(activity=discord.Streaming(name=text, url=url))
        await ctx.send(
            embed=discord.Embed(
            title="Successfully changed status to Streaming.",
            colour=discord.Colour.green()
            )
        )

    @status_group.command(name="listening")
    async def _listening(self, ctx: commands.Context, *, text: str):
        """Change the bot's activity to `Listening` with the text you give."""
        await self.bot.change_presence(
            activity=discord.Activity(name=text, type=discord.ActivityType.listening)
            )

        await ctx.send(
            embed=discord.Embed(
            title="Successfully changed status to Listening.",
            colour=discord.Colour.green()
            )
        )

    @status_group.command(name="watching")
    async def _watching(self, ctx: commands.Context, *, text: str):
        """Change the bot's activity to `Watching` with the text you give."""
        await self.bot.change_presence(
            activity=discord.Activity(name=text, type=discord.ActivityType.watching)
            )

        await ctx.send(
            embed=discord.Embed(
            title="Successfully changed status to Watching.",
            colour=discord.Colour.green()
            )
        )
    
    @owner.command()
    async def clear(self, ctx: commands.Context, limit: int):
        """
        Clear the bot's messages. 
        
        Checks the limit amout of messages and if it's sent by the bot then it gets deleted.
        """
        await ctx.channel.purge(limit=limit, check=lambda m: m.author == self.bot.user)

def setup(bot: commands.Bot):
    bot.add_cog(Owner(bot))
    print("Loaded Owner")
