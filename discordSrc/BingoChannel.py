__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .AddPlayerButton import AddPlayerButton
from .GameGuild import GameGuild
from .GameStatusEmbed import GameStatusEmbed
from .IChannelInterface import IChannelInterface, ChannelView, verifyView
from .LeaderboardCreator import LeaderboardCreator

from config.Config import Config
from config.Globals import GLOBALVARS
from io import BytesIO

class BingoChannel(IChannelInterface):
    __MSG_ADD_PLAYER = "addplayer"
    __MSG_GAME_STATUS = "gamestatus"
    __MSG_GLOBAL_STATS = "global"

    def __init__(self, bot: discord.Client, guild: GameGuild):
        super().__init__(guild.channelBingo)
        self.fileLeaderBoard = None

        self.leaderboard = LeaderboardCreator(bot, guild.persistentStats)
        self.gameStatus = GameStatusEmbed(guild.guildID)
        self.addPlayer = AddPlayerButton(guild.guildID)

    @verifyView(ChannelView.NEW)
    async def setViewNew(self):
        pass

    @verifyView(ChannelView.STARTED)
    async def setViewStarted(self):
        await self._purgeChannel()
        await self._updateChannelItem(BingoChannel.__MSG_GLOBAL_STATS, file=await self._getLeaderBoardFile())
        await self._updateChannelItem(BingoChannel.__MSG_GAME_STATUS, embed=self.gameStatus, file=self.gameStatus.file)
        await self._updateChannelItem(BingoChannel.__MSG_ADD_PLAYER, content=self.addPlayer.msgStr, view=self.addPlayer)

    @verifyView(ChannelView.PAUSED)
    async def setViewPaused(self):
        await self.removeNotice()
        await self._updateChannelItem(BingoChannel.__MSG_ADD_PLAYER, content=f"{self.addPlayer.msgStr} <paused>")
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_PAUSED))

    @verifyView(ChannelView.STOPPED)
    async def setViewStopped(self):
        await self._purgeChannel()
        await self._updateChannelItem(BingoChannel.__MSG_GLOBAL_STATS, file=await self._getLeaderBoardFile(True))

        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_ENDED))
        # TODO SCH Add some post-game detailed stats

    async def refreshGameStatus(self):
        self.gameStatus.refreshStats()
        await self._updateChannelItem(BingoChannel.__MSG_GAME_STATUS, embed=self.gameStatus)

    # We need to make sure the add player button is always last in the bingo channel
    async def sendNoticeItem(self, **kwargs):
        await self._deleteChannelItem(BingoChannel.__MSG_ADD_PLAYER)
        kwargs['view'] = self.addPlayer
        await super().sendNoticeItem(**kwargs)

    async def _getLeaderBoardFile(self, forceRefresh: bool = False) -> discord.File:
        if not self.fileLeaderBoard or forceRefresh:
            self.fileLeaderBoard = await self.leaderboard.createAsset()
        return self.fileLeaderBoard or discord.File(BytesIO())

