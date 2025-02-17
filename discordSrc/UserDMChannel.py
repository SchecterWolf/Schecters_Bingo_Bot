__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord
import os

from .IChannelInterface import IChannelInterface, ChannelView, verifyView
from .MakeRequestView import MakeRequestView

from config.ClassLogger import ClassLogger
from config.Config import Config
from config.Globals import GLOBALVARS
from config.Log import LogLevel
from discord.channel import DMChannel
from game.CardImgCreator import CardImgCreator
from game.Player import Player

class UserDMChannel(IChannelInterface):
    __LOGGER = ClassLogger(__name__)
    __MSG_BINGO_BOARD = "bingoboard"
    __MSG_REQUEST_CALL = "requestcall"

    def __init__(self, gameID: int, channel: DMChannel, player: Player):
        super().__init__(channel)

        self.player = player
        self.requestView = MakeRequestView(gameID, self.player)
        self.cardFile = ""

    @verifyView(ChannelView.NEW)
    async def setViewNew(self):
        await self._purgeChannel()

    @verifyView(ChannelView.STARTED)
    async def setViewStarted(self):
        await self.setViewNew()
        await self.setBoardView()
        await self._updateChannelItem(UserDMChannel.__MSG_REQUEST_CALL, content=self.requestView.msgStr, view=self.requestView)

    @verifyView(ChannelView.PAUSED)
    async def setViewPaused(self):
        await self._deleteChannelItem(UserDMChannel.__MSG_REQUEST_CALL)
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_PAUSED))

    @verifyView(ChannelView.STOPPED)
    async def setViewStopped(self):
        UserDMChannel.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Setting DM channel to stopped for player: {self.player.card.getCardOwner()}.") # TODO SCH rm
        await self._deleteChannelItem(UserDMChannel.__MSG_REQUEST_CALL)
        await self.removeNotice()
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_ENDED))
        if self.cardFile and os.path.exists(self.cardFile):
            try:
                os.remove(self.cardFile)
                UserDMChannel.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Deleted user card {self.cardFile}")
            except Exception as e:
                UserDMChannel.__LOGGER.log(LogLevel.LEVEL_ERROR, "Failed to remove card file for player \"{self.player.card.getCardOwner()}\": {e}")

    async def refreshRequestView(self):
        UserDMChannel.__LOGGER.log(LogLevel.LEVEL_DEBUG, "refreshRequestView called") # TODO SCH rm
        self.requestView.refreshView()
        await self._updateChannelItem(UserDMChannel.__MSG_REQUEST_CALL, content=self.requestView.msgStr, view=self.requestView)

    async def setBoardView(self):
        UserDMChannel.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Updating player card for player \"{self.player.card.getCardOwner()}\"")
        embed = discord.Embed(title="Max Livestream Bingo Card", color=discord.Color.green())
        self.cardFile, cardName = CardImgCreator().createGraphicalCard(self.player.card)
        file = discord.File(self.cardFile, filename=cardName)
        embed.set_image(url=f"attachment://{cardName}")

        if not self._hasChannelItem(UserDMChannel.__MSG_BINGO_BOARD):
            await self._updateChannelItem(UserDMChannel.__MSG_BINGO_BOARD, file=file, embed=embed)
        else:
            await self._updateChannelItem(UserDMChannel.__MSG_BINGO_BOARD, embed=embed, attachments=[file])
        UserDMChannel.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Updating player card finished") # TODO SCH rm

