__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import json

from .Player import Player

from config.ClassLogger import ClassLogger
from config.Config import GLOBALVARS
from config.Log import LogLevel
from pathlib import Path
from typing import Deque, Dict, List, Tuple, Union, cast

TypeStat = Tuple[str, int, int] # Player name, ID, Value
TypeDataStat = Dict[str, int]
TypePlayerData = Dict[str, Union[int, TypeDataStat]]
TypePlayerEntry = Dict[str, TypePlayerData]

class PersistentStats():
    __LOGGER = ClassLogger(__name__)

    ITEM_DATA = "stats"
    ITEM_ID = "id"

    DATA_ITEM_BINGOS = "bingos"
    DATA_ITEM_CALLS = "calls"
    DATA_ITEM_GAMES = "games"

    def __init__(self):
        self.topBingos: Deque[TypeStat] = Deque()
        self.topCalls: Deque[TypeStat] = Deque()
        self.topGames: Deque[TypeStat] = Deque()

        self.filePlayerData = Path(GLOBALVARS.FILE_PLAYER_DATA)
        self.playerData: TypePlayerEntry = dict()

        self._readInPlayerData()

    def updateFromPlayers(self, players: List[Player]):
        PersistentStats.__LOGGER.log(LogLevel.LEVEL_INFO, "Updating player game data.")
        for player in players:
            playerName = player.card.getCardOwner()
            playerStatData = self._getPlayerStats(playerName)

            # Update bingos
            if player.card.hasBingo():
                playerStats[PersistentStats.DATA_ITEM_BINGOS] += 1
                self._processStat(self.topBingos, playerName, playerStats[PersistentStats.DATA_ITEM_BINGOS])

            # Update num calls
            numCalls = player.card.getNumMarked()
            if numCalls:
                playerStats[PersistentStats.DATA_ITEM_CALLS] += numCalls
                self._processStat(self.topBingos, playerName, playerStats[PersistentStats.DATA_ITEM_CALLS])

            # Update games played
            playerStats[PersistentStats.DATA_ITEM_GAMES] += 1
            self._processStat(self.topBingos, playerName, playerStats[PersistentStats.DATA_ITEM_GAMES])

            # Update the internal stats member
            self.playerData[playerName] = playerStatData

        # Save the new updated stats
        with self.filePlayerData.open("w") as file:
            json.dump(self.playerData, file, indent=4)
            PersistentStats.__LOGGER.log(LogLevel.LEVEL_INFO, "Player data saved.")

    def _readInPlayerData(self):
        PersistentStats.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Reading in saved player data...")
        if self.filePlayerData.exists():
            with self.filePlayerData.open("r") as file:
                self.playerData = json.load(file)

        for key, val in self.playerData.items():
            playerID: int = cast(int, val[PersistentStats.ITEM_ID])
            playerData: TypeDataStat = cast(TypeDataStat, val[PersistentStats.ITEM_DATA])
            self._processStat(self.topBingos, key, playerID, playerData[PersistentStats.DATA_ITEM_BINGOS])
            self._processStat(self.topCalls, key, playerID, playerData[PersistentStats.DATA_ITEM_CALLS])
            self._processStat(self.topGames, key, playerID, playerData[PersistentStats.DATA_ITEM_GAMES])

    def _processStat(self, queue: Deque[TypeStat], player: str, playerID: int, num: int):
        stat: TypeStat = (player, playerID, num)
        if not queue and num:
            queue.appendleft(stat)
            return

        idx = 0
        for index, qStat in enumerate(queue):
            if num >= qStat[1]:
                break
            idx = index + 1
        queue.insert(idx, stat)

        if len(queue) > 3:
            queue.pop()

    def _getPlayerStats(self, player: str) -> TypePlayerData:
        ret: dict = self.playerData.get(player, dict())

        if not ret:
            ret[PersistentStats.ITEM_ID] = -1
            ret[PersistentStats.ITEM_DATA][PersistentStats.DATA_ITEM_BINGOS] = 0
            ret[PersistentStats.ITEM_DATA][PersistentStats.DATA_ITEM_CALLS] = 0
            ret[PersistentStats.ITEM_DATA][PersistentStats.DATA_ITEM_GAMES] = 0

        return ret

