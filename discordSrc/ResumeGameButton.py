__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IGameCtrlBtn import IGameCtrlBtn

from config.ClassLogger import ClassLogger
from config.Log import LogLevel
from discord.ui import Button, View
from game.GameStore import GameStore

class ResumeGameButton(IGameCtrlBtn):
    __LOGGER = ClassLogger(__name__)
    __btn_label = "Resume Game"
    __btn_id = "resume_bingo"

    def __init__(self, gameID: int):
        super().__init__()
        self.gameID = gameID

    def addToView(self, view: View):
        button = Button(
            label=ResumeGameButton.__btn_label,
            style=discord.ButtonStyle.primary,
            custom_id=ResumeGameButton.__btn_id)
        button.callback = self.button_callback

        view.add_item(button)
        view.interaction_check = self.interaction_check
        self._interactExpired = False

    async def button_callback(self, interaction: discord.Interaction):
        ResumeGameButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord resume bingo game button pressed.")
        expired = self._interactExpired
        self._interactExpired = True
        await interaction.response.defer()

        game = GameStore().getGame(self.gameID)
        if not expired and game:
            _ = game.resume()

