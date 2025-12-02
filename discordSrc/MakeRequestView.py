__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IContentItem import IContentItem
from .IGateKeeper import IGateKeeper

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from discord.ui import Select, View

from game.ActionData import ActionData
from game.Bing import Bing
from game.CallRequest import CallRequest
from game.GameStore import GameStore
from game.Player import Player

from typing import List

class MakeRequestView(View, IContentItem, IGateKeeper):
    __LOGGER = ClassLogger(__name__)
    __SELECT_ID = "req_select"
    __SELECT_PLCHDR = "Select a call request..."
    __REJECTION_LIMIT = 2

    def __init__(self, gameID: int, player: Player):
        View.__init__(self, timeout=None)
        IContentItem.__init__(self, "Make call request")
        IGateKeeper.__init__(self)

        self.gameID = gameID
        self._player = player
        self._buildMenu()

        self.interaction_check = self.interactionCheck

    def refreshView(self):
        self.clear_items()
        self._buildMenu()

    async def select_callback(self, interaction: discord.Interaction):
        if not self.select.values:
            MakeRequestView.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Skipping call request selection made with no value selected.")
            return

        MakeRequestView.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Request call selection made: {self.select.values[0]}")

        game = GameStore().getGame(self.gameID)
        bingID = int(self.select.values[0])
        requestBing = self._player.card.getBingFromID(bingID)
        maxRequestsLimit = Config().getConfig("MaxRequests", 0)
        rejectionTimeout = Config().getConfig("ReqTimeoutMin", 1)

        if self._interactExpired:
            await interaction.response.send_message(f"\U0000FE0F Make request is still processing, please wait.")
        elif not game:
            await interaction.response.send_message(f"Failed to process request", ephemeral=True)
        elif not requestBing:
            errStr = "Requested call category does not exist in this players card, aborting."
            MakeRequestView.__LOGGER.log(LogLevel.LEVEL_ERROR, errStr)
            await interaction.response.send_message(errStr, ephemeral=True)
        elif requestBing.marked:
            await interaction.response.send_message(f"Slot \"{requestBing.bingStr}\" has already been marked!. If the square is not red, please wait for the board to update.", ephemeral=True)
        elif game.game.playerHasRequest(self._player, bingID):
            await interaction.response.send_message(f"\U0000FE0F You already made a call request for '{requestBing.bingStr}'", ephemeral=True)
        elif game.game.getNumRequestByPlayer(self._player) >= maxRequestsLimit:
            await interaction.response.send_message(f"\U0001F6D1 Request limit reached! You can only have up to {maxRequestsLimit} active requests at a time.", ephemeral=True)
        elif not self._player.allowedRequest(MakeRequestView.__REJECTION_LIMIT, rejectionTimeout):
            await interaction.response.send_message(f"\U0001F6D1 Your request by you has already been rejected {MakeRequestView.__REJECTION_LIMIT} times! Ignoring for {rejectionTimeout} minutes!", ephemeral=True)
        else:
            self.setInteractExpired()
            await interaction.response.defer()
            _ = game.requestCall(ActionData(interaction=interaction,
                                            callRequest=CallRequest(self._player, requestBing),
                                            **{ActionData.FINALIZE_FUNCT: self.resetExpired}))

        # Reset the dropdown for the user's view
        if interaction.message:
            self.select.values.clear()
            self.select.placeholder = MakeRequestView.__SELECT_PLCHDR
            await interaction.message.edit(view=self)

    def _buildMenu(self):
        # Get all the unmarked bings from the card in an unsorted manner
        unsortedBings: List[Bing] = []
        for row in self._player.card.getCardBings():
            for bing in row:
                if not bing.marked:
                    unsortedBings.append(bing)

        # Create select options for a sorted list of bings
        options = []
        for bing in sorted(unsortedBings, key=lambda x: x.bingIdx):
            options.append(discord.SelectOption(label=f"[{bing.bingIdx}] {bing.bingStr}", value=str(bing.bingIdx)))

        self.select = Select(
            placeholder=MakeRequestView.__SELECT_PLCHDR,
            options=options,
            custom_id=MakeRequestView.__SELECT_ID)
        self.select.callback = self.select_callback
        self.add_item(self.select)

