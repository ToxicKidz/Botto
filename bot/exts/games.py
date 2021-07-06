import asyncio
import datetime
import typing as t
from copy import deepcopy
from dataclasses import dataclass
from itertools import cycle

import discord
from discord.ext import commands
from discord.ui import Button, View, button

from bot.command import command, example

# constants
PIECES = ("\U0001f7e6", "\U0001f7e5")
EMPTY_PIECE = "\u2B1B"
NUMBERS = {d: str(d) + "\N{combining enclosing keycap}" for d in range(1, 7)}
BOARD = [[EMPTY_PIECE for _ in range(6)] for _ in range(6)]

@dataclass
class Player:
    piece: str
    user: discord.abc.User

class Connect4View(View):
    def __init__(self, players: t.Iterable[discord.Member], **kwargs):
        self.cycle_turn = cycle(Player(PIECES[i], player) for i, player in enumerate(players))
        self.done = False
        self.turn: t.Optional[Player] = None
        self.message: t.Optional[discord.Message] = None
        self.board = deepcopy(BOARD)
        self.players = players
        if len(self.players) != 2:
            raise ValueError("There must be exactly 2 players")

        super().__init__(**kwargs)

    def get_embed(self) -> discord.Embed:
        self.turn = next(self.cycle_turn)

        return discord.Embed(
            title=f"Connect 4! \n{self.players[0].display_name} VS {self.players[1].display_name}",
            description="\n".join(
                [
                    f"{self.turn.user.display_name}'s turn!",
                    " ".join(NUMBERS.values()),
                    *reversed(list(map(" ".join, self.board))),
                ]
            ),
            colour=discord.Colour.blue(),
            timestamp=datetime.datetime.now(),
        )

    async def add_piece(self, column: int, interaction: discord.Interaction):
        try:
            index1, index2 = next(
                (index1, index)
                for (index1, row) in enumerate(self.board)
                for (index, piece) in enumerate(row)
                if piece == EMPTY_PIECE and index == column
            )
            self.board[index1][index2] = self.turn.piece

        except StopIteration:
            if not self.check_full():
                return
            self.stop()
            return await self.message.channel.send("It's a tie!")

        self.turn = next(self.cycle_turn)
        await self.message.edit(embed=self.get_embed())
        if self.check_all():
            await self.message.channel.send(f"GG, {interaction.user.mention} won!")
            self.stop()
            self.done = True


    @staticmethod
    def check_all_equal(lst: t.List):
        return all(i == j for i in lst for j in lst)

    def check_full(self):
        return all(piece != EMPTY_PIECE for row in self.board for piece in row)

    def check_all(self):
        if self.check_horizontal():
            return True
        if self.check_vertical():
            return True
        if self.check_diagonal():
            return True
        return False

    def check_horizontal(self):
        for index1, row in enumerate(self.board):
            for index2, piece in enumerate(row):
                if piece == EMPTY_PIECE:
                    continue
                if (
                    self.check_all_equal(row[index2 : index2 + 4])
                    and len(row[index2 : index2 + 4]) == 4
                ):
                    return True
        return False

    def check_vertical(self):
        for index, row in enumerate(self.board):
            if any([i[index] == EMPTY_PIECE for i in self.board[index : index + 4]]):
                continue
            if (
                self.check_all_equal([i[index] for i in self.board[index : index + 4]])
                and len(self.board[index : index + 4]) == 4
            ):
                return True
        return False

    def check_diagonal(self):
        for index1, row in enumerate(self.board):
            for index2, piece in enumerate(row):
                try:
                    upwards_diagonal = [
                        self.board[index1 + 1][index2 + 1],
                        self.board[index1 + 2][index2 + 2],
                        self.board[index1 + 3][index2 + 3],
                    ]
                    if self.check_all_equal([piece, *upwards_diagonal]):
                        if (
                            all(i in PIECES for i in upwards_diagonal)
                            and piece in PIECES
                        ):
                            return True

                except IndexError:
                    pass
                try:
                    downwards_diagonal = [
                        self.board[index1 - 1][index2 + 1],
                        self.board[index1 - 2][index2 + 2],
                        self.board[index1 - 3][index2 + 3],
                    ]
                    if self.check_all_equal([piece, *downwards_diagonal]):
                        if (
                            all(i in PIECES for i in upwards_diagonal)
                            and piece in PIECES
                        ):
                            return True
                except IndexError:
                    pass
                try:
                    downwards_diagonal_left = [
                        self.board[index1 - 1][index2 - 1],
                        self.board[index1 - 2][index2 - 2],
                        self.board[index1 - 3][index2 - 3],
                    ]
                    if self.check_all_equal([piece, *downwards_diagonal_left]):
                        if (
                            all(i in PIECES for i in upwards_diagonal)
                            and piece in PIECES
                        ):
                            return True
                except IndexError:
                    pass
                try:
                    upwards_diagonal_left = [
                        self.board[index1 - 1][index2 - 1],
                        self.board[index1 - 2][index2 - 2],
                        self.board[index1 - 3][index2 - 3],
                    ]
                    if self.check_all_equal([piece, *upwards_diagonal_left]):
                        if (
                            all(i in PIECES for i in upwards_diagonal)
                            and piece in PIECES
                        ):
                            return True
                except IndexError:
                    pass
        return False

    @button(emoji=NUMBERS[1])
    async def num_1(self, button: Button, interaction: discord.Interaction):
        await self.add_piece(0, interaction)

    @button(emoji=NUMBERS[2])
    async def num_2(self, payload):
        await self.add_piece(1, payload)

    @button(emoji=NUMBERS[3])
    async def num_3(self, payload):
        await self.add_piece(2, payload)

    @button(emoji=NUMBERS[4])
    async def num_4(self, payload):
        await self.add_piece(3, payload)

    @button(emoji=NUMBERS[5])
    async def num_5(self, payload):
        await self.add_piece(4, payload)

    @button(emoji=NUMBERS[6])
    async def num_6(self, payload):
        await self.add_piece(5, payload)

    async def on_timeout(self) -> None:
        if not self.done:
            await self.message.channel.send(
                f"{self.turn.user.mention} took too long, so {next(self.cycle_turn).user.mention} won!"
            )

class Games(commands.Cog):
    """A catagory for singleplayer and multiplayer games."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @command()
    @example(
        """
    <prefix>connect4 @joe
    """
    )
    async def connect4(self, ctx: commands.Context, member: discord.Member):
        """Play connect 4 with a friend!"""
        emojis = ("✅", "🚫")
        if member.bot:
            return await ctx.send(
                f"Sorry {ctx.author.mention}, you can't play with a bot!"
            )
        if False and ctx.author == member:
            return await ctx.send(
                f"Sorry {ctx.author.mention}, you can't play with yourself!"
            )
        msg = await ctx.send(
            f"{member.mention}, do you want to play Connect 4 with {ctx.author.mention}?"
            f"React with {emojis[0]} if yes or {emojis[1]} if not."
        )
        for emoji in emojis:
            await msg.add_reaction(emoji)
        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: str(r) in emojis and u == member,
                timeout=20,
            )
            await msg.delete()
        except asyncio.TimeoutError:
            await msg.delete()
            return

        if str(reaction) == emojis[1]:
            return

        view = Connect4View(
            [ctx.author, member], timeout=20
        )

        view.message = await ctx.send("Let's play Connect 4!", embed=view.get_embed(), view=view)


def setup(bot):
    bot.add_cog(Games(bot))
    print("Loaded Games")
