__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IContentItem import IContentItem

from config.ClassLogger import ClassLogger, LogLevel
from discord.ui import Button, View
from game.ActionData import ActionData
from game.CallRequest import CallRequest
from game.GameStore import GameStore
from game.NotificationMessageMaker import MakeCallRequestNotif

class RequestView(View, IContentItem):
    __LOGGER = ClassLogger(__name__)
    __btn_accept_label = "Accept Request"
    __btn_accept_id = "accept_req"
    __btn_reject_label = "Reject Request"
    __btn_reject_id = "reject_req"

    def __init__(self, gameID:int, request: CallRequest):
        View.__init__(self, timeout=None)
        IContentItem.__init__(self, "Call requests")

        self.gameID = gameID
        self.callRequest = request
        self.viewID = f"request_{request.requestBing.bingIdx}"
        self.interactExpired = False

        # Set the request caption text
        self.viewText = MakeCallRequestNotif(self.callRequest)

        acceptButton = Button(
            label=RequestView.__btn_accept_label,
            style=discord.ButtonStyle.primary,
            custom_id=RequestView.__btn_accept_id)
        acceptButton.callback = self.accept_callback
        self.add_item(acceptButton)

        rejectButton = Button(
            label=RequestView.__btn_reject_label,
            style=discord.ButtonStyle.danger,
            custom_id=RequestView.__btn_reject_id)
        rejectButton.callback = self.reject_callback
        self.add_item(rejectButton)

    def updateRequest(self, request: CallRequest):
        if not self.callRequest.isMatchingRequest(request):
            RequestView.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Cannot update request view with a different type of request. \
This view has request ID ({self.callRequest.requestBing.bingIdx}) and the update request has ID ({request.requestBing.bingIdx})")
            return

        RequestView.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Request has {len(request.players)} players") # TODO SCH rm
        self.callRequest = request
        self.viewText = MakeCallRequestNotif(self.callRequest)
        RequestView.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Request text: {self.viewText}") # TODO SCH rm

    async def interaction_check(self, _: discord.Interaction):
        return not self.interactExpired

    async def accept_callback(self, interaction: discord.Interaction):
        RequestView.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Accept request button pressed.")
        expired = self.interactExpired
        self.interactExpired = True
        await interaction.response.defer()

        game = GameStore().getGame(self.gameID)
        if not expired and game:
            _ = game.makeCall(ActionData(interaction=interaction, index=self.callRequest.requestBing.bingIdx))

    async def reject_callback(self, interaction: discord.Interaction):
        RequestView.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Reject request button pressed.")
        expired = self.interactExpired
        self.interactExpired = True
        await interaction.response.defer()

        game = GameStore().getGame(self.gameID)
        if not expired and game:
            _ = game.deleteRequest(ActionData(index=self.callRequest.requestBing.bingIdx))

