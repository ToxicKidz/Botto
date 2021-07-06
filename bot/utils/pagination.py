import typing as t
from more_itertools import chunked

import discord
from discord.ext import commands
from discord.ui import View, Button, Select, button, select

from ..constants import Emojis

class PaginatedView(View):
    def __init__(
        self,
        ctx: commands.Context,
        embeds: list[discord.Embed],
        timeout: t.Optional[float] = None
    ) -> None:
        super().__init__(timeout=timeout)
        self.current_page = 0
        self.context = ctx
        self.embeds = embeds

        select: Select = self.children[-1]

        for option in range(len(self.embeds)):
            select.add_option(label=f"Got to Page {option+1}", value=str(option))

    async def start(self) -> None:
        embed = self.embeds[self.current_page].copy()
        embed.set_footer(text=f"Page number: {self.current_page+1}")
        await self.context.send(embed=embed, view=self)

    async def edit_message(self, interaction: discord.Interaction) -> None:
        if interaction.user != self.context.author:
            await interaction.response.send_message(
                "You cannot interact with someone else's command!", ephemeral=True
            )
        else:
            embed = self.embeds[self.current_page].copy()
            embed.set_footer(text=f"Page number: {self.current_page+1}")
            await interaction.message.edit(embed=embed)

    @button(emoji=Emojis.FIRST)
    async def first_button(
        self, button: Button, interaction: discord.Interaction
    ) -> None:
        if self.current_page:
            self.current_page = 0
            await self.edit_message(interaction)

    @button(emoji=Emojis.PREVIOUS)
    async def previous_button(
        self, button: Button, interaction: discord.Interaction
    ) -> None:
        if self.current_page:
            self.current_page -= 1
            await self.edit_message(interaction)

    @button(emoji=Emojis.NEXT)
    async def next_button(
        self, button: Button, interaction: discord.Interaction
    ) -> None:
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.edit_message(interaction)

    @button(emoji=Emojis.LAST)
    async def last_button(
        self, button: Button, interaction: discord.Interaction
    ) -> None:
        if self.current_page < len(self.embeds) - 1:
            self.current_page = len(self.embeds) - 1
            await self.edit_message(interaction)

    @button(emoji=Emojis.TRASH)
    async def trash_button(
        self, button: Button, interaction: discord.Interaction
    ) -> None:
        if self.context.author != interaction.user:
            await interaction.response.send_message(
                "You cannot interact with someone else's command!", ephemeral=True
            )
            return
        self.stop()
        await interaction.message.delete()

    @select(placeholder="Select a page to go to")
    async def select_page(
        self, select: Select, interaction: discord.Interaction
    ) -> None:
        value = int(select.values[0])

        if value != self.current_page:
            if interaction.user != self.context.author:
                await interaction.response.send_message(
                    "You cannot interact with someone else's command!", ephemeral=True
                )
            else:
                self.current_page = value
                await self.edit_message(interaction)

    @classmethod
    def from_embed(cls, ctx: commands.Context, embed: discord.Embed, max_embeds: int, **options):
        keep_inline = options.pop("keep_inline", False)
        pages = []

        for page in chunked(embed.fields, max_embeds):
            embed1 = discord.Embed(
                title=embed.title, description=embed.description, colour=embed.colour
            )

            for field in page:
                inline = False
                if keep_inline:
                    inline = field.inline
                embed1.add_field(name=field.name, value=field.value, inline=inline)
            pages.append(embed1)

        return cls(ctx, pages, **options)