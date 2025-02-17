__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IContentItem import IContentItem
from config.ClassLogger import ClassLogger
from config.Log import LogLevel
from discord.ui import Select, View
from game.ActionData import ActionData
from game.Bing import Bing
from game.CallRequest import CallRequest
from game.GameStore import GameStore
from game.Player import Player
from typing import List

class MakeRequestView(View, IContentItem):
    __LOGGER = ClassLogger(__name__)
    __SELECT_ID = "req_select"
    __SELECT_PLCHDR = "Select a call request..."

    def __init__(self, gameID: int, player: Player):
        View.__init__(self, timeout=None)
        IContentItem.__init__(self, "Make call request")

        self.gameID = gameID
        self._player = player
        self._buildMenu()

    def refreshView(self):
        self.clear_items()
        self._buildMenu()

    async def select_callback(self, interaction: discord.Interaction):
        MakeRequestView.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Request call selection made: {self.select.values[0]}")

        game = GameStore().getGame(self.gameID)
        requestBing = self._player.card.getBingFromID(int(self.select.values[0]))
        if not requestBing:
            errStr = "Requested call category does not exist in this players card, aborting."
            MakeRequestView.__LOGGER.log(LogLevel.LEVEL_ERROR, errStr)
            await interaction.response.send_message(errStr, ephemeral=True)
        elif requestBing.marked:
            await interaction.response.send_message(f"Slot \"{requestBing.bingStr}\" has already been marked!.", ephemeral=True)
        else:
            await interaction.response.defer()
            # TODO SCH I need to limit this per player to 2 max
            if game:
                _ = game.requestCall(ActionData(interaction=interaction, callRequest=CallRequest(self._player, requestBing)))

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

