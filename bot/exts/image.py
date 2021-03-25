import asyncio
from io import BytesIO
import typing as t

import discord
from discord.ext import commands
import PIL
from PIL import ImageOps

from bot.exts.command import command, example
from bot.exts.utils.converters import ImageConverter



class Image(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def invert_image(image: BytesIO) -> BytesIO:
        image = PIL.Image.open(image)
        inverted_image = ImageOps.invert(image.convert(mode="RGB"))
        bytes_io = BytesIO()
        inverted_image.save(bytes_io, "WEBP")
        return bytes_io

    @staticmethod
    def to_8bit(image: BytesIO) -> BytesIO:
        avatar = PIL.Image.open(image)
        avatar = avatar.convert("RGBA").resize((1024, 1024))
        eightbit = avatar.resize((32, 32), resample=PIL.Image.NEAREST).resize(
            (1024, 1024), resample=PIL.Image.NEAREST
        )
        eightbit = eightbit.quantize()
        bytes_io = BytesIO()
        eightbit.save(bytes_io, "WEBP")
        return bytes_io

    @command(aliases=("invertavatar", "invert_avatar"))
    @example(
        """
    <prefix>8bit @john doe
    <prefix>8-bit some-image-link.com
    """
    )
    async def invert(self, ctx: commands.Context, image: ImageConverter = None) -> None:
        """Invert the colours of your avatar or a member if you include one.

        You can also specify a link that leads to an image, or an attachment."""
        bytes_image = image or await ImageConverter().convert(ctx, image)
        bytes_image.seek(0)
        image = await self.bot.loop.run_in_executor(
            None, self.invert_image, bytes_image
        )
        image.seek(0)
        embed = discord.Embed(title="Inverted image.", colour=discord.Colour.green())
        file = discord.File(image, filename="inverted.webp")
        embed.set_image(url="attachment://inverted.webp")
        await ctx.send(file=file, embed=embed)

    @command(name="8bit", aliases=("8-bit", "8_bit"))
    @example(
        """
    <prefix>8bit @john doe
    <prefix>8-bit some-image-link.com
    """
    )
    async def _8bit(self, ctx: commands.Context, image: ImageConverter = None) -> None:
        """Turn your avatar or a member if you specify into a pixelated one.

        You can also specify a link that leads to an image, or an attachment."""
        bytes_image = image or await ImageConverter().convert(ctx, image)
        bytes_image.seek(0)
        eightbit = await self.bot.loop.run_in_executor(None, self.to_8bit, bytes_image)
        eightbit.seek(0)
        embed = discord.Embed(title="8bit Image!", colour=discord.Colour.orange())
        file = discord.File(eightbit, filename="8bit.webp")
        embed.set_image(url="attachment://8bit.webp")
        await ctx.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(Image(bot))
    print("Loaded Image")
