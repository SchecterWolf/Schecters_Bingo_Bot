__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import json
import sqlite3
import time
from dataclasses import dataclass, asdict
from collections import defaultdict

from .CallRequest import CallRequest
from .Game import Game, GameState
from .Bing import Bing
from .Binglets import Binglets
from .IRecoveryInterface import IRecoveryInterface
from .PersistentStats import PersistentStats
from .Player import Player
from .Result import Result

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS

from typing import Any, Dict, List, Optional, Set

@dataclass
class RecoveryData:
    guildid: int
    gamestate: GameState
    gametype: str
    timestarted: float
    calledbings: Set[Bing]
    kickedplayers: Set[int]
    playerbingos: Set[str]

class Recovery(IRecoveryInterface):
    __TABLE = "RECOVER"
    __PLAYERS = "RECPLAYERS"
    __PLAYER_CARD = "RECPLAYERCELLS"
    __REQUESTS = "RECREQUESTS"

    __BING_ID_BUFFER = 1000

    __LOGGER = ClassLogger(__name__)

    def __init__(self, gameID: int):
        self.gameID = gameID
        self.cachedRecovGame: Optional[RecoveryData] = None
        self.cachedPlayers: Set[Player] = set()
        self.cachedRequests: Dict[int, CallRequest] = {}

        self.gameType = GLOBALVARS.GAME_TYPE_DEFAULT

    def getGameID(self) -> int:
        return self.gameID

    def hasRecovery(self) -> bool:
        if not Config().getConfig('UseRecovery', False):
            return False

        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        cur = conn.cursor()

        cur.execute(f"SELECT guildid FROM {Recovery.__TABLE} WHERE guildid = ?", (self.gameID,))
        ret = True if cur.fetchone() else False

        Recovery.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Checking if recovery exists for guild {self.gameID}: {ret}")

        self.__closeDB(conn)
        return ret

    def removeRecovery(self):
        if not Config().getConfig('UseRecovery', False):
            return

        Recovery.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Removing recover for guild {self.gameID}")

        # Construct the db tools, enabling foreign keys
        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        self.__removeData(cur, "guildid", self.gameID, Recovery.__TABLE)

        conn.commit()
        self.__closeDB(conn)

    def updateRecovery(self, game: Game):
        if not Config().getConfig('UseRecovery', False):
            return

        # Construct the db tools, enabling foreign keys
        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        # Make sure the game type is syncronized
        self.gameType = game.gameType

        currentGame = RecoveryData(
            guildid= self.gameID,
            gamestate = game.state,
            gametype = game.gameType,
            timestarted = game.timeStarted,
            calledbings = game.calledBings,
            kickedplayers = game.kickedPlayers,
            playerbingos = game.playerBingos,
        )

        self.__updateGameState(cur, currentGame)
        self.__updateGamePlayers(cur, game, self.gameID)
        self.__updateGameCallRequests(cur, game, self.gameID)

        conn.commit()
        self.__closeDB(conn)

    def recoverGame(self, stats: PersistentStats) -> Optional[Game]:
        if not Config().getConfig('UseRecovery', False):
            return None

        Recovery.__LOGGER.log(LogLevel.LEVEL_INFO, f"Attempting to recover game from the recovery database....")
        bCont = True
        game = Game()

        # Construct the db tools, enabling foreign keys
        conn = sqlite3.connect(GLOBALVARS.FILE_GAME_DB)
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        recoveredGameData = self.__recoverGameState(cur, self.gameID)
        if not recoveredGameData:
            Recovery.__LOGGER.log(LogLevel.LEVEL_WARN, f"There was no game to recover.")
            bCont = False

        # Set the game state
        while bCont and recoveredGameData and game.state != recoveredGameData.gamestate:
            result = Result(False)

            if game.state == GameState.NEW:
                result = Result(game.initGame(stats))
            elif game.state == GameState.IDLE:
                result = game.startGame()
            elif game.state == GameState.STARTED and recoveredGameData.gamestate == GameState.PAUSED:
                result = game.pauseGame()
            elif game.state == GameState.STARTED and recoveredGameData.gamestate == GameState.STOPPED:
                result = game.stopGame()
            elif game.state == GameState.STOPPED:
                game.destroyGame()
                result.result = True

            if not result.result:
                Recovery.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Encountered an error when setting the game state during the recovery.")
                bCont = False

        # Set the rest of the game data
        if bCont and recoveredGameData:
            game.gameType = recoveredGameData.gametype
            game.timeStarted = recoveredGameData.timestarted
            game.calledBings = recoveredGameData.calledbings
            game.kickedPlayers = recoveredGameData.kickedplayers
            game.playerBingos = recoveredGameData.playerbingos

        # Add the recovered players to the game
        if bCont:
            self.__recoverGamePlayers(cur, self.gameID, game)

        # Recover the call requests
        if bCont:
            self.__recoverGameCallRequests(cur, self.gameID, game)

        # Return null if recovery was unsuccessful
        if not bCont:
            game = None

        return game

    def __recoverGamePlayers(self, cur: sqlite3.Cursor, gameID: int, game: Game):
        templ = self.__createPlayerData(0, 0, "", 0, 0, 0.0, 0)
        listRecoveredPlayerData: List[Dict[str, Any]] = self.__recoverData(cur, templ, "id", gameID, Recovery.__PLAYERS)

        for playerData in listRecoveredPlayerData:
            player = Player(playerData['name'], playerData['playerid'])
            if not game.checkEligible(player):
                Recovery.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Received a malformed player recovery data, player not eligible, skipping...")
                continue

            player.valid = bool(playerData['valid'])
            player.rejectedRequests = playerData['rejectedreqs']
            player.rejectedTimestamp = playerData['rejectedtime']

            if self.__recoverPlayerCard(cur, player, game.gameType):
                player.setClean()
                game.players.add(player)

    def __recoverPlayerCard(self, cur: sqlite3.Cursor, player: Player, gameType: str) -> bool:
        bRet = True
        binglets = Binglets(gameType)
        templ = self.__createPlayerCardData(0, "0", 0, 0, 0)
        listRecoveredCardData: List[Dict[str, Any]] = self.__recoverData(cur, templ, "id", player.userID, Recovery.__PLAYER_CARD)

        # The database isn't guaranteed to return the bing cells in "order". Therefore we're using dictionaries
        # to sort the bing cells as they are processed from the recovery data
        temporaryCellStructure: Dict[int, Dict[int, Bing]] = defaultdict(dict)

        for cardData in listRecoveredCardData:
            bingID = abs(int(cardData['bingid'])) % Recovery.__BING_ID_BUFFER
            bing = binglets.getBingFromIndex(bingID)
            if bing.bingIdx < 0:
                break

            bing.marked = bool(cardData['marked'])
            bing.x = int(cardData['x'])
            bing.y = int(cardData['y'])

            temporaryCellStructure[bing.x][bing.y] = bing

        # Sort the cells
        temporaryCellStructure = {
            outer: dict(sorted(inner.items()))
            for outer, inner in sorted(temporaryCellStructure.items())
        }

        # Sanity check
        cardSize = int(Config().getConfig('CardSize', "0"))
        cells: List[List[Bing]] = [list(inner.values()) for inner in temporaryCellStructure.values()]
        invalidCard = len(cells) != cardSize and all(len(row) == cardSize for row in cells)

        if invalidCard:
            Recovery.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Received malform card recovery data for player {player.card.getCardOwner()}, skipping player...")
            bRet = False
        else:
            player.card.cells = cells
            player.card._cardSize = cardSize

            # Even though the bing object is set as marked internally, I still need to mark the bing at the card
            # level because there is some extra tracking structs that are updated as a result
            for row in player.card.cells:
                for bing in row:
                    if bing.marked:
                        player.card.markCell(bing, True)
                    bing.setClean()

        return bRet

    def __recoverGameCallRequests(self, cur: sqlite3.Cursor, gameID: int, game: Game):
        binglets = Binglets(game.gameType)

        templ = self.__createCallRequestData(0, 0, "")
        listCallRequestData: List[Dict[str, Any]] = self.__recoverData(cur, templ, "id", gameID, Recovery.__REQUESTS)

        # Add all the recovered called requests retrieved from the recovery table
        for reqData in listCallRequestData:
            playerIDs = reqData['playerids']
            if not playerIDs:
                Recovery.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Received a malformed call request recovery data, skipping...")
                continue
            playerIDs = json.loads(playerIDs)

            # Fetch the requester player and requests bing objects
            result = game.getPlayer(playerIDs[0])
            player = result.additional
            bing = binglets.getBingFromIndex(int(reqData['bingid']))
            if not result.result or bing.bingIdx < 0:
                Recovery.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Received a malformed call request recovery data, skipping...")
                continue

            # Create the recovered call request
            callReq = CallRequest(player, bing)

            # Add any additional players to the request, if any
            for pid in playerIDs[1:]:
                result = game.getPlayer(pid)
                player = result.additional
                if result.result:
                    callReq.addPlayer(player)

            # Add the recovered call request to the game
            game.requestedCalls.append(callReq)

        return False

    def __recoverGameState(self, cur: sqlite3.Cursor, gameID: int) -> Optional[RecoveryData]:
        cur.execute("SELECT guildid, gamestate, gametype, timestarted, calledbings, kickedplayers, playerbingos, timesaved"
                    + f" FROM {Recovery.__TABLE} WHERE guildid = {gameID}")
        row = cur.fetchone()

        ret = None
        if row:
            ret = RecoveryData(
                guildid = row[0],
                gamestate = GameState(int(row[1])),
                gametype = row[2],
                timestarted = row[3],
                calledbings = self.__parseBings(row[2], set(json.loads(row[4]))),
                kickedplayers = set(json.loads(row[5])),
                playerbingos = set(json.loads(row[6]))
            )

        return ret

    def __updateGameState(self, cur: sqlite3.Cursor, gameData: RecoveryData):
        self.cachedRecovGame = self.__recoverGameState(cur, gameData.guildid)

        # Update the recovery DB if the recovery data is stale
        if gameData != self.cachedRecovGame:
            Recovery.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Updating game recovery data for guild {self.gameID}")

            # Convert the recovery data into a dictionary
            data = asdict(gameData)

            # Convert the game type to an int
            data['gamestate'] = data['gamestate'].value

            # Convert the sets to json structs
            data['kickedplayers'] = json.dumps(list(gameData.kickedplayers))
            data['playerbingos'] = json.dumps(list(gameData.playerbingos))

            # Convert the Bings to IDs
            data['calledbings'] = json.dumps([b.bingIdx for b in gameData.calledbings])

            # Add save time
            data['timesaved'] = time.time()

            self.__commitData(cur, data, "guildid", Recovery.__TABLE)
            self.cachedRecovGame = gameData

    def __updateGamePlayers(self, cur: sqlite3.Cursor, game: Game, gameID: int):
        # Update players into the DB
        for player in game.players:
            # Update player data
            if player.getIsDirty() or player.card.getIsDirty():
                Recovery.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Updating player recovery data for player \"{player.card.getCardOwner()}\"({player.userID})")
                dataPlayer = self.__createPlayerData(gameID,
                                                     player.userID,
                                                     player.card.getCardOwner(),
                                                     int(player.valid),
                                                     player.rejectedRequests,
                                                     player.rejectedTimestamp,
                                                     int(player.card.hasBingo()))
                self.__commitData(cur, dataPlayer, "playerid", Recovery.__PLAYERS)

            # Shift (multiply) 1000 to the player ID as a "buffer" for the bing ID placement,
            # since im pretty sure we will never have more than 1000 slots configured....
            # Im doing this to get a deterministic DB id for each players card cells,
            # since its easier to do it this way with the way the code is written for
            # persisting data to the DB
            playerID = abs(player.userID) * Recovery.__BING_ID_BUFFER

            # Update player card data
            for cellsX in player.card.cells:
                for cell in cellsX:
                    if cell.getIsDirty():
                        Recovery.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Updating player card recovery data for player \"({player.userID})\" Bing({cell.bingIdx}) [{cell.x}][{cell.y}] => {cell.marked}")
                        dataCard = self.__createPlayerCardData(player.userID,
                                                               str(playerID + cell.bingIdx),
                                                               cell.x,
                                                               cell.y,
                                                               cell.marked)
                        self.__commitData(cur, dataCard, "bingid", Recovery.__PLAYER_CARD)
                    cell.setClean()

            # Clean the cache dirty bit
            player.setClean()
            player.card.setClean()

        # Delete any players that got removed from the game since last time
        for player in self.cachedPlayers - game.players:
            self.__removeData(cur, "playerid", player.userID, Recovery.__PLAYERS)

        self.cachedPlayers = game.players.copy()

    def __updateGameCallRequests(self, cur: sqlite3.Cursor, game: Game, gameID: int):
        tmpNewReq: Dict[int, CallRequest] = {}

        # Save new or changed requests
        for request in game.requestedCalls:
            tmp = self.cachedRequests.pop(request.requestBing.bingIdx, None)

            if not tmp or tmp.players != request.players:
                data = self.__createCallRequestData(gameID,
                                                    request.requestBing.bingIdx,
                                                    json.dumps([p.userID for p in request.players]))
                self.__commitData(cur, data, 'bingid', Recovery.__REQUESTS)

            tmpNewReq[request.requestBing.bingIdx] = request

        # Remove any old requests
        for request in self.cachedRequests.values():
            self.__removeData(cur, 'bingid', request.requestBing.bingIdx, Recovery.__REQUESTS)

        self.cachedRequests = tmpNewReq

    def __commitData(self, cur: sqlite3.Cursor, data: Dict[Any, Any], idKey: str, tablename: str):
        # Construct the query
        columns = ", ".join(data.keys())
        vals = ", ".join(["?"] * len(data.keys()))
        updateColumns = ", ".join(f"{k}=excluded.{k}" for k in data.keys() if k != idKey)
        sql = f"""
        INSERT INTO {tablename} ({columns})
        VALUES ({vals})
        ON CONFLICT({idKey}) DO UPDATE SET {updateColumns};
        """

        # Insert
        Recovery.__LOGGER.log(LogLevel.LEVEL_INFO, f"{sql}\n{data}")
        cur.execute(sql, list(data.values()))

    def __recoverData(self, cur: sqlite3.Cursor, data: Dict[Any, Any], idKey: str, idVal: int, tablename: str) -> List[Dict[Any, Any]]:
        columns = ", ".join(data.keys())
        sql = f"""
        SELECT {columns} FROM {tablename} WHERE {idKey} = {idVal};
        """

        cur.execute(sql)
        rows = cur.fetchall()

        columns = list(data.keys())
        return [dict(zip(columns, row)) for row in rows]

    def __removeData(self, cur: sqlite3.Cursor, idKey: str, idVal: int, tablename: str):
        cur.execute(f"DELETE FROM {tablename} WHERE {idKey} = ?", (idVal,))

    def __parseBings(self, gameType: str, bingIDs: Set[int]) -> Set[Bing]:
        binglets = Binglets(gameType)
        return {binglets.getBingFromIndex(x) for x in bingIDs}

    def __createCallRequestData(self, id: int, bingid: int, playerids: str) -> Dict[str, Any]:
        return self.__genericTemplDict(**locals())

    def __createPlayerData(self, id: int, playerid: int, name: str, valid: int, rejectedreqs: int, rejectedtime: float, hasbingo: int) -> Dict[str, Any]:
        return self.__genericTemplDict(**locals())

    def __createPlayerCardData(self, id: int, bingid: str, x: int, y: int, marked: int):
        return self.__genericTemplDict(**locals())

    def __closeDB(self, conn: sqlite3.Connection):
        conn.close()

    @staticmethod
    def __genericTemplDict(**kwargs) -> Dict[str, Any]:
        kwargs.pop('self', None)
        return kwargs

