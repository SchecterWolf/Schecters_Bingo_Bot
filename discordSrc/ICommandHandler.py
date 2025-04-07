__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from abc import ABC
from discord.app_commands import AppCommandContext, CommandTree
from discord.app_commands.commands import Command
from discord.app_commands.errors import AppCommandError
from typing import Callable, Coroutine, Any

ErrorHandler = Callable[[Any, discord.Interaction, AppCommandError], Coroutine[Any, Any, None]]
class ICommandHandler(ABC):
    def __init__(self):
        self.appContext = AppCommandContext(guild=True, dm_channel=False, private_channel=False)
        self.listCommands: list[Command] = []
        self.errorHandler:ErrorHandler = self.defaultErrorHandler

    def setupCommands(self, tree: CommandTree):
        for cmd in self.listCommands:
            cmd.on_error = self.errorHandler
            tree.add_command(cmd)

    async def defaultErrorHandler(self, ignore, interaction: discord.Interaction, error: AppCommandError):
        pass

