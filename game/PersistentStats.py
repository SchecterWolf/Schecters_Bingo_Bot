__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import datetime
import json

from .Player import Player

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from game.SavedData import SavedData
from pathlib import Path
from typing import Deque, Dict, List, Union, cast

TypeDataStat = Dict[str, int]
TypePlayerData = Dict[str, Union[str, TypeDataStat]]
TypePlayerEntry = Dict[str, TypePlayerData]

class PlayerOrdinal:
    def __init__(self, playerID: int, name: str = "", ):
        self.playerID = playerID
        self.name = name

        self.stats: dict[str, TypeDataStat] = {}
        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            self.stats[cType] = {}
            for dType in PersistentStats.LIST_DATA_ITEMS:
                self.stats[cType][dType] = 0

        self.points: dict[str, int] = {}
        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            self.points[cType] = 0

class PersistentStats():
    __LOGGER = ClassLogger(__name__)

    ITEM_NAME = "name"
    ITEM_TOTAL = "total"
    ITEM_MONTH = "month"
    ITEM_WEEK = "week"

    DATA_ITEM_BINGOS = "bingos"
    DATA_ITEM_CALLS = "calls"
    DATA_ITEM_GAMES = "games"

    LIST_DATA_ITEMS = [DATA_ITEM_BINGOS, DATA_ITEM_CALLS, DATA_ITEM_GAMES]
    LIST_CATEGORY_ITEMS = [ITEM_TOTAL, ITEM_MONTH, ITEM_WEEK]

    def __init__(self):
        cfg = Config()
        self.bonuses: dict[str, int] = {
            PersistentStats.DATA_ITEM_BINGOS: cfg.getConfig("BonusBingo", 1),
            PersistentStats.DATA_ITEM_CALLS: cfg.getConfig("BonusSlotsCalled", 1),
            PersistentStats.DATA_ITEM_GAMES: cfg.getConfig("BonusGamesPlayed", 1)
        }

        self.topPlayers: dict[str, Deque] = {
            PersistentStats.ITEM_TOTAL: Deque(),
            PersistentStats.ITEM_MONTH: Deque(),
            PersistentStats.ITEM_WEEK: Deque(),
        }
        self.filePlayerData = Path(GLOBALVARS.FILE_PLAYER_DATA)
        self.playerData: TypePlayerEntry = dict()

        self._readInPlayerData()

    def updateFromPlayers(self, players: List[Player]):
        PersistentStats.__LOGGER.log(LogLevel.LEVEL_INFO, "Updating player game data.")

        for player in players:
            if player.userID < 0:
                continue

            playerName = player.card.getCardOwner()
            playerID = player.userID
            playerStatData: TypePlayerData = self._getPlayerStats(playerID)

            for cType in PersistentStats.LIST_CATEGORY_ITEMS:
                stat = cast(TypeDataStat, playerStatData[cType])

                # Update bingos
                if player.card.hasBingo():
                    stat[PersistentStats.DATA_ITEM_BINGOS] += 1

                # Update num calls
                numCalls = player.card.getNumMarked()
                if numCalls:
                    stat[PersistentStats.DATA_ITEM_CALLS] += numCalls

                # Update games played
                stat[PersistentStats.DATA_ITEM_GAMES] += 1

            self.playerData[playerName] = playerStatData

        # Update the internal top players
        self._loadPlayerData()

        # Save player data to file
        self._save()

    def removePlayer(self, playerID: int):
        ID = str(playerID)
        if ID in self.playerData:
            PersistentStats.__LOGGER.log(LogLevel.LEVEL_INFO, f"Player ID {playerID} has been removed from saved player data.")
            self.playerData.pop(ID, None)
            self._loadPlayerData()
            self._save()

    def getBonus(self, bType: str) -> int:
        return self.bonuses.get(bType, 0)

    def getTopPlayer(self, place: int, category: str = ITEM_TOTAL) -> Union[PlayerOrdinal, None]:
        ret = None
        leaderboard = self.topPlayers.get(category)
        if leaderboard and place - 1 < len(leaderboard):
            ret = leaderboard[place -1]
        return ret

    def _readInPlayerData(self):
        PersistentStats.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Reading in saved player data...")
        if self.filePlayerData.exists():
            with self.filePlayerData.open("r") as file:
                self.playerData = json.load(file)

        self._loadPlayerData()

    def _loadPlayerData(self):
        currentWeekID = datetime.date.today().isocalendar()[1]
        currentMonthID = datetime.date.today().month
        savedWeekID = int(SavedData().getData("weekID") or 0)
        savedMonthID = int(SavedData().getData("monthID") or 0)

        # Clear out top players
        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            self.topPlayers[cType].clear()

        # Populate the top players
        for key, val in self.playerData.items():
            playerID: int = int(key)
            name: str = cast(str, val[PersistentStats.ITEM_NAME])
            for cType in PersistentStats.LIST_CATEGORY_ITEMS:
                player = PlayerOrdinal(playerID, name)

                # Null out the month/week stats if we're currently elapsed
                stats:TypeDataStat = cast(TypeDataStat, val[cType])
                if (cType == PersistentStats.ITEM_MONTH and currentMonthID > savedMonthID)\
                    or (cType == PersistentStats.ITEM_WEEK and currentWeekID > savedWeekID):
                    stats = cast(TypeDataStat, self._getPlayerStats(-1)[cType])
                self._processStats(player, cType, stats)

    def _processStats(self, player: PlayerOrdinal, cType: str, stats: TypeDataStat):
        for dType in PersistentStats.LIST_DATA_ITEMS:
            val = stats.get(dType, 0)
            player.stats[cType][dType] = val
            player.points[cType] += val * self.bonuses[dType]

        leaderboard = self.topPlayers[cType]
        if not leaderboard:
            leaderboard.appendleft(player)
            return

        idx = 0
        for index, qStat in enumerate(leaderboard):
            if player.points[cType] >= qStat.points[cType]:
                break
            idx = index + 1
        leaderboard.insert(idx, player)

        if len(self.topPlayers) > 3:
            leaderboard.pop()

    def _getPlayerStats(self, playerID: int) -> TypePlayerData:
        ret: dict = self.playerData.get(str(playerID), dict())

        if not ret:
            ret[PersistentStats.ITEM_NAME] = ""
            ret.update(PlayerOrdinal(-1).stats)

        return ret

    def _save(self):
        # Save the new updated stats
        with self.filePlayerData.open("w") as file:
            json.dump(self.playerData, file, indent=4)
            PersistentStats.__LOGGER.log(LogLevel.LEVEL_INFO, "Player data saved.")

        # Save timestamps
        SavedData().saveData("weekID", str(datetime.date.today().isocalendar()[1]))
        SavedData().saveData("monthID", str(datetime.date.today().month))

