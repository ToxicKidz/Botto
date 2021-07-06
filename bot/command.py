from discord.ext import commands

class Command(commands.Command):
    def __init__(self, func, **kwargs):
        self.example = getattr(func, "example", None)
        return super().__init__(func, **kwargs)


class Group(commands.Group):
    def __init__(self, func, **kwargs):
        self.example = getattr(func, "example", None)
        return super().__init__(func, **kwargs)

    def command(self, *args, **kwargs):
        return super().command(*args, cls=kwargs.pop('cls', Command), **kwargs)

    def group(self, *args, **kwargs):
        return super().group(*args, cls=kwargs.pop('cls', Group), **kwargs)


def command(name=None, cls=Command, **attrs):
    if not issubclass(cls, Command):
        raise TypeError("Use commands.command instead.")
    return commands.command(name=name, cls=cls, **attrs)


def group(name=None, cls=Group, **attrs):
    cls = cls or Group
    if not issubclass(cls, Group):
        raise TypeError("Use commands.group instead.")

    return commands.group(name=name, cls=cls, **attrs)


def example(ex: str):
    def decorator(func):
        if not isinstance(ex, str):
            raise TypeError("Example must be a str.")
        func.example = ex
        return func

    return decorator
