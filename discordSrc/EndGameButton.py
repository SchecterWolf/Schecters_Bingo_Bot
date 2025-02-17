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

class EndGameButton(IGameCtrlBtn):
    __LOGGER = ClassLogger(__name__)
    __btn_label = "End Game"
    __btn_id ="end_bingo"

    def __init__(self):
        super().__init__()

    def addToView(self, view: View):
        button = Button(
            label=EndGameButton.__btn_label,
            style=discord.ButtonStyle.danger,
            custom_id=EndGameButton.__btn_id)
        button.callback = self.button_callback

        view.add_item(button)
        view.interaction_check = self.interaction_check
        self._interactExpired = False

    async def button_callback(self, interaction: discord.Interaction):
        EndGameButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord end bingo game button pressed.")
        if not interaction.guild_id:
            await interaction.response.send_message("Invalid interaction arg.", ephemeral=True)
            return

        expired = self._interactExpired
        self._interactExpired = True
        await interaction.response.defer()

        controller = GameStore().getController()
        if not expired and controller:
            _ = controller.stopGame(interaction.guild_id)

