__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from abc import ABC, abstractmethod

class IGameCtrlBtn(ABC):
    def __init__(self):
        super().__init__()
        self._interactExpired = False

    async def interaction_check(self, interaction: discord.Interaction):
        return not self._interactExpired

    @abstractmethod
    def addToView(self, view: discord.ui.View):
        pass

