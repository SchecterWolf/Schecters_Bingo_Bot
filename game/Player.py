__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .Card import Card
from typing import Any

class Player:
    def __init__(self, name: str, userID: int):
        self.card = Card(name)
        self.userID = userID
        self.ctx: Any = None
        self.valid = True

    def __eq__(self, rhs):
        return isinstance(rhs, Player) and self.userID == self.userID

    def __hash__(self):
        return hash(self.userID)

