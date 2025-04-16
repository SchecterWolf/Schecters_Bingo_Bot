__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .GameGuild import GameGuild
from .GameInterfaceDiscord import GameInterfaceDiscord
from .IAsyncDiscordGame import IAsyncDiscordGame

from config.ClassLogger import ClassLogger
from config.Log import LogLevel

from game.GameStore import GameStore
from game.IGameController import IGameController
from game.Result import Result
from game.Sync import sync_aware

from typing import Dict, Optional, cast

class GameControllerDiscord(IGameController):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client, gameGuilds: Dict[int, GameGuild]):
        self.bot = bot
        self.gameGuilds = gameGuilds
        self.gameStore = GameStore()

    def getBotClient(self) -> discord.Client:
        return self.bot

    def getGuild(self, guildID: int) -> Optional[GameGuild]:
        return self.gameGuilds.get(guildID)

    def startGame(self, *args, **kwargs):
        self._startGameInternal(*args, **kwargs)

    def stopGame(self, *args, **kwargs):
        self._stopGameInternal(*args, **kwargs)

    @sync_aware
    async def _startGameInternal(self, interaction: discord.Interaction) -> Result:
        # Sanity check
        guild = interaction.guild
        if not guild:
            return Result(False, "Start game called with an empty guild, aborting.")
        GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Bot is starting game for guild {guild.name}")

        ret = Result(False)
        gameGuild = self.gameGuilds.get(guild.id)
        newGame = self.gameStore.getGame(guild.id)

        # Create the new bingo game object
        if not gameGuild:
            ret.responseMsg = f"Discord server id \"{guild.id}\" has not been registered with the bot, aborting."
        elif newGame:
            ret.responseMsg = f"Discord server id \"{guild.id}\" already has a game in progress, skipping."
            newGame = None
        else:
            newGame = cast(IAsyncDiscordGame, GameInterfaceDiscord(self.bot, gameGuild))
            ret.result = True

        # Go ahead an add the game to the store since the startup procedure needs it
        if ret.result and newGame:
            self.gameStore.addGame(guild.id, newGame)

        # Init and start the game
        if newGame and isinstance(newGame, IAsyncDiscordGame):
            if not (await newGame.init()).result:
                ret.responseMsg = "Failed to initialize game. Aborting."
            else:
                ret = await newGame.start()

        # Teardown on error
        if not ret.result:
            # Remove the game from the store
            self.gameStore.removeGame(guild.id)
            # Destroy the new game
            if newGame:
                GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_CRIT, "Destroying problematic game.")
                newGame.destroy()
            # Send error message
            await interaction.followup.send(ret.responseMsg, ephemeral=True)

        GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_INFO if ret.result else LogLevel.LEVEL_ERROR, ret.responseMsg)
        return ret

    @sync_aware
    async def _stopGameInternal(self, guildID: int) -> Result:
        GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, "Game signaled to be stopped for guild id {guildID}.")
        ret = Result(False)
        game = self.gameStore.getGame(guildID)

        if not game:
            ret.responseMsg = f"No active game exists for guild \"{guildID}\", skipping stop game."
        elif isinstance(game, IAsyncDiscordGame):
            await game.destroy()
            self.gameStore.removeGame(guildID)
            ret.result = True
            ret.responseMsg = f"Bingo game stopped."

        if not ret.result:
            GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)

        return ret
