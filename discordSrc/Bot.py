__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord
import logging # TODO SCH rm

from .DebugCommandHandler import DebugCommandHandler
from .GameControllerDiscord import GameControllerDiscord
from .GameGuild import GameGuild
from .ServerGlobalStats import ServerGlobalStats
from .StartGameButton import StartGameButton

from config.ClassLogger import ClassLogger
from config.Config import Config
from config.Globals import GLOBALVARS
from config.Log import LogLevel

from discord.client import Client
from discord.ui import View

from game.GameStore import GameStore
from game.PersistentStats import PersistentStats

from typing import Union

class Bot(Client):
    __LOGGER = ClassLogger(__name__)
    __STARTUP_MSG = "Schecter's Bingo Bot started!"

    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.guilds = True
        intents.dm_messages = True
        super().__init__(intents=intents)

        self.gameGuilds: dict[int, GameGuild] = {}
        self.debugCommands: Union[None, DebugCommandHandler] = None

    def runBot(self) -> bool:
        token = ""
        tokenFile = Config().getConfig('TokenFile')
        with open(f"{GLOBALVARS.PROJ_ROOT}/{tokenFile}") as file:
            token = file.readline()
        #self.run(token, log_level=logging.DEBUG, root_logger=True) # Blocks # TODO SCH
        self.run(token, log_level=logging.INFO, root_logger=True) # Blocks

        return True

    async def stopBot(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, "Shutting down discord bot...")
        for guildID in self.gameGuilds:
            GameStore().removeGame(guildID)
        self.gameGuilds.clear()
        await self.close()

    async def setup_hook(self):
        if Config().getConfig("Debug"):
            self.debugCommands = DebugCommandHandler(self)
            self.debugCommands.setupCommands()
            await self.debugCommands.syncCommands()

    # TODO I need to account for the situation if the bot gets disconnected then reconnects
    async def on_ready(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_INFO, f"Discord bot logged in as {self.user}")
        for guild in self.guilds:
            await self.on_guild_join(guild)

        GameStore().addController(GameControllerDiscord(self.gameGuilds, self.loop))

    async def on_guild_join(self, guild: discord.Guild):
        """
        Called whenever this bot is added to a discord server or when the bot is
        starting up
        """
        Bot.__LOGGER.log(LogLevel.LEVEL_INFO, f"Initializing guild: {guild.name}")
        persistentStats = PersistentStats()

        # Get the regular bingo channel
        try:
            channelBingo = discord.utils.get(guild.text_channels, name=GLOBALVARS.CHANNEL_BINGO)
            if channelBingo:
                await channelBingo.purge()
                await channelBingo.send(Bot.__STARTUP_MSG, embed=ServerGlobalStats(persistentStats))
        except Exception as e:
            self.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Could not set up bingo channel for guild {guild.id}: {e}")
            return

        # Get the bingo admin channel
        try:
            Bot.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Initializing the admin bingo channel for the guild.")
            channelAdmin = discord.utils.get(guild.text_channels, name=GLOBALVARS.CHANNEL_ADMIN_BINGO)
            if channelAdmin:
                await channelAdmin.purge()

                # Bootstrap the start game button
                startView = View(timeout=None)
                startButton = StartGameButton()
                startButton.addToView(startView)
                await channelAdmin.send(Bot.__STARTUP_MSG, view=startView)
        except Exception as e:
            self.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Could not set up admin channel for guild \"{guild.name}\" ({guild.id}): {e}")
            if channelBingo:
                await channelBingo.purge()
            return

        if channelBingo and channelAdmin:
            self._addGuild(GameGuild(guild.id, persistentStats, channelBingo, channelAdmin))

    async def on_guild_remove(self, guild: discord.Guild):
        """
        Called whenever this bot is removed from a discord server
        """
        # TODO SCH Stop any games associated with this guild and then remove from gameGuilds
        pass

    async def on_disconnect(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, "Bot has been disconnected.")

    def _addGuild(self, gg: GameGuild):
        if self.gameGuilds.get(gg.guildID):
            Bot.__LOGGER.log(LogLevel.LEVEL_WARN, f"Guild id \"{gg.guildID}\" is already registered.")
        else:
            Bot.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Server \"{gg.guildID}\" has been registered to use bingo.")
            self.gameGuilds[gg.guildID] = gg

