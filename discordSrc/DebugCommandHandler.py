__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "__"

import aiohttp
import discord

from .ICommandHandler import ICommandHandler

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS

from discord.app_commands.commands import Command

from game.ActionData import ActionData
from game.CallRequest import CallRequest
from game.CardImgCreator import CardImgCreator
from game.GameStore import GameStore
from game.IGameInterface import IGameInterface
from game.Player import Player

from PIL import Image
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, cast

class DebugCommandHandler(ICommandHandler):
    __LOGGER = ClassLogger(__name__)
    __DEBUG_ID_COUNTER = -1

    def __init__(self):
        super().__init__()
        self.listCommands = [
            Command(
                name="add_player",
                description="[DEBUG] Add an ephemeral user",
                callback=self.addPlayer,
                allowed_contexts=self.appContext,
            ),
            Command(
                name="bulk_add_players",
                description="[DEBUG] Adds many ephemeral users (30)",
                callback=self.bulkAddPlayers,
                allowed_contexts=self.appContext
            ),
            Command(
                name="save_avatar",
                description="[DEBUG] Saves the users avatar internally",
                callback=self.saveAvatar,
                allowed_contexts=self.appContext
            ),
            Command(
                name="make_req",
                description="[DEBUG] Make a request on behalf of a user",
                callback=self.makeRequest,
                allowed_contexts=self.appContext
            ),
            Command(
                name="get_board",
                description="[DEBUG] Get the board slots for a player",
                callback=self.getBoard,
                allowed_contexts=self.appContext
            )
        ]

    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def saveAvatar(self, interaction: discord.Interaction):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Saving avatar for user \"{interaction.user.display_name}\"({interaction.user.id})")

        # Make sure user is included
        if not interaction.user:
            await interaction.response.send_message("Command didn't include user", ephemeral=True)
            return
        await interaction.response.send_message("Request processing", ephemeral=True)

        # Save the user's avatar
        user = interaction.user
        async with aiohttp.ClientSession() as session:
            async with session.get(user.display_avatar.url) as response:
                imageData = await response.read()
                image = Image.open(BytesIO(imageData))
                image.save(f"{GLOBALVARS.PROJ_ROOT}/SavedUserAvatar.png")

    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def bulkAddPlayers(self, interaction: discord.Interaction):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Slash command bulkAddPlayers called")
        mockPlayers = ["Elephant", "Tiger", "Whale", "Eagle", "Panda", "Shark", "Leopard", "Kangaroo", "Anaconda", "Penguin",
                       "Giraffe", "Frog", "Fox", "Dragon", "Cobra", "Bison", "Kingfisher", "Squid", "Mandrill", "Okapi", "Axolotl",
                       "Tasmanian Devil", "Badger", "Dog", "Crab", "Narwal", "Cat", "Quokka", "Fish", "Dove"]

        # Make sure game instance exists
        game = await self._getGame(interaction)
        if not game:
            return

        # Add mock players to game
        await interaction.response.send_message("Adding bulk players to the game.", ephemeral=True)
        for player in mockPlayers:
            mockInter = self._makeMockInteraction(interaction)
            self._addPlayerIntrnl(game, mockInter, player, False)
        self._addPlayerIntrnl(game, self._makeMockInteraction(interaction), "Pikachu", True)

    @discord.app_commands.describe(player_name="Mock player name to add to the game")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def addPlayer(self, interaction: discord.Interaction, player_name: str):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Slash command addPlayer called with guild id: {interaction.guild_id}.")

        # Make sure the game instance exists
        game = await self._getGame(interaction)
        if not game:
            return

        # Check if the player is eligible
        res = game.game.checkEligibleFromID(player_name, -1)
        if not res.result:
            await interaction.response.send_message(res.responseMsg, ephemeral=True)
            return

        # Add mock player to the game
        await interaction.response.send_message(f"Mock user \"{player_name}\" as been added to the game.", ephemeral=True)
        self._addPlayerIntrnl(game, interaction, player_name, True)

    @discord.app_commands.describe(player_name="Mock player to make request for")
    @discord.app_commands.describe(bing_id="Bing ID of the slot to request")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def makeRequest(self, interaction: discord.Interaction, player_name: str, bing_id: int):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Slash command makeRequest called with guild id: {interaction.guild_id}.")

        game = await self._getGame(interaction)
        if not game:
            return

        player: Optional[Player] = self._getPlayerByName(game, player_name)
        if not player:
            await interaction.response.send_message(f"Could not find an active player with the name '{player_name}'.", ephemeral=True)
            return

        requestBing = player.card.getBingFromID(bing_id)
        if not requestBing:
            await interaction.response.send_message("Requested call category does not exist in this players card, aborting.", ephemeral=True)
            return

        await interaction.response.send_message("Making call request...", ephemeral=True)
        _ = game.requestCall(ActionData(interaction=interaction, callRequest=CallRequest(player, requestBing)))

    @discord.app_commands.describe(player_name="Mock player to get board for")
    @discord.app_commands.checks.has_role(Config().getConfig("GameMasterRole"))
    async def getBoard(self, interaction: discord.Interaction, player_name: str):
        DebugCommandHandler.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Slash command getBoardcalled with guild id: {interaction.guild_id}.")

        game = await self._getGame(interaction)
        if not game:
            return

        player: Optional[Player] = self._getPlayerByName(game, player_name)
        if not player:
            await interaction.response.send_message(f"Could not find an active player with the name '{player_name}'.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        slots = [f"[{bing.bingIdx}] {bing.bingStr}" for row in player.card.getCardBings() for bing in row]
        slots = sorted(slots, key=lambda s:int(s.split(']')[0][1:]))

        # Create graphical board
        filename = f"board_{player.userID}.png"
        file = discord.File(CardImgCreator().createGraphicalCard(player.card), filename)

        await interaction.followup.send(f"Board slots for player {player.card.getCardOwner()}:\n " + ",  ".join(slots), file=file, ephemeral=True)

    async def _getGame(self, interaction: discord.Interaction) -> Optional[IGameInterface]:
        game = GameStore().getGame(interaction.guild_id or -1)
        if not game:
            guildName = interaction.guild.name if interaction.guild else "the guild"
            await interaction.response.send_message(f"There is no active game for {guildName}, cannot add player!", ephemeral=True)
        return game

    def _getPlayerByName(self, iface: IGameInterface, name: str) -> Optional[Player]:
        ret = None
        for player in iface.game.players:
            if player.card.getCardOwner() == name:
                ret = player
                break
        return ret

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

    def _addPlayerIntrnl(self, game: IGameInterface, interaction: discord.Interaction, player: str, refresh: bool):
        # Create the mock user
        mockUser = MagicMock(spec=discord.User)
        mockUser.id = DebugCommandHandler.__DEBUG_ID_COUNTER
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
        DebugCommandHandler.__DEBUG_ID_COUNTER -= 1

