from discord.ext import commands
from random import randint
from discord.utils import find
import discord

from bot.exts.utils.pagination import PaginatedMenu, Source
from bot.exts.command import command, example

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cd_mapping = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.member
        )
        self.leveling_dict = {
            range(0, 100): 0,
            range(100, 255): 1,
            range(255, 475): 2,
            range(475, 770): 3,
            range(770, 1550): 4,
            range(1550, 1625): 5,
            range(1625, 2205): 6,
            range(2205, 2900): 7,
            range(2205, 2900): 8,
            range(2900, 3465): 9,
            range(3465, 4000): 10,
            range(4000, 5775): 11,
            range(5775, 7030): 12,
            range(7030, 8450): 13,
            range(8450, 10045): 14,
            range(10045, 11825): 15,
            range(11825, 13800): 16,
            range(13800, 15980): 17,
            range(15980, 18375): 18,
            range(18375, 20995): 19,
            range(20995, 26950): 20,
            range(26950, 30305): 21,
            range(30305, 33925): 22,
            range(33,925, 37820): 23,
            range(37,820, 42000 ): 24,
            range(42000, 46475): 25,
            range(42000, 51255): 26,
            range(51255, 56350): 27,
            range(56350, 61770): 28,
            range(61770, 67525): 29,
            range(67525, 73625): 30,
            range(73625, 80080): 31,
            range(80080, 86900): 32,
            range(86900, 94095): 33,
            range(94095, 101675): 34,
            range(101675, 109650): 35,
            range(109650, 118030): 36,
            range(118030, 126825): 37,
            range(126825, 136045): 38,
            range(136045, 145700): 39,
            range(145700, 155800): 40,
        }

    @commands.Cog.listener("on_message")
    async def level_up(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if message.content.startswith(self.bot.command_prefix(self.bot, message)):
            return
        bucket = self.cd_mapping.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if not retry_after:
            async with self.bot.db.acquire() as connection:
                member = await connection.fetchrow(
                    "SELECT * FROM member WHERE user_guild = $1",
                    [message.author.id, message.guild.id],
                )
                if member:
                    xp = member["xp"]
                    if xp:
                        member_xp = xp + randint(15, 25)
                        level = find(lambda x: xp in x[0], self.leveling_dict.items())
                        new_level = find(
                            lambda x: member_xp in x[0], self.leveling_dict.items()
                        )
                        if new_level[1] is not None and new_level[1] > level[1]:
                            self.bot.dispatch("level_up", new_level[1], message)
                        await connection.execute(
                            "UPDATE member SET xp = $1 WHERE user_guild = $2",
                            member_xp,
                            [message.author.id, message.guild.id],
                        )
                    else:
                        await connection.execute(
                            "UPDATE member SET xp = $1 WHERE user_guild = $2",
                            randint(15, 25),
                            [message.author.id, message.guild.id],
                        )
                else:
                    await connection.execute(
                        "INSERT INTO member (user_guild, xp) VALUES ($1, $2)",
                        [message.author.id, message.guild.id],
                        randint(15, 25),
                    )
                    member = await connection.fetchrow(
                        "SELECT * FROM member WHERE user_guild = $1",
                        [message.author.id, message.guild.id],
                    )
                member_messages = member["messages"]
                if member_messages:
                    await connection.execute(
                        "UPDATE member SET messages = messages + 1 WHERE user_guild = $1",
                        member["user_guild"],
                    )
                else:
                    await connection.execute(
                        "UPDATE member SET messages = 1 WHERE user_guild = $1",
                        member["user_guild"],
                    )

    @commands.Cog.listener()
    async def on_level_up(self, level: int, message: discord.Message):
        async with self.bot.db.acquire() as connection:
            guild = await connection.fetchrow(
                "SELECT * FROM guilds WHERE guild_id = $1", message.guild.id
            )
            if guild["level_up_messages"]:
                await message.channel.send(
                    f"Good job {message.author.mention}, you leveled up to level {level}!"
                )

    @commands.guild_only()
    @example(
    '''<prefix>rank @some_preson
       <prefix>level
    '''
    )
    @command(name="rank", aliases=("level",))
    async def _rank(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        if member.bot:
            return await ctx.send("Bots don't have levels!")
        async with self.bot.db.acquire() as connection:
            db_member = await connection.fetchrow(
                "SELECT * FROM member WHERE user_guild = $1",
                [member.id, member.guild.id],
            )
            if not db_member:
                embed = discord.Embed(
                    title="Error",
                    description=f"{member.mention} hasn't sent a message yet.",
                    colour=discord.Colour.red(),
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
                )
                return await ctx.send(embed=embed)
            if not db_member["xp"]:
                embed = discord.Embed(
                    title="Error",
                    description="You haven't sent a message yet.",
                    colour=discord.Colour.red(),
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
                )
                return await ctx.send(embed=embed)
            rank = (
                await connection.fetch(
                    "SELECT * FROM member WHERE array_position(user_guild, $1) = 2",
                    ctx.guild.id,
                )
            ).index(db_member) + 1
            level = find(lambda x: db_member["xp"] in x[0], self.leveling_dict.items())
            embed = discord.Embed(
                title=f"{member.display_name}'s level",
                description=f"""**Rank:** {rank}\n**Level: **{level[1]}
                                            **XP: **{db_member['xp'] - level[0].start}/{level[0].stop - level[0].start} """,
                colour=discord.Colour.green(),
            )
            await ctx.send(embed=embed)

    @commands.guild_only()
    @example("<prefix>leaderboard")
    @command(name="leaderboard", aliases=("levels",))
    async def _leaderboard(self, ctx: commands.Context):
        async with self.bot.db.acquire() as connection:
            rankings = await connection.fetch(
                "SELECT * FROM member WHERE array_position(user_guild, $1) = 2 AND xp IS NOT NULL ORDER BY xp DESC",
                ctx.guild.id,
            )
            embed = discord.Embed(
                title=f"Rankings for {ctx.guild}", colour=discord.Colour.green()
            )
            for rank, record in enumerate(rankings, start=1):
                user_guild = record["user_guild"]
                messages = record["messages"]
                level = find(lambda x: record["xp"] in x[0], self.leveling_dict.items())
                try:
                    embed.add_field(
                        name=f"{rank}. {ctx.guild.get_member(user_guild[0]).display_name}",
                        value=f"{messages} Messages."
                        )

                    embed.add_field(name=f"Level {level[1]}",
                                    value=(
                                           f"{record['xp'] - level[0].start}/{level[0].stop - level[0].start}"
                                           f" and {record['xp']} total XP."
                                           )
                                   )
                    embed.add_field(name="\u200b", value="\u200b")

                except AttributeError:
                    pass
        source = Source.make_pages(embed, 5)

        menu = PaginatedMenu(source, clear_reactions_after=True)

        await menu.start(ctx, wait=True)


def setup(bot):
    bot.add_cog(Leveling(bot))
    print("Loaded Leveling")
