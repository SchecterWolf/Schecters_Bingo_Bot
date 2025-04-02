__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .GameControls import GameControls, GameControlState
from .GameGuild import GameGuild
from .IChannelInterface import IChannelInterface, ChannelView, verifyView
from .MakeCallView import MakeCallView
from .RequestView import RequestView

from config.Config import Config
from config.Globals import GLOBALVARS
from game.CallRequest import CallRequest
from typing import List

# TODO SCH rm
from config.ClassLogger import ClassLogger
from config.Log import LogLevel

class AdminChannel(IChannelInterface):
    __MSG_GAME_CONTROLS = "gamecontrols"
    __MSG_MAKE_CALL = "makecall"

    def __init__(self, gameGuild: GameGuild):
        super().__init__(gameGuild.channelAdmin)

        self.gameID = gameGuild.guildID
        self.callView = MakeCallView(gameGuild.guildID)
        self.gameControls = GameControls(gameGuild.guildID)
        self.requestsViews: List[RequestView] = []

        # TODO SCH Add the views:
        #   * Retract call
        #   * Current game admin stats (Number of times each bing has been called, etc)

    @verifyView(ChannelView.NEW)
    async def setViewNew(self):
        await self._purgeChannel()

    @verifyView(ChannelView.STARTED)
    async def setViewStarted(self):
        await self.removeNotice()
        self.gameControls.setControllsState(GameControlState.RUNNING)
        await self._updateChannelItem(AdminChannel.__MSG_GAME_CONTROLS, content=self.gameControls.msgStr, view=self.gameControls)
        await self._updateChannelItem(AdminChannel.__MSG_MAKE_CALL, content=self.callView.msgStr, view=self.callView)
        await self._addAllRequestViews()

    @verifyView(ChannelView.PAUSED)
    async def setViewPaused(self):
        self.gameControls.setControllsState(GameControlState.PAUSED)
        await self._updateChannelItem(AdminChannel.__MSG_GAME_CONTROLS, content=self.gameControls.msgStr, view=self.gameControls)
        await self._deleteChannelItem(AdminChannel.__MSG_MAKE_CALL)
        await self._delAllRequestViews()
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_PAUSED))

    @verifyView(ChannelView.STOPPED)
    async def setViewStopped(self):
        await self._purgeChannel()
        self.gameControls.setControllsState(GameControlState.ENDED)
        await self._updateChannelItem(AdminChannel.__MSG_GAME_CONTROLS, content=self.gameControls.msgStr, view=self.gameControls)
        await self.sendNotice(Config().getFormatConfig("StreamerName", GLOBALVARS.GAME_MSG_ENDED))

    async def addCallRequest(self, request: CallRequest):
        requestView = None
        for req in self.requestsViews:
            if request.isMatchingRequest(req.callRequest):
                requestView = req
                break

        # Update the request view, or add a new one if necessary
        if requestView:
            requestView.callRequest.mergeRequests(request)
        else:
            requestView = RequestView(self.gameID, request)
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

    async def _addAllRequestViews(self):
        ClassLogger(__name__).log(LogLevel.LEVEL_DEBUG, "Adding all request views")
        for req in self.requestsViews:
            await self._updateChannelItem(req.viewID, content=req.viewText, view=req)

    async def _delAllRequestViews(self):
        for req in self.requestsViews:
            await self._deleteChannelItem(req.viewID)

