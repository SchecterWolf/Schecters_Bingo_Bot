__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from abc import ABC

class IGateKeeper(ABC):
    def __init__(self):
        super().__init__()
        self._interactExpired = False

    def setInteractExpired(self):
        self._interactExpired = True

    def resetExpired(self):
        self._interactExpired = False

    async def interactionCheck(self, interaction: discord.Interaction):
        if self._interactExpired:
            await interaction.response.send_message("Action is already being processed, please wait", ephemeral=True)
        return not self._interactExpired

