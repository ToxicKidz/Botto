import asyncio
import datetime
from time import time
import traceback
import typing as t

import discord
from discord import Member, utils
from discord.ext import commands, tasks
from discord.ext.commands import Context, Greedy
from discord.utils import get, find

from bot.exts.utils.converters import TimeConverter

class IDGenerator:
    def __init__(self):
        self.wid = 0
        self.inc = 0

    def __next__(self):
        t = round(time() * 1000) - 1609459200000
        self.inc += 1
        return (t << 14) | (self.wid << 6) | (self.inc % 2 ** 6)

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        bot.loop.create_task(self.setup_timed_events())

    @commands.has_permissions(ban_members=True)
    @commands.command(name="ban", aliases=("permban", "permaban"))
    async def _ban(self, ctx: Context, member: Member, *, reason: str = None) -> None:
        """Perminantly bans this member and will log it for the future."""
        await self.apply_ban(ctx, member, ctx.author)

    @commands.has_permissions(ban_members=True)
    @commands.command(name="mute")
    async def _mute(self, ctx: Context, member: Member, *, reason: str = None):
        """Mutes the member so that they cannot send messages nor can they talk in vc."""
        await self.apply_mute(ctx, member, reason)

    @commands.has_permissions(ban_members=True)
    @commands.command(name="unmute")
    async def _unmute(self, ctx: Context, member: Member, *, reason: str = None):
        async with self.bot.db.acquire() as connection:
            guild = await connection.fetchrow(
                "SELECT * FROM guilds WHERE guild_id = $1", ctx.guild.id
            )
            if not guild:
                await ctx.send("No mutes found here.")
            muted_role = ctx.guild.get_role(guild["muted_role"])
            if muted_role:
                if muted_role in member.roles:
                    await member.remove_roles(muted_role)
                    await connection.execute(
                        "UPDATE cases SET expired = True WHERE userid = $1", member.id
                    )
                    await ctx.send(embed=discord.Embed(title=f"✅ {member} was unmuted."))
                else:
                    await ctx.send(
                        "This person is either not muted or they have the wrong muted role for this bot."
                    )

            else:
                muted_role = find(
                    lambda role: role.name.lower() == "muted", ctx.guild.roles
                )
                if muted_role and muted_role in member.roles:
                    await member.remove_roles(muted_role)
                    await ctx.send(
                        embed=discord.Embed(title=f"✅ {member} was unmuted.")
                    )
                else:
                    await ctx.send("This person is not muted.")

    async def apply_ban(
        self, ctx: Context, member: Member, mod: Member, reason: str = None
    ):
        try:
            await ctx.guild.ban(member, reason=reason)
        except discord.Forbidden:
            return await ctx.send(f"Sorry {mod.mention}, I can't ban that user!")
        async with self.bot.acquire() as connection:
            await connection.execute(
                ("INSERT INTO cases (id, guildid, userid, modid, username, modname, case_type, case_data)"
                 "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"),
                next(self.bot.idgen), ctx.guild.id, member.id, mod.id,
                 member.name, mod.name, "ban", reason,
            )

    async def apply_mute(
        self,
        ctx: Context,
        member: Member,
        reason: str,
        expires_at: t.Optional[datetime.datetime] = None
    ):
        async with self.bot.db.acquire() as connection:
            check_muted = await connection.fetchrow(
                "SELECT * FROM cases WHERE userid = $1 and expired = False", member.id
            )
            if check_muted:
                await ctx.send("This person is already muted")
                return
            muted_role = await connection.fetchrow(
                "SELECT muted_role FROM guilds WHERE guild_id = $1", (ctx.guild.id)
            )

            if not muted_role:
                muted_role = get(ctx.guild.roles, name="Muted") or get(
                    ctx.guild.roles, name="muted"
                )
                if not muted_role:
                    muted_permissions = discord.Permissions(
                        send_messages=False, speak=False
                    )
                    muted_role = await ctx.guild.create_role(
                        name="Muted",
                        permissions=muted_permissions,
                        colour=0x808080,
                        reason="New Muted role for mods.",
                    )
                    muted_role_position = next(
                        (role.position - 1)
                        for index, role in enumerate(ctx.guild.roles)
                        if role.permissions.manage_members
                        or index + 1 == len(ctx.guild.roles)
                    )
                    await muted_role.edit(position=muted_role_position)
                    await ctx.send(embed=discord.Embed(title=f"✅ {member} was muted."))
                guild = await connection.fetchrow(
                    "SELECT * FROM guilds WHERE guild_id = $1", ctx.guild.id
                )
                if guild:
                    await connection.execute(
                        "UPDATE guilds SET muted_role = $1 WHERE guild_id = $2",
                        muted_role.id,
                        ctx.guild.id,
                    )
                else:
                    await connection.execute(
                        "INSERT INTO guilds (guild_id, muted_role) VALUES ($1, $2)",
                        ctx.guild.id,
                        muted_role.id,
                    )
            else:
                muted_role = ctx.guild.get_role(muted_role["muted_role"])
                if not muted_role:
                    muted_role = discord.utils.find(
                        lambda role: role.name.lower() == "muted", ctx.guild.roles
                    )
                    if muted_role:
                        await connection.execute(
                            "UPDATE guilds SET muted_role = $1 WHERE guild_id = $2",
                            muted_role,
                            ctx.guild.id,
                        )
                    else:
                        muted_permissions = discord.Permissions(
                            send_messages=False, speak=False
                        )
                        muted_role = await ctx.guild.create_role(
                            name="Muted",
                            permissions=muted_permissions,
                            colour=0x808080,
                            reason="New Muted role for mods.",
                        )
                        muted_role_position = next(
                            (role.position - 1)
                            for index, role in enumerate(ctx.guild.roles)
                            if role.permissions.ban_members
                            or index + 1 == len(ctx.guild.roles)
                        )
                        await muted_role.edit(position=muted_role_position)
                        guild = await connection.fetchrow(
                            "SELECT * FROM guilds WHERE guild_id = $1", ctx.guild.id
                        )
                        if guild:
                            await connection.execute(
                                """UPDATE guilds SET muted_role = $1, 
                                           WHERE guild_id = $2""",
                                muted_role.id,
                                ctx.guild.id,
                            )
                        else:
                            await connection.execute(
                                """INSERT INTO guilds (guild_id, muted_role)
                                                        VALUES ($1, $2)""",
                                ctx.guild.id,
                                muted_role.id,
                            )
            await member.add_roles(muted_role)
            await ctx.send(embed=discord.Embed(title=f"✅ {member} was muted."))
            await connection.execute(
                "INSERT INTO cases (id, guildid, userid, modid, username, modname, case_type, case_data, expires_at) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                case_id:=next(self.bot.idgen),
                ctx.guild.id,
                member.id,
                ctx.author.id,
                member.name,
                ctx.author.name,
                "mute",
                reason,
                expires_at,
            )
            return case_id

    @commands.command()
    async def tempmute(self, 
                       ctx: commands.Context,
                       member: discord.Member,
                       time: commands.Greedy[TimeConverter],
                       *,
                       reason: str = "No reason Provided"
                       ):
        expires_at = datetime.datetime.now() + datetime.timedelta(seconds=sum(time))
        ret = await self.apply_mute(ctx, member, reason, expires_at)
        await self.preform_unmute(member, expires_at=expires_at, case_id=ret)


    async def preform_unmute(self,
                             member: discord.Member,
                             *,
                             muted_role: t.Optional[discord.Role] = None,
                             expires_at: datetime.datetime,
                             case_id: int
                             ):
        await utils.sleep_until(expires_at)
        try:
            if not muted_role:
                muted_role = discord.utils.find(lambda r: r.name.lower() == 'muted', member.roles)
            await member.remove_roles(muted_role)
        except Exception:
            pass
        async with self.bot.db.acquire() as connection:
            await connection.execute("UPDATE cases SET expired = 'True' WHERE id = $1", case_id)
    
    async def preform_unban(self, user: int, expires_at: datetime.datetime, case_id: int, guild: discord.Guild):
        await discord.utils.sleep_until(expires_at)
        try:
            await guild.unban(discord.Object(user))
        except Exception:
            pass

        async with self.bot.db.acquire() as connection:
            await connection.execute("UPDATE cases SET expired = 'True' WHERE id = $1", case_id)

    async def setup_timed_events(self):
        await self.bot.wait_until_ready()
        async with self.bot.db.acquire() as connection:
            mutes = await connection.fetch(
                "SELECT * FROM cases WHERE case_type = 'mute' AND expires_at IS NOT NULL"
            )
            bans = await connection.fetch(
                "SELECT * FROM cases WHERE case_type = 'ban' AND expires_at IS NOT NULL"
            )
            for mute in mutes:
                db_guild = await connection.fetchrow("SELECT * FROM guilds WHERE guild_id = $1", mute["guildid"])
                guild = mute["guildid"]
                guild = self.bot.get_guild(guild)
                member = guild.get_member(mute["userid"])
                role = guild.get_role(db_guild["muted_role"])
                await self.preform_unmute(member, muted_role=role,
                                          expires_at=mute["expires_at"], case_id=mute["id"])
            for ban in bans:
                guild = ban["guildid"]
                guild = self.bot.get_guild(guild)
                await self.preform_unban(ban["user"], ban["expires_at"], ban["id"], guild)

def setup(bot):
    bot.add_cog(Moderation(bot))
    bot.idgen = IDGenerator()
    print("Loaded cogs.Moderation")
