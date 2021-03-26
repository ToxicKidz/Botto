import discord
from discord.ext import commands

from datetime import datetime, timedelta
from inspect import getsourcelines, getsourcefile
from pathlib import Path
from time import perf_counter
from types import ModuleType
import typing as t


from bot.exts.command import command, example

GITHUB_REPO_URL = "https://github.com/ToxicKidz/Botto"

MIN_EXTENSION_LENGTH = 4 

# Source command from vcokltfre/Magoji

class SourceConverter(commands.Converter):
    """A Converter that converts a string to a Command, Cog or Extension."""

    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> t.Union[commands.Command, commands.Cog, ModuleType]:
        if command := ctx.bot.get_command(argument):
            if command.name == "help":
                return ctx.bot.help_command
            return command

        if cog := ctx.bot.get_cog(argument):
            return cog

        if len(argument[:-3]) < MIN_EXTENSION_LENGTH:
            raise commands.BadArgument("Not a valid Command, Cog nor Extension.")

        if (
            extension := discord.utils.find(
                lambda ext: ext[0].endswith(argument[:-3]), ctx.bot.extensions.items()
            )
        ) and argument.endswith(".py"):
            return extension[1]

        raise commands.BadArgument("Not a valid Command, Cog nor Extension.")


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @example("<prefix>ping")
    @command(name="ping")
    async def _ping(self, ctx):
        """See how fast the bot can repond to you."""
        delay = datetime.utcnow() - ctx.message.created_at
        delay = round(delay.total_seconds() * 1000)

        async with self.bot.db.acquire() as connection:
            now = perf_counter()
            await connection.execute("SELECT 1")
            db_delay = (perf_counter() - now) * 1000
        embed = discord.Embed(
            title="🏓 Pong!",
            description=(f"Bot latency: `{round(self.bot.latency * 1000)}ms`\n"
                         f"Command Processing Time: `{delay}ms`\n"
                         f"Database Delay: `{round(db_delay)}ms`"
                        ),               
        )
        await ctx.send(embed=embed)

    @example("<prefix>server")
    @command(name="server", aliases=("server_info", "serverinfo"))
    async def _server(self, ctx: commands.Context):
        """Find information about the server you're in."""
        guild_created_at = ctx.guild.created_at.strftime(
            f"%A, %B %-d, %Y at %-I:%M {'A' if ctx.guild.created_at.hour < 12 else 'P'}M UTC"
        )
        embed = discord.Embed(
            title=f"Info for server {ctx.guild}",
            colour=discord.Colour.blurple(),
            timestamp=datetime.utcnow(),
        )
        embed.description = f"""**Created at:** {guild_created_at}\n**Server Owner:** {ctx.guild.owner}\n**Emojis:** {len(ctx.guild.emojis)}
                                **Member Count:** {ctx.guild.member_count}\n**Server Region:** {ctx.guild.region}\n**Boost Level:** {ctx.guild.premium_tier}"""
        embed.add_field(
            name=f"Channels: {len(ctx.guild.channels)}",
            value=(f"Text Channels: {len(ctx.guild.text_channels)}\nVoice Channels: {len(ctx.guild.voice_channels)}"
                  f"Categories: {len(ctx.guild.categories)}"
            ),
        )
        if ctx.guild.features:
            guild_features = ", ".join(
                feature.replace("_", " ").title() for feature in ctx.guild.features
            )
            embed.add_field(
                name=f"{len(ctx.guild.features)} Feature{'' if len(ctx.guild.features) == 1 else 's'}",
                value=guild_features,
            )
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @example("<prefix>about")
    @command(name="about", aliases=("botinfo", "bot_info"))
    async def _about(self, ctx: commands.Context):
        """See info about the bot."""
        owner = ctx.bot.get_user(506618674921340958)
        embed = discord.Embed(
            title="About this bot.",
            description=ctx.bot.description,
            colour=discord.Colour.blue(),
            timstamp=datetime.utcnow(),
        )
        uptime = self.get_uptime(ctx.message.created_at - self.bot.start_time)
        embed.set_author(name=str(ctx.bot.user), icon_url=ctx.me.avatar_url)
        embed.add_field(name="Owner", value=f"{owner} \n**ID:** {owner.id}")
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="Made with discord.py", value="\u200b", inline=False)
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)

    @staticmethod
    def get_uptime(time: timedelta) -> str:
        seconds = time.total_seconds()
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)
        months, weeks = divmod(weeks, 4)
        string = ""
        if months:
            string += f"{round(months)} month{'' if months == 1 else 's'}"
        if weeks:
            string += f"{', ' if string else ''}{round(weeks)} week{'' if weeks == 1 else 's'}"
        if days:
            string += (
                f"{', ' if string else ''}{round(days)} day{'' if days == 1 else 's'}"
            )
        if hours:
            string += f"{', ' if string else ''}{round(hours)} hour{'' if hours == 1 else 's'}"
        if minutes:
            string += f"{', ' if string else ''}{round(minutes)} minute{'' if minutes == 1 else 's'}"
        if seconds:
            string += f"{', ' if string else ''}{round(seconds)} second{'' if seconds == 1 else 's'}"
        return string or "Just Now!"

    @commands.command(aliases=("src", "github", "git"), invoke_without_command=True)
    async def source(
        self, ctx: commands.Context, *, source_item: SourceConverter = None
    ) -> None:
        """Shows the github repo for this bot, include a command, cog, or extension to got to that file.
        If you want the source for an extension, it must end with `.py`."""
        if source_item is None:
            embed = discord.Embed(
                title="Botto's Github Repository",
                description=f"[Here's the github link!]({GITHUB_REPO_URL})",
                colour=0x87CEEB,
            )
            await ctx.send(embed=embed)
            return
        embed = self.build_embed(source_item)
        await ctx.send(embed=embed)


    def get_github_url(self, source_item):
        if isinstance(source_item, (commands.HelpCommand, commands.Cog)):
            src = type(source_item)
            filename = getsourcefile(src)
        elif isinstance(source_item, commands.Command):
            src = source_item.callback.__code__
            filename = src.co_filename
        elif isinstance(source_item, ModuleType):
            src = source_item
            filename = src.__file__

        lines, first_line_no = self.get_source_code(source_item)
        lines_extension = ""
        if first_line_no:
            lines_extension = f"#L{first_line_no}-L{first_line_no+len(lines)-1}"

        file_location = Path(filename).relative_to(Path.cwd()).as_posix()

        url = f"{GITHUB_REPO_URL}/blob/master/{file_location}{lines_extension}"

        return url, file_location, first_line_no or None

    def get_source_code(
        self, source_item: t.Union[commands.Command, commands.Cog, ModuleType]
    ) -> t.Tuple[str, int]:
        if isinstance(source_item, ModuleType):
            source = getsourcelines(source_item)
        elif isinstance(source_item, (commands.Cog, commands.HelpCommand)):
            source = getsourcelines(type(source_item))
        elif isinstance(source_item, commands.Command):
            source = getsourcelines(source_item.callback)

        return source

    def build_embed(self, source_object) -> discord.Embed:
        """Build embed based on source object."""
        url, location, first_line = self.get_github_url(source_object)

        if isinstance(source_object, commands.HelpCommand):
            title = "Help Command"
            help_cmd = self.bot.get_command("help")
            description = help_cmd.help
        elif isinstance(source_object, commands.Command):
            description = source_object.short_doc
            title = f"Command: {source_object.qualified_name}"
        elif isinstance(source_object, ModuleType):
            title = f"Extension: {source_object.__name__}.py"
            description = discord.Embed.Empty
        else:
            title = f"Cog: {source_object.qualified_name}"
            description = source_object.description

        embed = discord.Embed(title=title, description=description, colour=0x87CEEB)
        embed.add_field(name="Source Code", value=f"[Here's the Github link!]({url})")
        line_text = f":{first_line}" if first_line else ""
        embed.set_footer(text=f"{location}{line_text}")

        return embed


def setup(bot):
    info_cog = Info(bot)
    bot.help_command.cog = info_cog
    bot.add_cog(info_cog)
    print("Loaded Info")
