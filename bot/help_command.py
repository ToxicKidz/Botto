from discord.ext.commands import HelpCommand
import typing as t
from discord.ext import commands, menus
import discord
from bot.exts.utils.pagination import PaginatedMenu, Source
from textwrap import dedent


class Help(HelpCommand):
    def get_command_signature(self, command):
        return f"{self.clean_prefix}{command.qualified_name} {command.signature}"

    async def send_bot_help(
        self, mapping: t.Mapping[commands.Cog, t.List[commands.Command]]
    ):
        embed = discord.Embed(
            title="Help",
            description=("A list of all the commands for this bot.\n"
                         "<> means mandatory while [] means optional."),
            colour=0xE15D44,
        )
        for cog, list_commands in mapping.items():

            list_commands = await self.filter_commands(list_commands, sort=True)

            command_signatures = [
                self.get_command_signature(c) for c in list_commands if not c.hidden
            ]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "Other Commands")
                embed.add_field(
                    name=cog_name, value="\n".join(command_signatures), inline=False
                )
        if len(embed.fields) >= 5:
            source = Source.make_pages(embed, 4)
            menu = PaginatedMenu(source, delete_message_after=True)
            await menu.start(self.context, wait=True)
        else:
            await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            title=self.get_command_signature(command), colour=0x55B4B0
        )
        embed.add_field(
            name="Help",
            value=command.help or "No description for this command.",
            inline=False,
        )
        if getattr(command, "example", None):
            embed.add_field(
                name="Example:",
                value=f"```\n{dedent(command.example).strip().replace('<prefix>', self.clean_prefix)}```",
                inline=False,
            )
        if command.aliases:
            embed.add_field(
                name="Aliases", value=", ".join(f"`{x}`" for x in command.aliases)
            )
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = discord.Embed(
            title=f"Help for the `{cog.qualified_name}` catagory.", colour=0xDFCFBE
        )
        for command in cog.get_commands():
            embed.add_field(
                name=command.name,
                value=command.help or "No description for this command",
                inline=False,
            )
        if len(embed.fields) >= 5:
            source = Source.make_pages(embed, 4)
            menu = PaginatedMenu(source, delete_message_after=True)
            await menu.start(self.context, wait=True)
        else:
            await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(
            title=f"Help for {group.name}.",
            description=group.help or "No help for this command.",
            colour=0x9B2335,
        )
        group_commands = ", ".join(f"`{command.name}`" for command in group.commands)
        if getattr(group, "example", None):
            embed.add_field(
                name="Example:",
                value=f"```\n{dedent(group.example).strip().replace('<prefix>', self.clean_prefix)}```",
                inline=False,
            )
        embed.add_field(name=f"{group.name}'s subcommands", value=group_commands)
        embed.set_footer(
            text=f"Type {self.clean_prefix}{group.name} <command> to see info on each subcommand"
        )
        await self.get_destination().send(embed=embed)
