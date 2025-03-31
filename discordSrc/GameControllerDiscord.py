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

from typing import Dict, cast

class GameControllerDiscord(IGameController):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client, gameGuilds: Dict[int, GameGuild]):
        self.bot = bot
        self.gameGuilds = gameGuilds
        self.gameStore = GameStore()

    def getBotClient(self) -> discord.Client:
        return self.bot

    def startGame(self, *args, **kwargs):
        GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"startGame called") # TODO SCH rm
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

        GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "calling newGame.initGame") # TODO SCH rm
        if newGame and isinstance(newGame, IAsyncDiscordGame):
            # Init and start the game
            if not (await newGame.init()).result:
                ret.responseMsg = "Failed to initialize game. Aborting."
            else:
                GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "calling newGame.startGame") # TODO SCH rm
                ret = await newGame.start()

            # Add the game if all goes well
            if ret.result:
                GameStore().addGame(guild.id, newGame)
            # Remove the game on error
            else:
                GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_DEBUG, "calling newGame.destroyGame") # TODO SCH rm
                await newGame.destroy()

        # Send error message, if any
        if not ret.result:
            await interaction.response.send_message(ret.responseMsg, ephemeral=True)

        GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_INFO if ret.result else LogLevel.LEVEL_ERROR, ret.responseMsg)
        return ret

    @sync_aware
    async def _stopGameInternal(self, guildID: int) -> Result:
        GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_WARN, "Game signaled to be stopped for guild id {guildID}.")
        ret = Result(False)
        game =GameStore().getGame(guildID)

        if not game:
            ret.responseMsg = f"No active game exists for guild \"{guildID}\", skipping stop game."
        elif isinstance(game, IAsyncDiscordGame):
            await game.destroy()
            GameStore().removeGame(guildID)
            ret.result = True
            ret.responseMsg = f"Bingo game stopped."

        if not ret.result:
            GameControllerDiscord.__LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)

        return ret
