__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .AddPlayerButton import AddPlayerButton
from .GameGuild import GameGuild
from .GameStatusEmbed import GameStatusEmbed
from .IChannelInterface import IChannelInterface, ChannelView, verifyView
from .ServerGlobalStats import ServerGlobalStats

from config.Config import Config
from config.Globals import GLOBALVARS

class BingoChannel(IChannelInterface):
    __MSG_ADD_PLAYER = "addplayer"
    __MSG_GAME_STATUS = "gamestatus"
    __MSG_GLOBAL_STATS = "global"

    def __init__(self, guild: GameGuild):
        super().__init__(guild.channelBingo)

        self.globalEmbed = ServerGlobalStats(guild.persistentStats)
        self.gameStatus = GameStatusEmbed(guild.guildID)
        self.addPlayer = AddPlayerButton(guild.guildID)

    @verifyView(ChannelView.NEW)
    async def setViewNew(self):
        await self._purgeChannel()
        await self._updateChannelItem(BingoChannel.__MSG_GLOBAL_STATS, embed=self.globalEmbed)

    @verifyView(ChannelView.STARTED)
    async def setViewStarted(self):
        await self._purgeChannel()
        await self._updateChannelItem(BingoChannel.__MSG_ADD_PLAYER, content=self.addPlayer.msgStr, view=self.addPlayer)
        await self._updateChannelItem(BingoChannel.__MSG_GLOBAL_STATS, embed=self.globalEmbed)
        await self._updateChannelItem(BingoChannel.__MSG_GAME_STATUS, embed=self.gameStatus)

    @verifyView(ChannelView.PAUSED)
    async def setViewPaused(self):
        await self.removeNotice()
        await self._updateChannelItem(BingoChannel.__MSG_ADD_PLAYER, content=f"{self.addPlayer.msgStr} <paused>")
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_PAUSED))

    @verifyView(ChannelView.STOPPED)
    async def setViewStopped(self):
        await self._purgeChannel()

        self.globalEmbed.refreshStats()
        await self._updateChannelItem(BingoChannel.__MSG_GLOBAL_STATS, embed=self.globalEmbed)

        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_ENDED))
        # TODO SCH Add some post-game detailed stats

    async def refreshGameStatus(self):
        self.gameStatus.refreshStats()
        await self._updateChannelItem(BingoChannel.__MSG_GAME_STATUS, embed=self.gameStatus)

