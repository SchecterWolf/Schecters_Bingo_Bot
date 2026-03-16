__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .AdminCommandHandler import AdminCommandHandler
from .AdminChannel import AdminChannel
from .BingoChannel import BingoChannel
from .DebugCommandHandler import DebugCommandHandler
from .GameControllerDiscord import GameControllerDiscord
from .GameGuild import GameGuild
from .ICommandHandler import ICommandHandler
from .PlayerCommandHandler import PlayerCommandHandler

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS

from discord.client import Client

from game.GameStore import GameStore
from game.IGameInterface import IGameInterface
from game.PersistentStats import PersistentStats
from game.Recovery import Recovery

from typing import Optional, cast

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
        self.hasRecovery = False
        self.recovery = None

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

        # Finish starting the recovery game, if any
        gameController = GameStore().getController()
        if self.hasRecovery and self.recovery and gameController:
            Bot.__LOGGER.log(LogLevel.LEVEL_WARN, f"Game recovery found for server ID {self.recovery.gameID}, starting game recovery...")
            result = await gameController.startGameFromRecovery(self.recovery.gameID)

            # If for whatever reason we couldn't successfully set up the recovery, restart without the setup without the recovery
            if not result:
                Bot.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Failed to recover the game. Falling back to init state...")
                self.recovery.removeRecovery()
                await self.on_guild_join(self.guilds[0])

            self.hasRecovery = False

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
        self.recovery = Recovery(guild.id)
        self.hasRecovery = self.recovery.hasRecovery()

        # If there is a game already in progress, ignore recovery. (This shouldn't ever happen)
        if GameStore().getGame(guild.id):
            self.hasRecovery = False

        # Get the regular bingo channel
        try:
            channelBingo = None
            channelBingoID = Config().getConfig('ChannelBingo')
            if channelBingoID:
                channelBingo = guild.get_channel(channelBingoID)
                if not isinstance(channelBingo, discord.TextChannel):
                    self.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Bingo Channel ID ({channelBingoID}) does not appear to be a Text Channel. Please make sure to configure a text channel ID.")
                    channelBingo = None

            if channelBingo and not self.hasRecovery:
                tempGG = GameGuild(guild.id, persistentStats, channelBingo, channelBingo)
                bingoChannel = BingoChannel(self, tempGG)
                await bingoChannel.setViewIdle()
        except Exception as e:
            self.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Could not set up bingo channel for guild {guild.id}: {e}")
            return

        # Get the bingo admin channel
        try:
            Bot.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Initializing the admin bingo channel for the guild.")

            channelAdmin = None
            channelAdminID = Config().getConfig('ChannelAdmin')
            if channelAdminID:
                channelAdmin = guild.get_channel(channelAdminID)
                if not isinstance(channelAdmin, discord.TextChannel):
                    self.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Admin Bingo Channel ID ({channelAdminID}) does not appear to be a Text Channel. Please make sure to configure a text channel ID.")
                    channelAdmin = None

            if channelAdmin and not self.hasRecovery:
                # Bootstrap the start game button
                tempGG = GameGuild(guild.id, persistentStats, channelAdmin, channelAdmin)
                adminChannel = AdminChannel(tempGG, "", None)
                await adminChannel.setViewIdle()
        except Exception as e:
            self.__LOGGER.log(LogLevel.LEVEL_CRIT, f"Could not set up admin channel for guild \"{guild.name}\" ({guild.id}): {e}")
            if channelBingo:
                await channelBingo.purge()
            return

        # Get the general channel (optional)
        channelGeneralID = Config().getConfig('ChannelGeneral', 0)
        channelGeneral: Optional[discord.TextChannel] = None
        if channelGeneralID:
            try:
                channel = guild.get_channel(channelGeneralID)
                if isinstance(channel, discord.TextChannel):
                    channelGeneral = cast(discord.TextChannel, channel)
                else:
                    self.__LOGGER.log(LogLevel.LEVEL_ERROR, f"General Channel ID ({channelGeneralID}) does not appear to be a Text Channel. Please make sure to configure a text channel ID.")
            except Exception as e:
                pass

            if not channelGeneral:
                self.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Could not find the general channel for configured id {channelGeneralID}, Skipping.")

        # Add this guild to the game guilds
        if channelBingo and channelAdmin:
            self._addGuild(GameGuild(guild.id, persistentStats, channelBingo, channelAdmin, channelGeneral))

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
            Recovery(guild.id).removeRecovery()

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

