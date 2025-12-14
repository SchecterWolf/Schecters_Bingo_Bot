__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import hashlib
import math
import random
import time

from .Bing import Bing
from .Binglets import Binglets
from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from typing import Dict, List, Optional

class Card:
    ROW = 'row'
    COL = 'col'
    DIAG = 'diag'

    _LOGGER = ClassLogger(__name__)
    _cardSize = 0

    def __init__(self, playername: str):
        self.playername = playername
        self._initBoard()

    def generateNewCard(self, gameType: str) -> str:
        """
        Creates a new randomized bingo card for a player and returns
        a unique hash ID for the particular card arrangement.
        """
        Card._LOGGER.log(LogLevel.LEVEL_DEBUG, f"Generating card for player {self.playername}...")
        # Get the configured card size if we haven't already
        if Card._cardSize == 0:
            Card._LOGGER.log(LogLevel.LEVEL_DEBUG, "Reading in card size config.")
            Card._cardSize = int(Config().getConfig('CardSize', "0"))
        if not Card._cardSize > 0:
            Card._LOGGER.log(LogLevel.LEVEL_CRIT, "Cannot have a 'CardSize' of 0. Aborting game.")
            raise ValueError("Invalid CardSize configuration")

        self._initBoard()
        idString = ""
        bings = Binglets(gameType).getBingletsCopy()
        limits = Binglets(gameType).getLimits()

        for i in range(Card._cardSize):
            row = []
            for j in range(Card._cardSize):
                bing = self._extractRandomBinglet(limits, bings)
                bing.x = i
                bing.y = j
                idString += bing.bingStr
                row.append(bing)

            self.cells.append(row)

        # Place the free space, if we're using it
        if Config().getConfig("UseFreeSpace"):
            i = math.floor(Card._cardSize / 2)
            freeBing = Bing("FREE SPACE", 0)
            freeBing.x = i
            freeBing.y = i
            self.cells[i][i] = freeBing
            self.markCell(freeBing)

        md5 = hashlib.md5()
        md5.update(idString.encode('utf-8'))
        self.cardID = md5.hexdigest()

        Card._LOGGER.log(LogLevel.LEVEL_INFO, f"New card generated for player \"{self.playername}\" with ID: {self.cardID}")
        return self.cardID

    def markCell(self, calledBing: Bing) -> bool:
        """
        Attempts to mark a cell with a given bing string,
        if the card contains the bing string.
        Returns True if the card was able to mark a bing
        """
        bing = self._getBingCell(calledBing.bingIdx)
        prevBingo = self.hasBingo()

        if bing.bingStr and not bing.marked:
            Card._LOGGER.log(LogLevel.LEVEL_INFO, f"Player \"{self.playername}\" marked the square ({bing.bingStr})!")

            rowCount = self.markedCells[Card.ROW].get(bing.x, 0) + 1
            colCount = self.markedCells[Card.COL].get(bing.y, 0) + 1
            diagA = self.markedCells[Card.DIAG].get('A', 0) + (1 if bing.x == bing.y else 0)
            diagB = self.markedCells[Card.DIAG].get('B', 0) + (1 if bing.x + bing.y == Card._cardSize - 1 else 0)

            bing.marked = True
            self._adjustCondition(bing, rowCount, colCount, diagA, diagB)

        if self.hasBingo() and not prevBingo:
            Card._LOGGER.log(LogLevel.LEVEL_INFO, f"Player \"{self.playername}\" has a BINGO!")

        return bing.marked

    def unmarkCell(self, calledBing: Bing) -> bool:
        """
        Attempts to unmark a cell with a given bing string,
        if the card contains the bing string.
        Returns True if the card was able to unmark a bing
        """
        bing = self._getBingCell(calledBing.bingIdx)
        prevBingo = self.hasBingo()

        if bing.bingStr and bing.marked:
            Card._LOGGER.log(LogLevel.LEVEL_INFO, f"Player \"{self.playername}\" unmarked the square ({bing.bingStr}).")

            rowCount = self.markedCells[Card.ROW].get(bing.x, 1) - 1
            colCount = self.markedCells[Card.COL].get(bing.y, 1) - 1
            diagA = (self.markedCells[Card.DIAG].get('A', 1) - 1) if bing.x == bing.y else self.markedCells[Card.DIAG].get('A', 0)
            diagB = (self.markedCells[Card.DIAG].get('B', 1) - 1) if bing.x + bing.y else self.markedCells[Card.DIAG].get('B', 0)

            bing.marked = False
            self._adjustCondition(bing, rowCount, colCount, diagA, diagB)

        if prevBingo and not self.hasBingo():
            Card._LOGGER.log(LogLevel.LEVEL_INFO, f"Player \"{self.playername}\" lost their BINGO.")

        return not bing.marked

    def hasBingo(self) -> bool:
        return self.bingo

    def getCardOwner(self) -> str:
        return self.playername

    def getCardID(self) -> str:
        return self.cardID

    def getNumMarked(self) -> int:
        return sum(bing.marked for row in self.cells for bing in row)

    def getCellsStr(self) -> List[List[str]]:
        cellsStr: List[List[str]] = []
        for row in self.cells:
            rowStr: List[str] = []
            for cell in row:
                itemStr: str = f"{cell.bingStr} ({cell.bingIdx})"
                rowStr.append(itemStr)
            cellsStr.append(rowStr)
        return cellsStr

    def getCardBings(self) -> List[List[Bing]]:
        return self.cells

    def getBingFromID(self, bingID: int) -> Optional[Bing]:
        return next((bing for row in self.cells for bing in row if bing.bingIdx == bingID), None)

    def isCellMarked(self, i, j) -> bool:
        ret = False
        if i < len(self.cells) and j < len(self.cells[0]):
            ret = self.cells[i][j].marked
        return ret

    def _adjustCondition(self, bing, rowCount, colCount, diagA, diagB):
            self.markedCells[Card.ROW][bing.x] = rowCount
            self.markedCells[Card.COL][bing.y] = colCount
            self.markedCells[Card.DIAG]['A'] = diagA
            self.markedCells[Card.DIAG]['B'] = diagB

            self.bingo = (rowCount == Card._cardSize or
                          colCount == Card._cardSize or
                          diagA == Card._cardSize or
                          diagB == Card._cardSize)

    def _getBingCell(self, index) -> Bing:
        found = Bing("", 0)
        for row in self.cells:
            for cell in row:
                if index == cell.bingIdx:
                    found = cell
                    break
            if found.bingStr:
                break

        return found

    def _initBoard(self):
        self.bingo = False
        self.cardID = ""
        self.cells: List[List[Bing]] = []
        self.markedCells = {
            Card.ROW: {},
            Card.COL: {},
            Card.DIAG: {},
        }

    def _extractRandomBinglet(self, limits: Dict[str, int], bings) -> Bing:
        if not bings:
            return Bing("invalid", -1)

        if not hasattr(random, "_initSeed"):
            random.seed(time.time())
            setattr(random, "_initSeed", True)
        randomIdx = random.randrange(0, len(bings))
        ret: Bing = bings.pop(randomIdx)

        # Check if we have a category limit, retry (recursive) if the limit is reached,
        # else decrement the limit and proceed
        catLimit = limits.get(ret.category, None)
        if catLimit != None:
            if catLimit == 0:
                ret = self._extractRandomBinglet(limits, bings)
            else:
                limits[ret.category] = catLimit - 1

        return ret

