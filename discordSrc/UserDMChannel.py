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

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from discord.channel import DMChannel
from game.CardImgCreator import CardImgCreator
from game.GameStore import GameStore
from game.Player import Player

class UserDMChannel(IChannelInterface):
    __LOGGER = ClassLogger(__name__)
    __MSG_BINGO_BOARD = "bingoboard"
    __MSG_REQUEST_CALL = "requestcall"
    __GAME_CARD_TITLE = "{StreamerName} Livestream Bingo Card"

    def __init__(self, gameID: int, channel: DMChannel, player: Player):
        super().__init__(channel)

        self.player = player
        self.requestView = MakeRequestView(gameID, self.player)
        self.gameType = "--"

        game = GameStore().getGame(gameID)
        if game:
            self.gameType = game.game.gameType

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
        await self._deleteChannelItem(UserDMChannel.__MSG_REQUEST_CALL)
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_ENDED))

    async def setViewKicked(self, action: str):
        await self._purgeChannel()
        await self.sendNotice(f"\U0000274C\U0001F528 Sorry, you have been {action} from playing the livestream bingo.")

    async def refreshRequestView(self):
        # Skipping updating the request view since it uses too many API calls, and sometimes causes throttles with large # of players.
        pass

    async def setBoardView(self):
        UserDMChannel.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Updating player card for player \"{self.player.card.getCardOwner()}\"")
        filename = f"board_{self.player.userID}.png"
        titleName = Config().getFormatConfig("StreamerName", UserDMChannel.__GAME_CARD_TITLE) \
                    + f" [{self.gameType}]"
        embed = discord.Embed(title=titleName, color=discord.Color.green())
        file = discord.File(CardImgCreator().createGraphicalCard(self.player.card), filename)

        embed.set_image(url=f"attachment://{filename}")

        if not self._hasChannelItem(UserDMChannel.__MSG_BINGO_BOARD):
            await self._updateChannelItem(UserDMChannel.__MSG_BINGO_BOARD, file=file, embed=embed)
        else:
            await self._updateChannelItem(UserDMChannel.__MSG_BINGO_BOARD, embed=embed, attachments=[file])

