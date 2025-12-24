__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .AdminCommandHandler import AdminCommandHandler
from .DebugCommandHandler import DebugCommandHandler
from .GameControllerDiscord import GameControllerDiscord
from .GameGuild import GameGuild
from .ICommandHandler import ICommandHandler
from .LeaderboardCreator import LeaderboardCreator
from .PlayerCommandHandler import PlayerCommandHandler
from .StartGameButton import StartGameButton

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS

from discord.client import Client
from discord.ui import View

from game.GameStore import GameStore
from game.IGameInterface import IGameInterface
from game.PersistentStats import PersistentStats

from typing import Optional

class Bot(Client):
    __LOGGER = ClassLogger(__name__)
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        # Init guard
        if hasattr(self, "initialized"):
            return

        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.guilds = True
        intents.dm_messages = True
        intents.members = True
        super().__init__(intents=intents)

        self.gameGuilds: dict[int, GameGuild] = {}
        self.debugCommands: Optional[DebugCommandHandler] = None

        self.initialized = True

    def runBot(self) -> bool:
        token = ""
        tokenFile = Config().getConfig('TokenFile')
        with open(f"{GLOBALVARS.PROJ_ROOT}/{tokenFile}") as file:
            token = file.readline()
        self.run(token, root_logger=True) # Blocks

        return True

    async def stopBot(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, "Shutting down discord bot...")
        for guildID in self.gameGuilds:
            GameStore().removeGame(guildID)
        self.gameGuilds.clear()
        await self.close()

    async def setup_hook(self):
        self.tree = discord.app_commands.CommandTree(self)
        self.slashCommands: list[ICommandHandler] = [
            AdminCommandHandler(),
            PlayerCommandHandler()
        ]
        if Config().getConfig("Debug"):
            self.slashCommands.append(DebugCommandHandler())

        for cmds in self.slashCommands:
            cmds.setupCommands(self.tree)
        # Apparently this only has to be done once to register the commands
        # TODO make this automatic. have it touch a file in the config dir once it
        # registers the slash commands
        if False:
            print("SLASH COMMANDS SYNCING")
            try:
                Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, "Bot commands are syncing...")
                await self.tree.sync()
            except Exception as e:
                Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Failed to sync bot commands: {e}")

    # TODO I need to account for the situation if the bot gets disconnected then reconnects
    async def on_ready(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_INFO, f"Discord bot logged in as {self.user}")
        for guild in self.guilds:
            await self.on_guild_join(guild)

        GameStore().addController(GameControllerDiscord(self, self.gameGuilds))

    async def on_guild_join(self, guild: discord.Guild):
        """
        Called whenever this bot is added to a discord server or when the bot is
        starting up
        """
        if guild.id in Config().getConfig("SkipServer", []):
            Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Guild \"{guild.name}\" marked as skiped.... skipping!")
            return

        Bot.__LOGGER.log(LogLevel.LEVEL_INFO, f"Initializing guild: {guild.name}")
        persistentStats = PersistentStats(guild.id)

        # Get the regular bingo channel
        try:
            channelBingo = discord.utils.get(guild.text_channels, name=GLOBALVARS.CHANNEL_BINGO)
            if channelBingo:
                await channelBingo.purge()
                await channelBingo.send(GLOBALVARS.GAME_MSG_STARTUP, file=await LeaderboardCreator(self, persistentStats).createAsset())
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
                await channelAdmin.send(GLOBALVARS.GAME_MSG_STARTUP, view=startView)
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
        Bot.__LOGGER.log(LogLevel.LEVEL_WARN, f"Guild signaled for removal: {guild.name}.")
        gg: Optional[GameGuild] = self.gameGuilds.pop(guild.id, None)
        activeGame: Optional[IGameInterface] = None

        if not gg:
            Bot.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Could not find guild \"{guild.name}\" for removal.")
        else:
            activeGame = GameStore().getGame(guild.id)

        if activeGame:
            Bot.__LOGGER.log(LogLevel.LEVEL_WARN, f"Force shutting down active game for guild \"{guild.name}\"...")
            activeGame.destroy()

        if gg:
            Bot.__LOGGER.log(LogLevel.LEVEL_WARN, f"Guild \"{guild.name}\" has been removed.")

    # Note: This also gets called when the SDK times out client side
    async def on_disconnect(self):
        Bot.__LOGGER.log(LogLevel.LEVEL_CRIT, "Bot has been disconnected.")

    def _addGuild(self, gg: GameGuild):
        if self.gameGuilds.get(gg.guildID):
            Bot.__LOGGER.log(LogLevel.LEVEL_WARN, f"Guild id \"{gg.guildID}\" is already registered.")
        else:
            Bot.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Server \"{gg.guildID}\" has been registered to use bingo.")
            self.gameGuilds[gg.guildID] = gg

