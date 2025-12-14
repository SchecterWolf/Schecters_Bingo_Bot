__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .Decorators import require_gamemaster
from .IGameCtrlBtn import IGameCtrlBtn
from .IGateKeeper import IGateKeeper

from config.ClassLogger import ClassLogger, LogLevel
from discord.ui import Button, View
from game.ActionData import ActionData
from game.GameStore import GameStore

class PauseGameButton(IGameCtrlBtn, IGateKeeper):
    __LOGGER = ClassLogger(__name__)
    __btn_label = "Pause Game"
    __btn_id = "pause_bingo"

    def __init__(self, gameID: int):
        super().__init__()
        self.gameID = gameID

    def addToView(self, view: View):
        button = Button(
            label=PauseGameButton.__btn_label,
            style=discord.ButtonStyle.secondary,
            custom_id=PauseGameButton.__btn_id)
        button.callback = self.button_callback

        view.add_item(button)
        view.interaction_check = self.interactionCheck
        self._interactExpired = False

    @require_gamemaster
    async def button_callback(self, interaction: discord.Interaction):
        PauseGameButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord pause bingo game button pressed.")
        # Note: The button never becomes un-expired, since the button view is expected to be removed
        expired = self._interactExpired
        self.setInteractExpired()
        game = GameStore().getGame(self.gameID)

        if not expired and game:
            await interaction.response.defer(thinking=True)
            _ = game.pause(ActionData(interaction=interaction))
        else:
            await interaction.response.send_message("Failed to process command", ephemeral=True)

