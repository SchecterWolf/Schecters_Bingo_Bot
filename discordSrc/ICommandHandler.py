__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from abc import ABC
from config.ClassLogger import ClassLogger, LogLevel
from discord.app_commands import AppCommandContext, CommandTree
from discord.app_commands.commands import Command
from discord.app_commands.errors import AppCommandError
from typing import Callable, Coroutine, Any

ErrorHandler = Callable[[Any, discord.Interaction, AppCommandError], Coroutine[Any, Any, None]]
class ICommandHandler(ABC):
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        self.appContext = AppCommandContext(guild=True, dm_channel=False, private_channel=False)
        self.listCommands: list[Command] = []
        self.errorHandler:ErrorHandler = self.defaultErrorHandler

    def setupCommands(self, tree: CommandTree):
        for cmd in self.listCommands:
            cmd.on_error = self.errorHandler
            tree.add_command(cmd)

    async def defaultErrorHandler(self, _, interaction: discord.Interaction, error: AppCommandError):
        if interaction.command:
            ICommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Handler error called for command \"{interaction.command.name}\": {error}")
        else:
            ICommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Handler error called for unknown command")

        if isinstance(error, discord.app_commands.errors.MissingRole):
            await interaction.response.send_message("\U0000274C You do not have permission to use this command!", ephemeral=True)
        elif isinstance(error, discord.app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(f"\U0000274C\U000023F1 Command is on cooldown for {error.retry_after:.1f} seconds.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not process command.", ephemeral=True)

