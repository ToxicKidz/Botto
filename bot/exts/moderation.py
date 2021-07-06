import datetime
import typing as t
from time import time

import discord
from discord import User, Member, utils
from discord.ext import commands
from discord.ext.commands import Context
from discord.utils import find

from bot.utils.converters import TimeConverter
from bot.utils.decorators import role_hierarchy

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
    @commands.command(aliases=("permban", "permaban"))
    @role_hierarchy()
    async def ban(self, ctx: Context, member: User, *, reason: str = None) -> None:
        """Perminantly bans this member and will log it for the future."""
        await self.apply_ban(ctx, member, ctx.author, reason or "No reason provided")

    @commands.has_permissions(ban_members=True)
    @commands.command()
    @role_hierarchy()
    async def mute(self, ctx: Context, member: Member, *, reason: str = None):
        """Mutes the member so that they cannot send messages nor can they talk in vc."""
        await self.apply_mute(ctx, member, reason)

    @commands.has_permissions(ban_members=True)
    @commands.command()
    @role_hierarchy()
    async def unmute(self, ctx: Context, member: Member, *, reason: str = None):
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
        async with self.bot.db.acquire() as connection:
            await connection.execute(
                "INSERT INTO cases (case_id, guild_id, target, moderator, case_type, reason) "
                "VALUES ($1, $2, $3, $4, $5, $6)",
                next(self.bot.idgen), ctx.guild.id, member.id, mod.id, "ban", reason,
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
                "SELECT * FROM cases WHERE target = $1 AND expired = False AND case_type = $2",
                member.id, "mute"
            )

            if check_muted:
                await ctx.send("This person is already muted")
                return

            muted_role = await connection.fetchval(
                "SELECT muted_role FROM guilds WHERE guild_id = $1", ctx.guild.id
            )

            muted_role = ctx.guild.get_role(muted_role)

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

                await connection.execute(
                    "INSERT INTO guilds (guild_id, muted_role) VALUES ($1, $2) "
                    "ON CONFLICT DO UPDATE SET muted_role = $1",
                    muted_role.id,
                    ctx.guild.id
                )

            await member.add_roles(muted_role)
            await ctx.send(embed=discord.Embed(title=f"✅ {member} was muted."))
            await connection.execute(
                "INSERT INTO cases "
                "(case_id, guild_id, target, moderator, case_type, expires_at, reason)"
                "VALUES ($1, $2, $3, $4, $5, $6, $7)",
                case_id := next(self.bot.idgen),
                ctx.guild.id,
                member.id,
                ctx.author.id,
                member.name,
                ctx.author.name,
                "mute",
                expires_at,
                reason,
            )

            return case_id

    @commands.has_permissions(ban_members=True)
    @commands.command()
    @role_hierarchy()
    async def tempmute(
        self, 
        ctx: commands.Context,
        member: discord.Member,
        time: commands.Greedy[TimeConverter],
        *,
        reason: str = "No reason Provided"
    ):
        if not sum(time):
            await ctx.send("Please specify a valid time")
            return
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
