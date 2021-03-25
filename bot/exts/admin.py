from datetime import datetime
import typing as t

import discord
from discord.ext import commands

from bot.exts.command import command, group, example


class Administration(commands.Cog):
    """A category for administrative commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.check_any(
        commands.has_permissions(administrator=True), commands.is_owner()
    )
    @group(name="prefix", invoke_without_command=True, case_insensitive=True)
    @example(
        """
    <prefix>prefix !
    <prefix>prefix change !
    <prefix>prefix insensitive true
    """
    )
    async def _prefix(self, ctx: commands.Context, prefix: str = None):
        """A group of commands for managing your guild's prefix.

        If no subcommand is invoked and you passed in a prefix then the prefix will be changed
        to that prefix. So `<prefix>prefix "bot "` would be the same as `<prefix>prefix change "bot "`"""
        if prefix is not None:
            return await self._change(ctx, prefix)
        await ctx.send_help(ctx.command)

    @_prefix.command(name="change")
    @example(
        """
    <prefix>prefix change !
    """
    )
    async def _change(self, ctx: commands.Context, prefix: str):
        """Changes the prefix for your server.

        NOTE: If you want to have spaces in your prefix, use quotes around the prefix
        Example: `{prefix}prefix change "bot "`"""
        if len(prefix) > 10:
            return await ctx.send("Your prefix can't be that long!")

        elif len(prefix) == 0:
            return await ctx.send("Your prefix cannot be nothing.")

        async with self.bot.db.acquire() as connection:
            guild = await connection.fetchrow(
                "SELECT * FROM guilds WHERE guild_id = $1", ctx.guild.id
            )
            if guild:
                await connection.execute(
                    "UPDATE guilds SET prefix = $1 WHERE guild_id = $2",
                    prefix,
                    ctx.guild.id,
                )
            else:
                await connection.execute(
                    "INSERT INTO guilds (guild_id, prefix) VALUES ($1, $2)",
                    ctx.guild.id,
                    prefix,
                )
            self.bot.dispatch('prefix_change')
        embed = discord.Embed(
            title=f"Set prefix to: {prefix}",
            colour=discord.Colour.green(),
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)

    @_prefix.command(
        name="insensitive", aliases=("case_insensitive", "caseinsensitive")
    )
    @example(
        """
    <prefix>prefix insensitive on
    <prefix>prefix case_insensitive disable
    """
    )
    async def _insensitive_prefix(self, ctx: commands.Context, true_or_false: bool):
        """Sets your prefix to case insensitive if you sent True and case sensitive if set to False.

        Prefixes are case sensitive by default."""
        async with self.bot.db.acquire() as connection:
            guild = await connection.fetchrow(
                "SELECT * FROM guilds WHERE guild_id = $1", ctx.guild.id
            )
            if guild is not None and guild["prefix"] is not None:
                await connection.execute(
                    "UPDATE guilds SET insensitive = $1 WHERE guild_id = $2",
                    true_or_false,
                    ctx.guild.id,
                )
            else:
                return await ctx.send("You didn't set your prefix yet!")
        embed = discord.Embed(
            title=f"Set prefix to case {'in' * int(true_or_false)}sensitive",
            colour=discord.Colour.green(),
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)

    @commands.has_permissions(manage_channels=True)
    @command(name="slow_mode", aliases=("slowmode", "sm"))
    @example(
        """
    <prefix>slowmode 10
    <prefix>sm 0
    """
    )
    async def slow_mode(
        self, ctx: commands.Context, channel: t.Optional[discord.TextChannel], time: int
    ):
        """Changes the slowmode delay for the channel you specify, if channel isn't sepicified it will be the channel you invoked the command.

        You can also set it to 0 to reset the slowmode delay."""
        channel = channel or ctx.channel
        if time < 0:
            return await ctx.send("You can't have a negative slowmode delay!")
        await channel.edit(slowmode_delay=time)
        if time == 0:
            embed = discord.Embed(
                title="Channel slowmode delay has been reset!",
                colour=discord.Colour.green(),
                timestamp=datetime.utcnow(),
            )
        else:
            s = "" if time == 1 else "s"
            embed = discord.Embed(
                title=f"Channel slowmode delay has been set to {time} second{s}!",
                colour=discord.Colour.green(),
                timestamp=datetime.utcnow(),
            )
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)

    @commands.check_any(
        commands.has_permissions(administrator=True), commands.is_owner()
    )
    @command(name="levelup_messages", aliases=("level_messages", "levelmessages"))
    async def _level_up_messages(self, ctx: commands.Context, true_or_false: bool):
        """Enable or disable the messages that are set when a user levels up.

        You can give 'yes', 'y', 'true', 't', '1', 'enable', 'on' if you want it on,
        or 'no', 'n', 'false', 'f', '0', 'disable', 'off' if you want it off. Casing does not matter."""
        async with self.bot.db.acquire() as connection:
            guild = await connection.fetchrow(
                "SELECT * FROM guilds WHERE guild_id = $1", ctx.guild.id
            )
            if not guild:
                await connection.execute(
                    "INSERT INTO guilds (guild_id, level_up_messages) VALUES ($1, $2)",
                    ctx.guild.id,
                    true_or_false,
                )
            else:
                await connection.execute(
                    "UPDATE guilds SET level_up_messages = $1 WHERE guild_id = $2",
                    true_or_false,
                    guild["guild_id"],
                )
        embed = discord.Embed(
            description=f"**✅ Set level up messages to {'on' if true_or_false else 'off'}**"
        )
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Administration(bot))
    print("Loaded Administration")
