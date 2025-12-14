__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .Decorators import require_gamemaster
from .IContentItem import IContentItem
from .IGateKeeper import IGateKeeper

from config.ClassLogger import ClassLogger, LogLevel
from discord.ui import Select, View

from game.ActionData import ActionData
from game.Bing import Bing
from game.Binglets import Binglets
from game.GameStore import GameStore

from typing import Awaitable, Callable, List, Optional

class SelectCall(Select):
    __LOGGER = ClassLogger(__name__)
    __SELECT_ID = "call_select"

    def __init__(self, gameID: int, key: str, bingList: List[Bing],
                 refresh: Callable[[discord.Interaction], Awaitable[None]],
                 finalization: Callable[[], None]):
        super().__init__()
        SelectCall.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Select made for call key: {key}")

        self.gameID = gameID
        self.refreshCallback = refresh
        self.placeholderVal = f"Calls for {key}"
        self.finalization = finalization

        # Select properties
        self.placeholder=self.placeholderVal
        for bing in bingList:
            self.options.append(discord.SelectOption(label=f"[{bing.bingIdx}] {bing.bingStr}", value=str(bing.bingIdx)))
        self.custom_id=f"{SelectCall.__SELECT_ID}_{key}"
        self.max_values = 1
        self.min_values = 1

    @require_gamemaster
    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            SelectCall.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Skipping call selection made with no value selected.")
            return

        SelectCall.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Call selection made: {self.values[0]}")
        callIndex = int(self.values[0])

        # Revert the select menu display
        self.values.clear()
        self.placeholder = self.placeholderVal
        await interaction.response.defer()
        await self.refreshCallback(interaction)

        game = GameStore().getGame(self.gameID)
        if game:
            _ = game.makeCall(ActionData(interaction=interaction,
                                         index=callIndex,
                                         **{ActionData.FINALIZE_FUNCT: self.finalization}))

class MakeCallView(View, IContentItem, IGateKeeper):
    __LOGGER = ClassLogger(__name__)
    # Discord views can only handle 5 rows max.
    __MAX_ROW_LEN = 5

    def __init__(self, gameID: int, gameType: str, offset: int = 0):
        View.__init__(self, timeout=None)
        IContentItem.__init__(self, "Game calls" if offset == 0 else "-")
        IGateKeeper.__init__(self)


        MakeCallView.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Generating call views with offset: {offset}")

        self.gameID = gameID
        self.callSelects: List[SelectCall] = []
        self.cascade: Optional[MakeCallView] = None

        self.interaction_check = self.interactionCheck

        # Create a Select Menu for each call category
        # Note: The call string must be broken up this way because the select menu's option
        #       limit is 25, apparently
        row = 0
        for key, array in Binglets(gameType).getBingDict().items():
            if row < offset:
                row += 1
                continue

            selectMenu = SelectCall(gameID, key, array, self.refreshView, self.resetExpired)
            self.callSelects.append(selectMenu)
            self.add_item(selectMenu)

            row += 1
            if row == MakeCallView.__MAX_ROW_LEN:
                break

        # If we have more categories, we will have to cascade into a new view
        if len(Binglets(gameType).getBingDict()) - MakeCallView.__MAX_ROW_LEN - offset > 0:
            self.cascade = MakeCallView(self.gameID, gameType, row)

    def getCascadedCallView(self) -> Optional['MakeCallView']:
        return self.cascade

    async def refreshView(self, interaction: discord.Interaction):
        if interaction.message:
            MakeCallView.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Refreshing the make call views message.")
            await interaction.message.edit(view=self)

