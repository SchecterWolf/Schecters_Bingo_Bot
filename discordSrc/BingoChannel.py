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
from typing import Optional

class BingoChannel(IChannelInterface):
    __MSG_ADD_PLAYER = "addplayer"
    __MSG_GAME_STATUS = "gamestatus"
    __MSG_GLOBAL_STATS = "global"

    def __init__(self, bot: discord.Client, guild: GameGuild):
        super().__init__(guild.channelBingo)
        self.cachedLeaderboard: Optional[bytes] = None
        self.cachedFilename = ""

        self.leaderboard = LeaderboardCreator(bot, guild.persistentStats)
        self.gameStatus = GameStatusEmbed(guild.guildID)
        self.addPlayer = AddPlayerButton(guild.guildID)
        self.showAddBtn = False

    @verifyView(ChannelView.NEW)
    async def setViewNew(self):
        pass

    @verifyView(ChannelView.STARTED)
    async def setViewStarted(self):
        self.showAddBtn = True
        self.gameStatus.reloadFile()

        await self._purgeChannel()
        await self._updateChannelItem(BingoChannel.__MSG_GLOBAL_STATS, file=await self._getLeaderBoardFile())
        await self._updateChannelItem(BingoChannel.__MSG_GAME_STATUS, embed=self.gameStatus, file=self.gameStatus.file)
        await self._updateChannelItem(BingoChannel.__MSG_ADD_PLAYER, content=self.addPlayer.msgStr, view=self.addPlayer)

    @verifyView(ChannelView.PAUSED)
    async def setViewPaused(self):
        self.showAddBtn = False
        await self.removeNotice()
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_PAUSED))

    @verifyView(ChannelView.STOPPED)
    async def setViewStopped(self):
        self.showAddBtn = False
        await self._purgeChannel()
        await self._updateChannelItem(BingoChannel.__MSG_GLOBAL_STATS, file=await self._getLeaderBoardFile(True))

        self.gameStatus.conclude()
        await self._updateChannelItem(BingoChannel.__MSG_GAME_STATUS, embed=self.gameStatus)

        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_ENDED))

    async def refreshGameStatus(self):
        self.gameStatus.refreshStats()
        await self._updateChannelItem(BingoChannel.__MSG_GAME_STATUS, embed=self.gameStatus)

    # We need to make sure the add player button is always last in the bingo channel
    async def sendNoticeItem(self, **kwargs):
        await self._deleteChannelItem(BingoChannel.__MSG_ADD_PLAYER)
        if self.showAddBtn:
            kwargs['view'] = self.addPlayer
        await super().sendNoticeItem(**kwargs)

    async def _getLeaderBoardFile(self, forceRefresh: bool = False) -> discord.File:
        if self.cachedLeaderboard and not forceRefresh:
            fileLeaderBoard = discord.File(BytesIO(self.cachedLeaderboard), filename=self.cachedFilename)
        else:
            fileLeaderBoard = await self.leaderboard.createAsset()
            fileLeaderBoard.fp.seek(0)
            self.cachedLeaderboard = fileLeaderBoard.fp.read()
            self.cachedFilename = fileLeaderBoard.filename
            fileLeaderBoard.fp.seek(0)

        return fileLeaderBoard

