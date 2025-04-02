__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "__"

import aiohttp
import discord
import sys

from .IAsyncDiscordGame import IAsyncDiscordGame

from config.ClassLogger import ClassLogger
from config.Globals import GLOBALVARS
from config.Log import LogLevel

from discord.app_commands.commands import Command

from game.ActionData import ActionData
from game.GameStore import GameStore

from PIL import Image
from io import BytesIO
from typing import cast
from unittest.mock import AsyncMock, MagicMock

class DebugCommandHandler:
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client):
        self.tree = discord.app_commands.CommandTree(bot)

        self.listCommands: list[Command] = [
            Command(
                name="add_player",
                description="Add an ephemeral user",
                callback=self.addPlayer
            ),
            Command(
                name="bulk_add_players",
                description="Adds many ephemeral users (30)",
                callback=self.bulkAddPlayers
            ),
            Command(
                name="save_avatar",
                description="Saves the users avatar internally",
                callback=self.saveAvatar
            )
        ]

    def setupCommands(self):
        for cmd in self.listCommands:
            self.tree.add_command(cmd)

    async def syncCommands(self):
        # Apparently this only has to be done once to register the commands
        return

        try:
            await self.tree.sync()
        except Exception as e:
            DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Failed to sync commands: {e}")
            sys.exit(1)

    async def saveAvatar(self, interaction: discord.Interaction):
        if not interaction.user:
            await interaction.response.send_message("Command didnt include user", ephemeral=True)
            return
        await interaction.response.send_message("Request processing", ephemeral=True)
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Saving avatar for user \"{interaction.user.display_name}\"({interaction.user.id})")

        user = interaction.user
        async with aiohttp.ClientSession() as session:
            async with session.get(user.display_avatar.url) as response:
                imageData = await response.read()
                image = Image.open(BytesIO(imageData))
                image.save(f"{GLOBALVARS.PROJ_ROOT}/SavedUserAvatar.png")

    async def bulkAddPlayers(self, interaction: discord.Interaction):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Slash command bulkAddPlayers called")
        mockPlayers = ["Elephant", "Tiger", "Whale", "Eagle", "Panda", "Shark", "Leopard", "Kangaroo", "Anaconda", "Penguin",
                       "Giraffe", "Frog", "Fox", "Dragon", "Cobra", "Bison", "Kingfisher", "Squid", "Mandrill", "Okapi", "Axolotl",
                       "Tasmanian Devil", "Badger", "Dart Frog", "Crab", "Narwal", "Aye-Aye", "Quokka", "Saiga"]

        # Add mock players to game
        game = GameStore().getGame(interaction.guild_id or -1)
        if not game:
            guildName = interaction.guild.name if interaction.guild else "the guild"
            await interaction.response.send_message(f"There is no active game for {guildName}, cannot add player!")
        else:
            await interaction.response.send_message("Added bulk players to the game!")

            game = cast(IAsyncDiscordGame, game)
            for player in mockPlayers:
                mockInter = self._makeMockInteraction(interaction)
                self._addPlayerIntrnl(game, mockInter, player, False)
            self._addPlayerIntrnl(game, self._makeMockInteraction(interaction), "Pikachu", True)

    async def addPlayer(self, interaction: discord.Interaction, message: str):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Slash command addPlayer called with guild id: {interaction.guild_id}.")
        game = GameStore().getGame(interaction.guild_id or -1)

        # Add mock player to the game
        if game:
            await interaction.response.send_message(f"Mock user \"{message}\" as been added to the game.")
            self._addPlayerIntrnl(cast(IAsyncDiscordGame, game), interaction, message, True)
        else:
            guildName = interaction.guild.name if interaction.guild else "the guild"
            await interaction.response.send_message(f"There is no active game for {guildName}, cannot add player!")

    def _makeMockInteraction(self, interaction: discord.Interaction):
        mockInter = AsyncMock(spec=discord.Interaction)

        mockUser = MagicMock()
        mockUser.id = interaction.user.id
        mockUser.mention = f"<@{interaction.user.id}>"
        mockUser.name = "MockUser"

        mockChannel = MagicMock()
        mockChannel.id = interaction.channel_id
        mockChannel.name = "MockChannel"

        mockGuild = MagicMock()
        mockGuild.id = interaction.guild_id
        mockGuild.name = "MockGuild"

        mockInter.user = mockUser
        mockInter.channel = mockChannel
        mockInter.guild = mockGuild
        mockInter.channel_id = interaction.channel_id
        mockInter.guild_id = interaction.guild_id

        mockInter.response = AsyncMock()

        return mockInter

    def _addPlayerIntrnl(self, game: IAsyncDiscordGame, interaction: discord.Interaction, player: str, refresh: bool):
        # Create the mock user
        mockUser = MagicMock(spec=discord.User)
        mockUser.id = -1
        mockUser.name = player
        mockUser.bot = False
        mockUser.mention = f"<@{mockUser.id}>"
        mockUser.display_name = player
        mockUser.dm_channel = None


        # Create a mock DM channel
        mockChannel = AsyncMock(spec=discord.DMChannel)
        mockChannel.id = -1
        mockChannel.recipient = mockUser
        mockChannel.type = discord.ChannelType.private

        # Add mock player to the running game
        interaction.user = mockUser
        _ = game.addPlayer(ActionData(interaction=interaction, mockDMChannel=mockChannel, refresh=refresh))

