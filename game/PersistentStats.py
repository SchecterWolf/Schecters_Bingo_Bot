__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import datetime
import sqlite3

from .Player import Player

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from typing import Dict, List, Optional, cast

DType = str
CType = str
TypeDataStat = Dict[DType, int]
TypePlayerData = Dict[CType, TypeDataStat]

# TODO This isn't a good practice to define the keys like this, since it diverges from the
#       "single source-of-truth" in the PersistentStats... But I cant forward declare in
#       python, so I'm just redefining the keys
BONUSES: Dict[str, int] = {
    "bingos": Config().getConfig("BonusBingo", 1),
    "calls": Config().getConfig("BonusSlotsCalled", 1),
    "games": Config().getConfig("BonusGamesPlayed", 1)
}

def GetBonus(dType: str) -> int:
    return BONUSES.get(dType, 0)

def CanonicalCType(cType: str) -> str:
    typeCanon = {
        PersistentStats.ITEM_TOTAL: "All-time",
        PersistentStats.ITEM_MONTH: "Monthly",
        PersistentStats.ITEM_WEEK: "Weekly"
    }
    return typeCanon.get(cType, "")

class PlayerOrdinal:
    def __init__(self, playerID: int, name: str = "", ):
        self.dbID: Optional[int] = None
        self.playerID: int = playerID
        self.guildid = 0
        self.name: str = name
        self.timestampMonth = 0
        self.timestampWeek = 0

        self.stats: TypePlayerData = {}
        self.points: dict[CType, int] = {}
        self.ranks: dict[CType, int] = {}

        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            self.stats[cType] = {}
            self.points[cType] = 0
            self.ranks[cType] = 0
            for dType in PersistentStats.LIST_DATA_ITEMS:
                self.stats[cType][dType] = 0

