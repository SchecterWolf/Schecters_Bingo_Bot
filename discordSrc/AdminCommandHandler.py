__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from discord.app_commands import AppCommandContext, CommandTree
from discord.app_commands.commands import Command

class AdminCommandHandler:
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        appContext = AppCommandContext(guild=True, dm_channel=False, private_channel=False)
        self.listCommands: list[Command] = [
            Command(
                name="kick_player",
                description="Kick a player from the remainder of the game.",
                callback=self.kickPlayer,
                allowed_contexts=appContext,
            ),
            Command(
                name="ban_player",
                description="Ban a player from playing, forever.",
                callback=self.banPlayer,
                allowed_contexts=appContext,
            )
        ]

    def setupCommands(self, tree: CommandTree):
        for cmd in self.listCommands:
            cmd.on_error = self._handleError
            tree.add_command(cmd)

    @discord.app_commands.describe(member="User to kick")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def kickPlayer(self, interaction: discord.Interaction, member: discord.Member):
        AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Admin command kick player called.")
        await interaction.response.defer()

    @discord.app_commands.describe(member="User to ban")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def banPlayer(self, interaction: discord.Interaction, member: discord.Member):
        AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Admin command ban player called.")
        await interaction.response.defer()

    async def _handleError(self, _, interaction: discord.Interaction, error):
        if interaction.command:
            AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Handler error called for command \"{interaction.command.name}\": {error}")
        else:
            AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Handler error called for unknown command")

        if isinstance(error, discord.app_commands.errors.MissingRole):
            await interaction.response.send_message("\U0000274C You do not have permission to use this command!", ephemeral=True)
        else:
            await interaction.response.send_message("Could not process command.", ephemeral=True)

