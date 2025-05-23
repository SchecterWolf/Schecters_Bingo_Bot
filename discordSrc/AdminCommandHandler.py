__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IAsyncDiscordGame import IAsyncDiscordGame
from .ICommandHandler import ICommandHandler
from .GameControllerDiscord import GameControllerDiscord
from .GameGuild import GameGuild

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config

from game.ActionData import ActionData
from game.BannedData import BannedData
from game.GameStore import GameStore

from discord.app_commands.commands import Command

from typing import Optional, cast

class AdminCommandHandler(ICommandHandler):
    __LOGGER = ClassLogger(__name__)

    def __init__(self):
        super().__init__()
        self.listCommands = [
            Command(
                name="kick_player",
                description="[ADMIN] Kick a player from the remainder of the game.",
                callback=self.kickPlayer,
                allowed_contexts=self.appContext,
            ),
            Command(
                name="ban_player",
                description="[ADMIN] Ban a player from playing, forever.",
                callback=self.banPlayer,
                allowed_contexts=self.appContext,
            ),
            Command(
                name="unban_player",
                description="[ADMIN] Unban a player from the livestream bingo games.",
                callback=self.unbanPlayer,
                allowed_contexts=self.appContext
            ),
            Command(
                name="game_status",
                description="[ADMIN] Get game status information.",
                callback=self.gameStatus,
                allowed_contexts=self.appContext
            )
        ]

    @discord.app_commands.describe(member="User to kick")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def kickPlayer(self, interaction: discord.Interaction, member: discord.Member):
        AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Admin command kick player called.")
        if self._checkBotMember(interaction, member):
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
        if self._checkBotMember(interaction, member):
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
            guild: Optional[GameGuild] = None
            if gameController:
                guild = cast(GameControllerDiscord, gameController).getGuild(guildID)
            if guild:
                guild.persistentStats.removePlayer(member.id)

    @discord.app_commands.describe(member="User to unban")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def unbanPlayer(self, interaction: discord.Interaction, member: discord.Member):
        AdminCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Admin command unban player called.")
        if self._checkBotMember(interaction, member):
            return

        # Remove player from the unban list
        await interaction.response.send_message(f"\U0001F607 Unbanning user {member.display_name}")
        BannedData().removeBanned(member.id)

    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def gameStatus(self, interaction: discord.Interaction):
        # TODO SCH
        await interaction.response.defer()
        pass

    async def _checkBotMember(self, interaction: discord.Interaction, member: discord.Member) -> bool:
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

