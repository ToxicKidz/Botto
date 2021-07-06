import discord
from discord.ext.commands import CheckFailure

class RoleHierarchyError(CheckFailure):
    def __init__(self, invoker: discord.Member, target: discord.Member):
        self.invoker = invoker
        self.target = target
    
    def __str__(self):
        return (
            f"Missing Permissions: {self.invoker.display_name}'s top role ({self.invoker.top_role}) "
            f"is lower than {self.target.display_name}'s top role {self.target.top_role}."
        )
    