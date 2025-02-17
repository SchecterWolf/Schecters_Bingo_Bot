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
from game.Binglets import Binglets
from game.GameStore import GameStore
from typing import Awaitable, Callable, List

class SelectCall(Select):
    __LOGGER = ClassLogger(__name__)
    __SELECT_ID = "call_select"

    def __init__(self, gameID: int, key: str, bingList: List[Bing],
                 refresh: Callable[[discord.Interaction], Awaitable[None]]):
        super().__init__()
        SelectCall.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Select made for call key: {key}")

        self.gameID = gameID
        self.refreshCallback = refresh
        self.placeholderVal = f"Calls for {key}"

        # Select properties
        self.placeholder=self.placeholderVal
        for bing in bingList:
            self.options.append(discord.SelectOption(label=f"[{bing.bingIdx}] {bing.bingStr}", value=str(bing.bingIdx)))
        self.custom_id=f"{SelectCall.__SELECT_ID}_{key}"
        self.max_values = 1
        self.min_values = 1

    async def callback(self, interaction: discord.Interaction):
        SelectCall.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Call selection made: {self.values[0]}")
        callIndex = int(self.values[0])

        # Revert the select menu display
        self.values.clear()
        self.placeholder = self.placeholderVal
        await interaction.response.defer()
        await self.refreshCallback(interaction)

        # TODO SCH Use the interaction_check mechanic to guard the select interaction. Disable until call is finished somehow
        game = GameStore().getGame(self.gameID)
        if game:
            _ = game.makeCall(ActionData(interaction=interaction, index=callIndex))

class MakeCallView(View, IContentItem):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, gameID: int):
        View.__init__(self, timeout=None)
        IContentItem.__init__(self, "Game calls")

        self.gameID = gameID
        self.callSelects: List[SelectCall] = []

        # Create a Select Menu for each call category
        # Note: The call string must be broken up this way because the select menu's option
        #       limit is 25, apparently
        for key, array in Binglets().getBingDict().items():
            selectMenu = SelectCall(gameID, key, array, self.refreshView)
            self.callSelects.append(selectMenu)
            self.add_item(selectMenu)

    async def refreshView(self, interaction: discord.Interaction):
        MakeCallView.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Refreshing view called...") # TODO SCH rm?
        if interaction.message:
            MakeCallView.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Refreshing the make call views message.")
            await interaction.message.edit(view=self)

