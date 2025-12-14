__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import sqlite3
import time

from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS
from typing import List, Optional

class BannedPlayer():
    def __init__(self):
        self.dbID: Optional[int] = None
        self.userID = 0
        self.name = ""
        self.timestamp = time.time()

class BannedData:
    __instance = None
    __LOGGER = ClassLogger(__name__)

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        # Init guard
        if hasattr(self, "initialized"):
            return

        self.data: List[BannedPlayer] = []

        self._loadData()
        self.initialized = True

    def isBanned(self, playerID: int) -> bool:
        return any(p.userID == playerID for p in self.data )

    def addBanned(self, playerID: int, playerName: str):
        # Check if player is already banned
        if self.isBanned(playerID):
            BannedData.__LOGGER.log(LogLevel.LEVEL_INFO, f"Player ID {playerID} has been banned, skipping.")
            return

        bp = BannedPlayer()
        bp.userID = playerID
        bp.name = playerName
        bp.timestamp = time.time()

        self.data.append(bp)
        self._addToDB(bp)
        BannedData.__LOGGER.log(LogLevel.LEVEL_INFO, f"Player ID {playerID} has been added to the banned list.")

    def removeBanned(self, playerID: int):
        for bp in self.data:
            if bp.userID == playerID:
                BannedData.__LOGGER.log(LogLevel.LEVEL_INFO, f"Player ID {playerID} has been removed from the banned list.")
                self._rmFromDB(bp)
                self.data.remove(bp)
                break

    def getAllBanned(self) -> List[int]:
        return [int(bp.userID) for bp in self.data]

    def _addToDB(self, bp: BannedPlayer):
        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        cur = conn.cursor()

        cur.execute("INSERT INTO BANNED (userid, name, timestamp)"
                    + " VALUES (?,?,?)",
                    [
                        bp.userID,
                        bp.name,
                        bp.timestamp
                    ])
        bp.dbID = cur.lastrowid

        conn.commit()
        conn.close()

    def _rmFromDB(self, bp: BannedPlayer):
        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM BANNED WHERE id = ?", (bp.dbID,))
        conn.commit()
        conn.close()

    def _loadData(self):
        BannedData.__LOGGER.log(LogLevel.LEVEL_INFO, "Reading in banned player data.")
        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        cur = conn.cursor()

        cur.execute("SELECT id, userid, name, timestamp"
                    + f" FROM BANNED")
        rows = cur.fetchall()

        for row in rows:
            bp = BannedPlayer()
            bp.dbID = row[0]
            bp.userID = row[1]
            bp.name = row[2]
            bp.timestamp = row[3]
            self.data.append(bp)

        conn.close()

