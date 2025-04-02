__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IAsyncDiscordGame import IAsyncDiscordGame
from .GameControllerDiscord import GameControllerDiscord
from .GameGuild import GameGuild

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config

from game.ActionData import ActionData
from game.BannedData import BannedData
from game.GameStore import GameStore

from discord.app_commands import AppCommandContext, CommandTree
from discord.app_commands.commands import Command

from typing import Union, cast

class AdminCommandHandler:
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        appContext = AppCommandContext(guild=True, dm_channel=False, private_channel=False)
        self.listCommands: list[Command] = [
            Command(
                name="kick_player",
                description="[ADMIN] Kick a player from the remainder of the game.",
                callback=self.kickPlayer,
                allowed_contexts=appContext,
            ),
            Command(
                name="ban_player",
                description="[ADMIN] Ban a player from playing, forever.",
                callback=self.banPlayer,
                allowed_contexts=appContext,
            ),
            Command(
                name="unban_player",
                description="[ADMIN] Unban a player from the livestream bingo games.",
                callback=self.unbanPlayer,
                allowed_contexts=appContext
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
        if self.checkBotMember(interaction, member):
            return

        # Make sure the game instance exists
        game = GameStore().getGame(interaction.guild_id or -1)
        if not game:
            gName = interaction.guild.name if interaction.guild else "N/A"
            await interaction.response.send_message(f"\U0000274C There is no active game for server {gName}", ephemeral=True)
            return

        # Kick player
        await interaction.response.send_message(f"\U0001F45F\U0001F4A5 Kicking user {member.display_name} from the remainder of the game!")
        game = cast(IAsyncDiscordGame, game)
        _ = game.kickPlayer(ActionData(member=member))

    @discord.app_commands.describe(member="User to ban")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def banPlayer(self, interaction: discord.Interaction, member: discord.Member):
        AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Admin command ban player called.")
        if self.checkBotMember(interaction, member):
            return

        await interaction.response.send_message(f"\U0000274C\U0001F528 Banning user {member.display_name} from all further games!")

        guildID = interaction.guild_id or -1
        game = GameStore().getGame(guildID)
        # Ban through the game instance
        if game:
            game = cast(IAsyncDiscordGame, game)
            _ = game.banPlayer(ActionData(member=member))
        # Otherwise, just add the player directly to the ban list
        else:
            BannedData().addBanned(member.id, member.display_name)
            gameController = GameStore().getController()
            guild: Union[GameGuild, None] = None
            if gameController:
                guild = cast(GameControllerDiscord, gameController).getGuild(guildID)
            if guild:
                guild.persistentStats.removePlayer(member.id)

    @discord.app_commands.describe(member="User to unban")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def unbanPlayer(self, interaction: discord.Interaction, member: discord.Member):
        AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Admin command unban player called.")
        if self.checkBotMember(interaction, member):
            return

        # Remove player from the unban list
        await interaction.response.send_message(f"\U0001F607 Unbanning user {member.display_name}")
        BannedData().removeBanned(member.id)

    async def checkBotMember(self, interaction: discord.Interaction, member: discord.Member) -> bool:
        """
        Checks if a member is the bot client itself

        Parameters:
            interaction (discord.Interaction): The interaction context in which
            member (discord.Member): The member to verify

        Returns:
            bool: True if the member the bot, False otherwise
        """
        bIsBot = interaction.client.user != None and interaction.client.user.id == member.id
        if bIsBot:
            await interaction.response.send_message(f"\U0001F6AB Can't use the bot for this command", ephemeral=True)
        return bIsBot

    async def _handleError(self, _, interaction: discord.Interaction, error):
        if interaction.command:
            AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Handler error called for command \"{interaction.command.name}\": {error}")
        else:
            AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Handler error called for unknown command")

        if isinstance(error, discord.app_commands.errors.MissingRole):
            await interaction.response.send_message("\U0000274C You do not have permission to use this command!", ephemeral=True)
        else:
            await interaction.response.send_message("Could not process command.", ephemeral=True)

