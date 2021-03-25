import discord
from discord.ext import commands
from datetime import datetime, timedelta
from time import perf_counter

from bot.help_command import Help
from bot.exts.command import command, example


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
            connection.execute("SELECT 1")
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


def setup(bot):
    info_cog = Info(bot)
    bot.help_command.cog = info_cog
    bot.add_cog(info_cog)
    print("Loaded Info")
