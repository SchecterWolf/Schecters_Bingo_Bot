__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import time

from .Card import Card
from typing import Any

BingIndex = int

class Player:
    def __init__(self, name: str, userID: int):
        self.card = Card(name)
        self.userID = userID
        self.ctx: Any = None
        self.valid = True
        self.rejectedRequests: int = 0
        self.rejectedTimestamp: float = 0.0

    def addRequestRejection(self):
        if not self.rejectedRequests:
            self.rejectedTimestamp = time.time()
        self.rejectedRequests += 1

    def delRequestRejection(self):
        self.rejectedRequests = 0
        self.rejectedTimestamp = 0.0

    def allowedRequest(self, limit: int, timeoutMin: int) -> bool:
        if time.time() - self.rejectedTimestamp >= timeoutMin * 60:
            self.delRequestRejection()
        return self.rejectedRequests < limit

    def __eq__(self, rhs):
        return isinstance(rhs, Player) and self.userID == rhs.userID

    def __hash__(self):
        return hash(self.userID)

