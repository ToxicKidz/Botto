from datetime import datetime
from operator import attrgetter
from os import getenv
import random

import discord
from discord.ext import commands

import aiohttp
from aiodog import Client
import asyncpraw, asyncprawcore

from bot.exts.command import command, example


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reddit = asyncpraw.Reddit(
            client_id=getenv("REDDIT_CLIENT_ID"),
            client_secret=getenv("REDDIT_CLIENT_SECRET"),
            user_agent="Botto by ToxicKidz",
        )
        self.dog_client = Client(getenv('DOG_API_KEY'), session=bot.http_session)

    @command()
    @example(
        """
    <prefix>say hello world!
    """
    )
    async def say(self, ctx: commands.Context, *, message: str):
        """Get the bot to say something for you..."""
        embed = discord.Embed(description=message, timestamp=datetime.utcnow())
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await ctx.send(embed=embed)

    @command()
    @example(
        """
    <prefix>meme
    """
    )
    async def meme(self, ctx: commands.Context):
        """Finds a random meme for you."""
        msg = await ctx.send("Looking for a random meme...")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://some-random-api.ml/meme") as response:
                data = await response.json()
        embed = discord.Embed(title=data["caption"], colour=0xFFFF00)
        embed.set_image(url=data["image"])
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await msg.edit(content="Found one!", embed=embed)

    @command(name="dog", aliases=("dogpic", "dog_pig"))
    @example(
        """
    <prefix>dog
    """
    )
    async def _dog_pic(self, ctx: commands.Context):
        msg = await ctx.send("Looking for a doggo...")
        images = await self.dog_client.get_images(order="random")
        image = images[0]

        embed = discord.Embed(title="Doggo! 🐶", colour=discord.Colour.blue(), url=image.url)


        embed.description = f"Breeds: {', '.join(map(attrgetter('name'), image.breeds))}"

        embed.set_image(url=image.url)
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )

        await msg.edit(content="Found one!", embed=embed)

    @commands.command(name="cat", aliases=("catpic", "cat_pic"))
    @example(
        """
    <prefix>dog
    """
    )
    async def _cat_pic(self, ctx: commands.Context):
        msg = await ctx.send("Looking for a kitty...")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://some-random-api.ml/img/cat") as response:
                data = await response.json()
        embed = discord.Embed(title="Kitty! 🐱", colour=discord.Colour.orange())
        embed.set_image(url=data["link"])
        embed.set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await msg.edit(content="Found one!", embed=embed)

    @command(name="randomcase", aliases=("random_case",))
    @example(
        """
    <prefix>randomcase youre stupid
    <prefix>randomcase i just didnt ask
    """
    )
    async def _random_case(
        self, ctx: commands.Context, *, message: commands.clean_content()
    ):
        """Send a message in casing to produce a funny message in random casing."""
        await ctx.message.reply(
            "".join(
                letter.lower() if random.randint(0, 1) == 0 else letter.upper()
                for letter in message
            )
        )

    @command(name="reddit")
    @example(
        """
    <prefix>reddit meme
    <prefix>reddit all
    """
    )
    async def _reddit(self, ctx: commands.Context, *, subreddit: str = None) -> None:
        """Get a random submission from a subreddit that you choose , if you don't provide a subreddit it will give a random post."""
        async with ctx.typing():
            if subreddit is not None:
                try:
                    subreddit = await self.reddit.subreddit(subreddit)
                except asyncprawcore.NotFound:
                    await ctx.send("Subreddit was not found.")
                submission = await subreddit.random()
                if ctx.guild and submission.over_18 and not ctx.channel.is_nsfw():
                    channel = discord.utils.find(
                        lambda c: c.is_nsfw(), ctx.guild.text_channels
                    )
                    if channel is None:
                        await ctx.send(
                            f"That was an nsfw submission, you can't see it here."
                        )
                        return
                    else:
                        await ctx.send(
                            f"That was an nsfw submission; maybe try again in {channel.mention}"
                        )
                        return
            else:
                while True:
                    subreddit = await self.reddit.subreddit("all")
                    submission = await subreddit.random()
                    if not submission.over_18:
                        break
            embed = discord.Embed(
                title=submission.title,
                url=submission.url,
                color=discord.Colour.orange(),
            )
            embed.set_author(
                name=f"r/{subreddit}",
                url=f"https://www.reddit.com/r/{subreddit}",
                icon_url="https://logodownload.org/wp-content/uploads/2018/02/reddit-logo-16.png",
            )
            embed.set_image(url=submission.url)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
    print("Loaded Fun")
