from asyncio import get_event_loop
from functools import partial, wraps

import discord
from discord.ext import commands

from bot.utils.exceptions import RoleHierarchyError

def role_hierarchy(*, ctx_arg: int = 1, member_arg: int = 2):
    """Check if the invoker's top role is higher than the member's top role."""

    def decorator(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            ctx = args[ctx_arg]
            try:
                member = args[member_arg]
            except IndexError:
                member = kwargs.get("member")
            if not (
                isinstance(ctx, commands.Context) and isinstance(member, discord.Member)
            ):
                return await func(
                    *args, **kwargs
                )  # Skip if they aren't the right types.

            if ctx.author.top_role <= member.top_role:
                raise RoleHierarchyError(ctx.author, member)

            return await func(*args, **kwargs)

        return inner

    return decorator


def run_in_executor(executor=None):

    loop = get_event_loop()

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            func = partial(func, *args, **kwargs)

            return loop.run_in_executor(executor, func)

        return inner

    return decorator
