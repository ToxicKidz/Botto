import discord
from discord.ext import commands
from discord.ext.commands import Command as _BaseCommand, Group as _BaseGroup


class Command(_BaseCommand):
    def __init__(self, func, **kwargs):
        self.example = getattr(func, "example", None)
        return super().__init__(func, **kwargs)


class Group(_BaseGroup):
    def __init__(self, func, **kwargs):
        self.example = getattr(func, "example", None)
        return super().__init__(func, **kwargs)


def command(name=None, cls=None, **attrs):
    cls = cls or Command
    if not issubclass(cls, Command):
        raise TypeError("Use commands.command instead.")
    return commands.command(name=name, cls=cls, **attrs)


def group(name=None, cls=None, **attrs):
    cls = cls or Group
    if not issubclass(cls, Group):
        raise TypeError("Use commands.command instead.")
    return commands.command(name=name, cls=cls, **attrs)


def example(ex: str):
    def decorator(func):
        if not isinstance(ex, str):
            raise TypeError("Example must be a str.")
        func.example = ex
        return func

    return decorator
