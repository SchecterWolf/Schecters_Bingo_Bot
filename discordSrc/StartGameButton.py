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
from config.Globals import GLOBALVARS
from config.Config import Config
from discord.ui import Button, View
from game.GameStore import GameStore

class StartGameButton(IGameCtrlBtn, IGateKeeper):
    __LOGGER = ClassLogger(__name__)
    __btn_label = "Start New Game ({type})"
    __btn_label_default = "Start New Game"

    def __init__(self):
        super().__init__()

    def addToView(self, view: View):
        StartGameButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Start game buttons added to view.")

        _gameTypes = Config().getConfig("GameTypes", [])
        # Create default start game button if no type are configured
        if not _gameTypes:
            button = Button(
                label=StartGameButton.__btn_label_default,
                style=discord.ButtonStyle.primary,
                custom_id=GLOBALVARS.GAME_TYPE_DEFAULT
            )
            button.callback = self.button_callback
            view.add_item(button)
        # Add a button for each game type defined in the config
        else:
            for gameType in _gameTypes:
                fData = {"type": gameType}
                button = Button(
                    label=StartGameButton.__btn_label.format(**fData),
                    style=discord.ButtonStyle.primary,
                    custom_id=gameType
                )
                button.callback = self.button_callback
                view.add_item(button)

        view.interaction_check = self.interactionCheck

    @require_gamemaster
    async def button_callback(self, interaction: discord.Interaction):
        StartGameButton.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Discord start bingo game button pressed.")
        if not interaction.guild:
            await interaction.response.send_message("Invalid interaction arg.", ephemeral=True)
            return

        # Note: The button never becomes un-expired, since the button view is expected to be removed
        expired = self._interactExpired
        self.setInteractExpired()

        controller = GameStore().getController()
        if not expired and controller:
            await interaction.response.defer(thinking=True)
            _ = controller.startGame(interaction)
        else:
            await interaction.response.send_message("Failed to process command", ephemeral=True)

