import discord
from discord.ext import commands, menus
from bot.exts.command import command, example
import typing as t
import datetime
from itertools import cycle
from copy import deepcopy
import asyncio

# constants
PLAYER_1_PIECE = "\U0001f7e6"
PLAYER_2_PIECE = "\U0001f7e5"
EMPTY_PIECE = "\u2B1B"
NUMBERS = {d: str(d) + "\N{combining enclosing keycap}" for d in range(1, 7)}
BOARD = [[EMPTY_PIECE for _ in range(6)] for _ in range(6)]


class Connect4Menu(menus.Menu):
    def __init__(self, players: t.List[discord.Member], **kwargs):
        self.cycle_turn = cycle(players)
        self.turn: t.Optional[discord.Member] = None
        self.board = deepcopy(BOARD)
        self.player_pieces = [PLAYER_1_PIECE, PLAYER_2_PIECE]
        self.players = players
        if len(self.players) != 2:
            raise ValueError("There must be exactly 2 players")
        super().__init__(**kwargs)

    def reaction_check(self, payload):
        if (
            payload.message_id != self.message.id
            or payload.event_type == "REACTION_REMOVE"
        ):
            return False
        return payload.member == self.turn

    async def send_initial_message(self, ctx, channel):
        self.turn = next(self.cycle_turn)
        embed = discord.Embed(
            title=f"Connect 4! \n{self.players[0].display_name} VS {self.players[1].display_name}",
            description="\n".join(
                [
                    f"{self.turn.display_name}'s turn!",
                    " ".join(NUMBERS.values()),
                    *reversed(list(map(" ".join, self.board))),
                ]
            ),
            colour=discord.Colour.blue(),
            timestamp=datetime.datetime.now(),
        )
        return await ctx.send(embed=embed)

    async def add_piece(self, column, payload):
        try:
            index1, index2 = next(
                (index1, index)
                for (index1, row) in enumerate(self.board)
                for (index, piece) in enumerate(row)
                if piece == EMPTY_PIECE and index == column
            )
            self.board[index1][index2] = self.player_pieces[
                self.players.index(payload.member)
            ]
        except StopIteration:
            if not check_full():
                try:
                    await self.message.remove_reaction(payload.emoji, payload.member)
                except discord.Forbidden:
                    pass
                return
            self.stop()
            return await self.message.channel.send("It's a tie!")
        self.turn = next(self.cycle_turn)
        embed = discord.Embed(
            title=f"Connect 4!\n{self.players[0].display_name} VS {self.players[1].display_name}",
            description="\n".join(
                [
                    f"{self.turn.display_name}'s turn!",
                    " ".join(NUMBERS.values()),
                    *reversed(list(map(" ".join, self.board))),
                ]
            ),
            colour=discord.Colour.blue(),
            timestamp=datetime.datetime.now(),
        )
        await self.message.edit(embed=embed)
        try:
            await self.message.remove_reaction(
                emoji=payload.emoji, member=payload.member
            )
        except discord.Forbidden:
            pass
        if self.check_all():
            await self.message.channel.send(f"GG, {payload.member.mention} won!")
            self.stop()

    async def finalize(self, timed_out):
        if timed_out:
            await self.message.channel.send(
                f"{self.turn.mention} took too long, so {next(self.cycle_turn).mention} won!"
            )

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
                            all(i in self.player_pieces for i in upwards_diagonal)
                            and piece in self.player_pieces
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
                            all(i in self.player_pieces for i in upwards_diagonal)
                            and piece in self.player_pieces
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
                            all(i in self.player_pieces for i in upwards_diagonal)
                            and piece in self.player_pieces
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
                            all(i in self.player_pieces for i in upwards_diagonal)
                            and piece in self.player_pieces
                        ):
                            return True
                except IndexError:
                    pass
        return False

    @menus.button(NUMBERS[1])
    async def num_1(self, payload):
        await self.add_piece(0, payload)

    @menus.button(NUMBERS[2])
    async def num_2(self, payload):
        await self.add_piece(1, payload)

    @menus.button(NUMBERS[3])
    async def num_3(self, payload):
        await self.add_piece(2, payload)

    @menus.button(NUMBERS[4])
    async def num_4(self, payload):
        await self.add_piece(3, payload)

    @menus.button(NUMBERS[5])
    async def num_5(self, payload):
        await self.add_piece(4, payload)

    @menus.button(NUMBERS[6])
    async def num_6(self, payload):
        await self.add_piece(5, payload)


class Games(commands.Cog):
    """A catagory for singleplayer and multiplayer games."""

    def __init__(self, bot):
        self.bot = bot

    @command(name="connect4")
    @example(
        """
    <prefix>connect4 @joe
    """
    )
    async def _connect4(self, ctx: commands.Context, member: discord.Member):
        """Play connect 4 with a friend!"""
        emojis = ("✅", "🚫")
        if member.bot:
            return await ctx.send(
                f"Sorry {ctx.author.mention}, you can't play with a bot!"
            )
        if ctx.author == member:
            return await ctx.send(
                f"Sorry {ctx.author.mention}, you can't play with yourself!"
            )
        msg = await ctx.send(
            f"{member.mention}, do you want to play connect4 with {ctx.author.mention}? React with {emojis[0]} if yes or {emojis[1]} if not."
        )
        for emoji in emojis:
            await msg.add_reaction(emoji)
        try:
            reaction, user = await self.bot.wait_for(
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
        menu = Connect4Menu(
            [ctx.author, member], clear_reactions_after=True, timeout=20
        )
        await menu.start(ctx, wait=True)


def setup(bot):
    bot.add_cog(Games(bot))
    print("Loaded Games")
