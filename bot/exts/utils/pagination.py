import discord
from discord.ext import commands, menus
import typing as t
from functools import wraps


class PaginatedMenu(menus.MenuPages):
    def __init__(
        self, source, emojis: t.Optional[t.Mapping[str, str]] = None, **kwargs
    ):
        super().__init__(source, **kwargs)
        if not emojis:
            emojis = {"⏹️": "🗑️"}
        for emoji, button in self._buttons.items():

            if emoji.name in emojis:
                emoji.name = emojis.pop(emoji.name)

            button.action = self.wrap_button(button.action)

    def wrap_button(self, action: t.Callable):
        @wraps(action)
        async def inner(self, payload: discord.RawReactionActionEvent):
            if self._can_remove_reactions and payload.event_type == "REACTION_REMOVE":
                return

            await action(self, payload)

            if self._can_remove_reactions and payload.event_type == "REACTION_ADD":
                await self.message.remove_reaction(payload.emoji, payload.member)

        return inner


class Source(menus.ListPageSource):
    async def format_page(self, menu: menus.MenuPages, entry: discord.Embed):
        return entry

    @classmethod
    def make_pages(cls, embed: discord.Embed, max_embeds: int, **options):
        pages = []

        for page in range(0, len(embed.fields), max_embeds):
            embed1 = discord.Embed(
                title=embed.title, description=embed.description, colour=embed.colour
            )

            for field in embed.fields[page : page + max_embeds]:
                inline = False
                if options.pop("keep_inline", False):
                    inline = field.inline
                embed1.add_field(name=field.name, value=field.value, inline=inline)
            pages.append(embed1)

        return cls(pages, per_page=1, **options)
