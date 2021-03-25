import typing

import discord
from discord.ext import commands

from bot.bot import Bot
from bot.exts.utils.converters import LanguageConverter, CodeBlockConverter
from bot.exts.utils.utils import get_mystbin_link

PISTON_API_URL = "https://emkc.org/api/v1/piston/execute"

class Miscellaneous(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def _run_eval(self, ctx: commands.Context, language: str, code: str):
        json = {'language': language, 'source': code}
        async with ctx.typing():
            async with self.bot.http_session.post(PISTON_API_URL, json=json) as response:
                return await response.json()

    @commands.command(name="eval", aliases=("e", "run"))
    @commands.max_concurrency(1, commands.BucketType.user)
    async def _eval(
        self,
        ctx: commands.Context,
        language: typing.Optional[LanguageConverter],
        *,
        code: CodeBlockConverter):

        if not language:
            if code[0]:
                language = code[0].group("lang")
        
        code = code[1]
        eval_data = await self._run_eval(ctx, language, code)

        if msg := eval_data.get("message"):
            return await ctx.reply(
                embed=discord.Embed(
                    title="That didn't go as expected.", description=msg, color=discord.Colour.red()
                )
            )
        if eval_data["language"] in ("python2", "python3"):
            eval_data["language"] = "python"

        output = eval_data["output"].strip().replace("```", '`\u200b``')
        link=None
        if len(lines := output.splitlines()) > 15:
            lines = '\n'.join(lines)
            output = f"{lines[:15]}\n ... \nTruncated (too many lines)"
            link = await get_mystbin_link(self.bot, eval_data['output'].strip(), eval_data['language'])
            link = f"**Full output [here](https://mystb.in/{link['pastes'][0]['id']})**"
        elif len(output) > 1500:
            output = f"{output[:1500]}\n ... \nTruncated (output too long)\n "
            link = await get_mystbin_link(self.bot, eval_data['output'], eval_data['language'])
            link = f"***Full output [here](https://mystb.in/{link['pastes'][0]['id']})***"

        embed = discord.Embed(
            title=f"Ran your code in `{eval_data['language']}`",
            description=f"```{eval_data['language']}\n{output}```",
            colour=discord.Colour.green()   
        )
        if link:
            embed.description += f"\n{link}"
        await ctx.send(embed=embed)

def setup(bot: Bot):
    bot.add_cog(Miscellaneous(bot))
    print("Loaded Miscellaneous")