__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

class Bing:
    """POD for a particular bing (Bingo cell)"""
    def __init__(self, bingStr: str, bingIdx: int):
        self.bingStr = bingStr
        self.bingIdx = bingIdx
        self.marked = False
        self.x = 0
        self.y = 0

    def __eq__(self, rhs):
        return isinstance(rhs, Bing) and self.bingIdx == rhs.bingIdx

    def __hash__(self):
        return hash(self.bingIdx)

