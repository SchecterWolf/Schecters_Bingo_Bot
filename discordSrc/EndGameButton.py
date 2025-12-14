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
from game.GameStore import GameStore

class EndGameButton(IGameCtrlBtn, IGateKeeper):
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
        view.interaction_check = self.interactionCheck

    @require_gamemaster
    async def button_callback(self, interaction: discord.Interaction):
        EndGameButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord end bingo game button pressed.")
        if not interaction.guild_id:
            await interaction.response.send_message("Invalid interaction arg.", ephemeral=True)
            return

        controller = GameStore().getController()

        # Note: The button never becomes un-expired, since the button view is expected to be removed
        expired = self._interactExpired
        self.setInteractExpired()

        if not expired and controller:
            await interaction.response.defer(thinking=True)
            _ = controller.stopGame(interaction.guild_id)
        else:
            await interaction.response.send_message("Failed to process command", ephemeral=True)

