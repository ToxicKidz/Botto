import io
import os
import re
from typing import Optional, Tuple

from discord.ext import commands
from discord.ext.commands import Converter
from more_itertools import chunked

ESCAPE_REGEX = re.compile("[`\u202E\u200B]{3,}")
FORMATTED_CODE_REGEX = re.compile(
    r"```(?P<lang>[a-z+]+)?\s*" r"(?P<code>.*)" r"\s*" r"```", re.DOTALL | re.IGNORECASE
)
TIME_MAP = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 7,
    "mo": 60 * 60 * 24 * 30,
    "y": 60 * 60 * 24 * 365
}
TIME_REGEX = re.compile(rf"\d+({'|'.join(TIME_MAP)})")


class TimeConverter(Converter):
    def __init__(self):
        self.time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


    async def convert(self, ctx: commands.Context, time: str) -> int:
        if not any([time.endswith(i) for i in self.time_dict]):
            raise commands.BadArgument("Time needs to end with s/h/d/w")
        time = self.time_dict[time[-1]] * int(time[:-1])
        return time


class CodeBlockConverter(Converter):
    async def convert(self, ctx: commands.Context, code: str):

        match = FORMATTED_CODE_REGEX.search(code)
        if match:
            code = match.group("code")

        return match, code


class ImageConverter(Converter):
    async def convert(self, ctx, image: Optional[str], recursion=False) -> io.BytesIO:
        if not isinstance(image, str):
            if image is not None:
                raise commands.BadArgument("Image must be a str, or None.")
            else:
                if ctx.message.attachments:
                    bytes_image = await ctx.message.attachments[0].read()
                else:
                    bytes_image = await ctx.author.avatar_url.read()
        else:
            try:
                user = await commands.UserConverter().convert(ctx, image)
            except commands.UserNotFound:
                try:
                    message = await commands.MessageConverter().convert(ctx, image)
                    context = await ctx.bot.get_context(message)
                    return await self.convert(context, message.content, True)
                except commands.MessageNotFound:
                    if recursion:
                        raise
                    async with ctx.bot.http_session.get(image) as response:
                        if response.status == 200:
                            bytes_image = await response.read()
            else:
                bytes_image = user.avatar_url.read()

        return io.BytesIO(bytes_image)

class ExtensionConverter(Converter):

    @staticmethod
    async def convert(ctx: commands.Context, argument: str):
        for file in os.listdir('bot/exts'):
            if file.endswith(argument if argument.endswith('py') else f"{argument}.py"):
                return f"bot.exts.{argument}"
        raise commands.BadArgument("Not a valid extension.")

class LanguageConverter(Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        if argument.lower() not in ctx.bot.setup_config["piston_langs"]:
            raise commands.BadArgument("Not a valid language")
        return argument.lower()

class Choice(Converter):
    def __init__(self, choices: Tuple[str]):
        assert isinstance(choices, tuple), "`Choises` must be a tuple."
        self.choices = list(map(str, choices))

    def __class_getitem__(cls, key: Tuple[str]):
        return cls(key)
    
    async def convert(self, ctx: commands.Context, argument: str):
        if argument.lower() in map(str.lower, self.choices):
            return argument.lower()
        raise commands.BadArgument(f"Argument is not in {', '.join(self.choices)}")
