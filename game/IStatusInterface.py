__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from abc import ABC, abstractmethod
from discord import Embed

class IStatusInterface(ABC):
    ORDINALS = ["3rd", "2nd", "1st"]

    def __init__(self):
        super().__init__()

    def _addFieldSeparator(self, embed: Embed):
        embed.add_field(name="\u200b", value="\u200b", inline=False)

    @abstractmethod
    def refreshStats(self):
        pass
