__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .GameControls import GameControls, GameControlState
from .GameGuild import GameGuild
from .IChannelInterface import IChannelInterface, ChannelView, verifyView
from .MakeCallView import MakeCallView
from .RequestView import RequestView

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from game.CallRequest import CallRequest
from typing import List, Optional

class AdminChannel(IChannelInterface):
    __LOGGER = ClassLogger(__name__)
    __MSG_GAME_CONTROLS = "gamecontrols"
    __MSG_MAKE_CALL = "makecall"

    def __init__(self, gameGuild: GameGuild, gameType: str, gameMasterRole: Optional[discord.Role]):
        super().__init__(gameGuild.channelAdmin)

        self.gameID = gameGuild.guildID
        self.callView = MakeCallView(gameGuild.guildID, gameType)
        self.gameControls = GameControls(gameGuild.guildID)
        self.requestsViews: List[RequestView] = []
        self.gameMasterRole: Optional[discord.Role] = gameMasterRole

    async def setViewIdle(self):
        botInfo = self.getFormattedBotInfo(Config().getBotVersion())
        self.gameControls.setControllsState(GameControlState.ENDED)

        # Add Github link
        botInfo += f"\n{GLOBALVARS.GAME_MSG_GITHUB}"

        await self._purgeChannel()
        await self._channel.send(botInfo, view=self.gameControls)

    @verifyView(ChannelView.NEW)
    async def setViewNew(self):
        ClassLogger(__name__).log(LogLevel.LEVEL_DEBUG, "setViewNew called")
        await self._purgeChannel()
        await self.sendNotice("Setting up game...")

    @verifyView(ChannelView.STARTED)
    async def setViewStarted(self):
        ClassLogger(__name__).log(LogLevel.LEVEL_DEBUG, "setViewStarted called")
        await self.removeNotice()
        self.gameControls.setControllsState(GameControlState.RUNNING)
        await self._updateChannelItem(AdminChannel.__MSG_GAME_CONTROLS, content=self.gameControls.msgStr, view=self.gameControls)
        await self._addAllCallViews()
        await self._addAllRequestViews()

    @verifyView(ChannelView.PAUSED)
    async def setViewPaused(self):
        self.gameControls.setControllsState(GameControlState.PAUSED)
        await self._updateChannelItem(AdminChannel.__MSG_GAME_CONTROLS, content=self.gameControls.msgStr, view=self.gameControls)
        await self._delAllCallViews()
        await self._delAllRequestViews()
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_PAUSED))

    @verifyView(ChannelView.STOPPED)
    async def setViewStopped(self):
        await self.setViewIdle()
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_ENDED))

    async def addCallRequest(self, request: CallRequest):
        AdminChannel.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Adding call request ID ({request.requestBing.bingIdx}) to the admin channel view.")
        requestView = None
        for req in self.requestsViews:
            if request.isMatchingRequest(req.callRequest):
                requestView = req
                break

        # Update the request view, or add a new one if necessary
        if requestView:
            requestView.updateRequest(request)
        else:
            requestView = RequestView(self.gameID, request, self.gameMasterRole)
            self.requestsViews.append(requestView)

        # Update the view in discord
        await self._updateChannelItem(requestView.viewID, content=requestView.viewText, view=requestView)

    async def delCallRequest(self, index: int):
        reqViewDelta: List[RequestView] = []
        removedViews: List[RequestView] = []

        # Sort through the request views
        for req in self.requestsViews:
            if req.callRequest.requestBing.bingIdx != index:
                reqViewDelta.append(req)
            else:
                removedViews.append(req)

        # Update the request views that are still outstanding
        self.requestsViews = reqViewDelta

        # Remove the necessary request views from the channel
        for req in removedViews:
            await self._deleteChannelItem(req.viewID)

    async def _addAllCallViews(self):
        if Config().getConfig('CasualMode', False):
            await self._updateChannelItem(AdminChannel.__MSG_MAKE_CALL, content="(Game is in Casual Mode)")
            return

        cv: Optional[MakeCallView] = self.callView
        while cv:
            await self._updateChannelItem(AdminChannel.__MSG_MAKE_CALL + str(id(cv)), content=cv.msgStr, view=cv)
            cv = cv.getCascadedCallView()

    async def _delAllCallViews(self):
        cv: Optional[MakeCallView] = self.callView
        while cv:
            await self._deleteChannelItem(AdminChannel.__MSG_MAKE_CALL + str(id(cv)))
            cv = cv.getCascadedCallView()

    async def _addAllRequestViews(self):
        for req in self.requestsViews:
            await self._updateChannelItem(req.viewID, content=req.viewText, view=req)

    async def _delAllRequestViews(self):
        for req in self.requestsViews:
            await self._deleteChannelItem(req.viewID)