class PersistentStats():
    __LOGGER = ClassLogger(__name__)

    ITEM_TOTAL = "total"
    ITEM_MONTH = "month"
    ITEM_WEEK = "week"

    DATA_ITEM_BINGOS = "bingos"
    DATA_ITEM_CALLS = "calls"
    DATA_ITEM_GAMES = "games"

    LIST_DATA_ITEMS = [DATA_ITEM_BINGOS, DATA_ITEM_CALLS, DATA_ITEM_GAMES]
    LIST_CATEGORY_ITEMS = [ITEM_TOTAL, ITEM_MONTH, ITEM_WEEK]

    def __init__(self, guildID: int):
        self.guildID = guildID
        self.allPlayers: List[PlayerOrdinal] = []
        self.cachedLeaders: Dict[CType, List[PlayerOrdinal]] = {}

        self.refresh()

    def updateFromPlayers(self, players: List[Player]):
        PersistentStats.__LOGGER.log(LogLevel.LEVEL_INFO, "Updating player game data.")

        currentWeekID = datetime.date.today().isocalendar()[1]
        currentMonthID = datetime.date.today().month

        for player in players:
            if player.userID < 0 and not Config().getConfig("Debug", False):
                continue

            playerName = player.card.getCardOwner()
            playerID = player.userID
            playerOrd: Optional[PlayerOrdinal] = self.getPlayer(playerID)

            # Add to player list if they are a new player
            if not playerOrd:
                playerOrd = PlayerOrdinal(playerID, playerName)
                playerOrd.guildid = self.guildID
                playerOrd.timestampMonth = currentMonthID
                playerOrd.timestampWeek = currentWeekID
                self.allPlayers.append(playerOrd)

            # Update the player stats
            playerStatData: TypePlayerData = playerOrd.stats
            for cType in PersistentStats.LIST_CATEGORY_ITEMS:
                stat = cast(TypeDataStat, playerStatData.setdefault(cType, dict()))

                # Update bingos
                if player.card.hasBingo():
                    stat[PersistentStats.DATA_ITEM_BINGOS] = 1 + stat.get(PersistentStats.DATA_ITEM_BINGOS, 0)

                # Update num calls
                numCalls = player.card.getNumMarked()
                if numCalls:
                    stat[PersistentStats.DATA_ITEM_CALLS] = numCalls + stat.get(PersistentStats.DATA_ITEM_CALLS, 0)

                # Update games played
                stat[PersistentStats.DATA_ITEM_GAMES] = 1 + stat.get(PersistentStats.DATA_ITEM_GAMES, 0)

            self._calculateBonus(playerOrd)

        # Update the internal top players
        self._loadPlayerRanks()

        # Save player data to file
        self._save()

    def removePlayer(self, playerID: int):
        player = self.getPlayer(playerID)
        if player:
            PersistentStats.__LOGGER.log(LogLevel.LEVEL_INFO, f"Player ID {playerID} has been removed from saved player data.")

            self.allPlayers.remove(player)
            self._loadPlayerRanks()

            # Remove player from DB
            conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
            cur = conn.cursor()
            cur.execute("DELETE FROM PLAYERS WHERE userid = ? AND guildid = ?", (playerID, self.guildID))
            conn.commit()
            conn.close()

    def getTopPlayer(self, place: int, category: str = ITEM_TOTAL) -> Optional[PlayerOrdinal]:
        leaderboard = self.getAllPlayers(category)
        return leaderboard[place -1] if (place - 1) < len(leaderboard) else None

    def getPlayer(self, playerID: int) -> Optional[PlayerOrdinal]:
        return next((player for player in self.allPlayers if player.playerID == playerID), None)

    def getAllPlayers(self, cType: str) -> List[PlayerOrdinal]:
        # Populate the leaders if there is no cache for the CType
        leaderboard: List[PlayerOrdinal] = self.cachedLeaders.setdefault(cType, [])
        if not leaderboard:
            leaderboard = sorted(self.allPlayers, key=lambda p: p.points[cType], reverse=True)
        return leaderboard

    def refresh(self):
        self.allPlayers: List[PlayerOrdinal] = []
        self._readInPlayerData()

    def _readInPlayerData(self):
        """
        Reads in the player data from the database
        """
        PersistentStats.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Reading in saved player data from the DB...")

        currentWeekID = datetime.date.today().isocalendar()[1]
        currentMonthID = datetime.date.today().month

        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        cur = conn.cursor()

        cur.execute("SELECT id, userid, name, guildid, timestampmonth, timestampweek, bingos, calls, games"
                    + ", bingosmonth, callsmonth, gamesmonth"
                    + ", bingosweek, callsweek, gamesweek"
                    + f"  FROM PLAYERS WHERE guildid = {self.guildID}")
        rows = cur.fetchall()

        for row in rows:
            pd = PlayerOrdinal(row[1], row[2])
            pd.dbID = row[0]
            pd.guildid = row[3]
            pd.timestampMonth = row[4]
            pd.timestampWeek = row[5]
            pd.stats[PersistentStats.ITEM_TOTAL][PersistentStats.DATA_ITEM_BINGOS] = row[6]
            pd.stats[PersistentStats.ITEM_TOTAL][PersistentStats.DATA_ITEM_CALLS] = row[7]
            pd.stats[PersistentStats.ITEM_TOTAL][PersistentStats.DATA_ITEM_GAMES] = row[8]
            if currentMonthID != pd.timestampMonth:
                pd.timestampMonth = currentMonthID
            else:
                pd.stats[PersistentStats.ITEM_MONTH][PersistentStats.DATA_ITEM_BINGOS] = row[9]
                pd.stats[PersistentStats.ITEM_MONTH][PersistentStats.DATA_ITEM_CALLS] = row[10]
                pd.stats[PersistentStats.ITEM_MONTH][PersistentStats.DATA_ITEM_GAMES] = row[11]
            if currentWeekID != pd.timestampWeek:
                pd.timestampWeek = currentWeekID
            else:
                pd.stats[PersistentStats.ITEM_WEEK][PersistentStats.DATA_ITEM_BINGOS] = row[12]
                pd.stats[PersistentStats.ITEM_WEEK][PersistentStats.DATA_ITEM_CALLS] = row[13]
                pd.stats[PersistentStats.ITEM_WEEK][PersistentStats.DATA_ITEM_GAMES] = row[14]

            self._calculateBonus(pd)
            self.allPlayers.append(pd)

        self._loadPlayerRanks()
        conn.close()

    def _loadPlayerRanks(self):
        self.cachedLeaders = {}

        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            for idx, player in enumerate(self.getAllPlayers(cType)):
                if player.points[cType] > 0:
                    player.ranks[cType] = idx + 1
                else:
                    player.ranks[cType] = 0

    def _calculateBonus(self, player: PlayerOrdinal):
        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            player.points[cType] = 0
            for dType in PersistentStats.LIST_DATA_ITEMS:
                val = player.stats[cType].get(dType, 0)
                player.points[cType] += val * GetBonus(dType)

    def _save(self):
        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        cur = conn.cursor()

        for pd in self.allPlayers:
            data = {
                "userid": pd.playerID,
                "guildid": pd.guildid,
                "name": pd.name,
                "timestampmonth": pd.timestampMonth,
                "timestampweek": pd.timestampWeek,
            }

            # Add in the player stats to the data container
            for cType in PersistentStats.LIST_CATEGORY_ITEMS:
                for dType in PersistentStats.LIST_DATA_ITEMS:
                    suffix = "" if cType == PersistentStats.ITEM_TOTAL else cType
                    data[f"{dType}{suffix}"] = pd.stats[cType][dType]

            sql = ""
            values = list(data.values())
            if not pd.dbID:
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                sql = f"""
                INSERT INTO PLAYERS ({columns})
                VALUES ({placeholders})
                """
            else:
                updateColumns = ", ".join(f"{k}=?" for k in data.keys())
                values.append(pd.dbID)
                sql = f"""
                UPDATE PLAYERS
                SET {updateColumns}
                WHERE id=?
                """

            cur.execute(sql, values)
            if not pd.dbID:
                pd.dbID = cur.lastrowid

        conn.commit()
        conn.close()

        PersistentStats.__LOGGER.log(LogLevel.LEVEL_INFO, "Player data saved.")

