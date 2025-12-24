__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import json
import pytest
import random
import sqlite3
import time

import test.utils.Const as Const
import test.utils.Utils as Utils
import game.Recovery as RecoveryModule

from game.Bing import Bing
from game.Binglets import Binglets
from game.CallRequest import CallRequest
from game.Game import Game, GameState
from game.Player import Player
from game.Recovery import Recovery
from game.Result import Result

from unittest.mock import MagicMock
from typing import List, Optional

@pytest.fixture(scope="function")
def mock_Database(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")

    # Patch the DB connect to use our in-memory connection
    monkeypatch.setattr(RecoveryModule.sqlite3, "connect", lambda *args, **kwargs: conn)
    monkeypatch.setattr(RecoveryModule.Recovery, "_Recovery__closeDB", lambda self, conn: None)

    # These tables are defined in the InitDB.sh script for the production
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS RECOVER (
            guildid INTEGER PRIMARY KEY,
            gamestate TEXT NOT NULL,
            gametype TEXT NOT NULL,
            timestarted INTEGER DEFAULT 0,
            calledbings TEXT NOT NULL DEFAULT '[]',
            kickedplayers TEXT NOT NULL DEFAULT '[]',
            playerbingos TEXT NOT NULL DEFAULT '[]',
            timesaved INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS RECPLAYERS (
            id INTEGER NOT NULL,
            playerid INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            valid INTEGER DEFAULT 0,
            rejectedreqs INTEGER DEFAULT 0,
            rejectedtime REAL NOT NULL DEFAULT 0.0,
            hasbingo INTEGER NOT NULL,
            FOREIGN KEY (id) REFERENCES RECOVER(guildid)
            ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS RECPLAYERCELLS (
            id INTEGER NOT NULL,
            bingid INTEGER PRIMARY KEY,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            marked INTEGER NOT NULL,
            FOREIGN KEY (id) REFERENCES RECPLAYERS(playerid)
            ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS RECREQUESTS (
            id INTEGER NOT NULL,
            bingid INTEGER PRIMARY KEY,
            playerids TEXT NOT NULL,
            FOREIGN KEY (id) REFERENCES RECOVER(guildid)
            ON DELETE CASCADE
        )
    """)
    conn.commit()

    yield conn

    conn.close()

def test_GameStateIsSuccessfullyPersisted(mock_Database, monkeypatch):
    conn: sqlite3.Connection = mock_Database
    Utils.disableBannedData(monkeypatch)

    game: Game = Game(Const.TEST_GAME_TYPE)

    game.initGame(MagicMock())
    assert game.state is GameState.IDLE

    game.startGame()
    assert game.state is GameState.STARTED

    populateGame(game)

    # Persist the recovery data
    recovery = Recovery(Const.TEST_GUILD_ID)
    recovery.updateRecovery(game)

    checkDB(conn, game)

def test_GameIsSuccessfullyRecovered(mock_Database, monkeypatch):
    Utils.disableBannedData(monkeypatch)

    # Populate the game to use as a reference, and save it to the DB
    referenceGame: Game = Game(Const.TEST_GAME_TYPE)
    referenceGame.initGame(MagicMock())
    assert referenceGame.state is GameState.IDLE
    referenceGame.startGame()
    assert referenceGame.state is GameState.STARTED
    populateGame(referenceGame)

    # Save the game recovery data
    recovery = Recovery(Const.TEST_GUILD_ID)
    recovery.updateRecovery(referenceGame)

    # Recover the game from the DB
    assert recovery.hasRecovery()
    game: Optional[Game] = recovery.recoverGame(MagicMock())
    assert game is not None

    # Check the game state
    assert referenceGame.state == game.state
    assert referenceGame.gameType == game.gameType
    assert referenceGame.players == game.players
    assert referenceGame.timeStarted == game.timeStarted
    assert referenceGame.calledBings == game.calledBings
    assert referenceGame.kickedPlayers == game.kickedPlayers
    assert referenceGame.playerBingos == game.playerBingos
    assert len(referenceGame.requestedCalls) == len(game.requestedCalls)
    game.requestedCalls = sorted(game.requestedCalls, key=lambda req: req.requestBing.bingIdx)
    for i, refReq in enumerate(sorted(referenceGame.requestedCalls, key=lambda req: req.requestBing.bingIdx)):
        req = game.requestedCalls[i]
        assert refReq == req, f"Call Request doesn't match the reference:" \
                            + f"\n\tReference: ID({refReq.requestBing.bingIdx} Players {[p.userID for p in list(refReq.players)]})" \
                            + f"\n\tRecovered: ID({req.requestBing.bingIdx} Players {[p.userID for p in list(req.players)]})"

    # Check the players
    for refPlayer in referenceGame.players:
        refCells = refPlayer.card.getCardBings()
        player = next((pl for pl in game.players if pl == refPlayer))
        assert player is not None
        cells = player.card.getCardBings()

        for x, cellX in enumerate(refCells):
            for y, cellY in enumerate(cellX):
                assert cellY.bingIdx == cells[x][y].bingIdx
                assert cellY.x == cells[x][y].x
                assert cellY.y == cells[x][y].y
                assert cellY.marked == cells[x][y].marked

def test_PlayerBingosAreRecovered(mock_Database, monkeypatch):
    Utils.disableBannedData(monkeypatch)
    game: Game = Game(Const.TEST_GAME_TYPE)

    # Start the game
    game.initGame(MagicMock())
    assert game.state is GameState.IDLE
    game.startGame()
    assert game.state is GameState.STARTED

    # Add 3 players
    for i in range(3):
        name = f"TestPlayer{i+1}"
        userID = Const.TEST_MOCK_VALID_USER_ID + i

        result: Result = game.addPlayer(name, userID)
        assert result.result

    # Horizontal bingo
    player: Player = game.getPlayer(Const.TEST_MOCK_VALID_USER_ID).additional
    assert player is not None
    xRow = random.randint(0, player.card._cardSize - 1)
    cells: List[List[Bing]] = player.card.getCardBings()
    for i in range(player.card._cardSize):
        player.card.markCell(cells[xRow][i])
    assert player.card.hasBingo()

    # Vertical bingo
    player: Player = game.getPlayer(Const.TEST_MOCK_VALID_USER_ID + 1).additional
    assert player is not None
    yRow = random.randint(0, player.card._cardSize - 1)
    cells: List[List[Bing]] = player.card.getCardBings()
    for i in range(player.card._cardSize):
        player.card.markCell(cells[i][yRow])
    assert player.card.hasBingo()

    # Diag bingo
    player: Player = game.getPlayer(Const.TEST_MOCK_VALID_USER_ID + 2).additional
    assert player is not None
    cells: List[List[Bing]] = player.card.getCardBings()
    for i in range(player.card._cardSize):
        player.card.markCell(cells[i][i])
    assert player.card.hasBingo()

    # Persist the recovery data
    recovery = Recovery(Const.TEST_GUILD_ID)
    recovery.updateRecovery(game)

    # Recover the game from the DB
    assert recovery.hasRecovery()
    game: Optional[Game] = recovery.recoverGame(MagicMock())
    assert game is not None

    # Verify each player still has a bingo
    for player in game.players:
        assert player.card.hasBingo(), f"Player {player.userID} does not have a bingo"

def test_ReveryDataIsPersistedOnlyWhenNeeded(mock_Database, monkeypatch):
    conn: sqlite3.Connection = mock_Database
    Utils.disableBannedData(monkeypatch)

    # Boilerplates for checking num times __commitData is called
    assertNumCommitDataCalled = 0
    commitData = Recovery._Recovery__commitData # pyright: ignore
    numCalledCommitData = 0
    def overrideCommitData(self, *args, **kwargs):
        nonlocal numCalledCommitData
        numCalledCommitData += 1
        return commitData(self, *args, **kwargs)
    monkeypatch.setattr(RecoveryModule.Recovery, "_Recovery__commitData", overrideCommitData)

    # Boilerplayes for checking num times __removeData is called
    assertNumRemoveDataCalled = 0
    removeData = Recovery._Recovery__removeData # pyright: ignore
    numCalledRemoveData = 0
    def overrideRemoveData(self, *args, **kwargs):
        nonlocal numCalledRemoveData
        numCalledRemoveData += 1
        return removeData(self, *args, **kwargs)
    monkeypatch.setattr(RecoveryModule.Recovery, "_Recovery__removeData", overrideRemoveData)

    game: Game = Game(Const.TEST_GAME_TYPE)
    game.initGame(MagicMock())
    assert game.state is GameState.IDLE
    game.startGame()
    assert game.state is GameState.STARTED

    # Persist the recovery data
    recovery = Recovery(Const.TEST_GUILD_ID)
    recovery.updateRecovery(game)
    assertNumCommitDataCalled = 1
    assert numCalledCommitData  == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Recover the game again
    recovery.updateRecovery(game)
    assert numCalledCommitData == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Add a few players
    for i in range(random.randint(2, 10)):
        name = f"TestPlayer{i+1}"
        userID = Const.TEST_MOCK_VALID_USER_ID + i + 1
        result: Result = game.addPlayer(name, userID)
        assert result.result

    # Re-compute the number of times the commitData should be called
    assertNumCommitDataCalled = len(game.players) * list(game.players)[0].card._cardSize * list(game.players)[0].card._cardSize + len(game.players) + assertNumCommitDataCalled

    # Recover the game again
    recovery.updateRecovery(game)
    assert numCalledCommitData == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Recover the game again
    recovery.updateRecovery(game)
    assert numCalledCommitData == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Remove a player
    game.kickPlayer(Const.TEST_MOCK_VALID_USER_ID + 1)
    recovery.updateRecovery(game)
    assertNumCommitDataCalled += 1
    assertNumRemoveDataCalled += 1
    assert numCalledCommitData == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Call a players slot
    player: Player = list(game.players)[0]
    player.card.markCell(player.card.getCardBings()[0][0])
    recovery.updateRecovery(game)
    assertNumCommitDataCalled += 1
    assert numCalledCommitData == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Make a couple call requests
    binglets = Binglets(Const.TEST_GAME_TYPE)
    bing = binglets.getBingFromIndex(player.card.getCardBings()[0][1].bingIdx)
    result: Result = game.requestCall(CallRequest(player, bing))
    assert result.result
    bing = binglets.getBingFromIndex(player.card.getCardBings()[0][2].bingIdx)
    result: Result = game.requestCall(CallRequest(player, bing))
    assert result.result
    recovery.updateRecovery(game)
    assertNumCommitDataCalled += 2
    assert numCalledCommitData == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Remove a call request
    result: Result = game.deleteRequest(bing.bingIdx)
    assert result.result
    recovery.updateRecovery(game)
    assertNumCommitDataCalled += 1
    assertNumRemoveDataCalled += 1
    assert numCalledCommitData == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Remove the entire game recovery
    recovery.removeRecovery()
    assertNumRemoveDataCalled += 1
    assert numCalledCommitData == assertNumCommitDataCalled
    assert numCalledRemoveData == assertNumRemoveDataCalled

    # Verify all the tables are empty
    rows = conn.execute(f"SELECT * from RECOVER").fetchall()
    assert rows == []

    rows = conn.execute(f"SELECT * FROM RECPLAYERS").fetchall()
    assert rows == []

    rows = conn.execute(f"SELECT * FROM RECPLAYERCELLS").fetchall()
    assert rows == []

    rows = conn.execute(f"SELECT * FROM RECREQUESTS").fetchall()
    assert rows == []

def populateGame(game: Game):
    # Add a few players
    for i in range(random.randint(2, 10)):
        name = f"TestPlayer{i+1}"
        userID = Const.TEST_MOCK_VALID_USER_ID + i + 1

        result: Result = game.addPlayer(name, userID)
        assert result.result

    # Make some calls
    binglets = Binglets(Const.TEST_GAME_TYPE)
    totalBinglets = binglets.getNumBings()
    for i in range(30):
        result: Result = game.makeCall(random.randint(1, totalBinglets))
        assert result.result


    # Make some call requests
    for i in range(random.randint(1, len(game.players))):
        playerID = i + Const.TEST_MOCK_VALID_USER_ID + 1
        player: Player = game.getPlayer(playerID).additional
        x = random.randint(0, player.card._cardSize - 1)
        y = random.randint(0, player.card._cardSize - 1)
        randomPlayerBing = player.card.getCardBings()[x][y]
        # Dont include the free space bing
        if randomPlayerBing.bingIdx == 0:
            continue
        bing = binglets.getBingFromIndex(randomPlayerBing.bingIdx)
        callReq = CallRequest(player, bing)

        result: Result = game.requestCall(callReq)
        assert result.result

def checkDB(conn: sqlite3.Connection, game: Game):
    # Verify the RECOVER table
    rows = conn.execute(f"SELECT * from RECOVER")
    assert rows is not None
    results = rows.fetchall()
    assert len(results) == 1
    results = results[0]
    assert results[0] == Const.TEST_GUILD_ID
    assert int(results[1]) == GameState.STARTED.value
    assert results[2] == Const.TEST_GAME_TYPE
    assert results[3] < time.time()
    assert results[4] == json.dumps([b.bingIdx for b in game.calledBings])
    assert results[5] == json.dumps(list(game.kickedPlayers))
    assert results[6] == json.dumps(list(game.playerBingos))
    assert results[7] < time.time()

    # Verify the RECPLAYERS table
    rows = conn.execute(f"SELECT * from RECPLAYERS")
    assert rows is not None
    results = rows.fetchall()
    assert len(results) == len(game.players)
    for res in results:
        assert res[0] == Const.TEST_GUILD_ID
        assert res[1] != 0

        player = game.getPlayer(int(res[1])).additional
        assert player is not None

        assert res[2] == player.card.getCardOwner()
        assert res[3] == int(player.valid)
        assert res[4] == player.rejectedRequests
        assert res[5] == player.rejectedTimestamp
        assert res[6] == int(player.card.hasBingo())

        # Verify the players card "RECPLAYERCELLS"
        rows = conn.execute(f"SELECT * FROM RECPLAYERCELLS WHERE id = {player.userID}")
        assert rows is not None
        cardResults = rows.fetchall()
        assert len(cardResults) == player.card._cardSize * player.card._cardSize
        playerCells = player.card.getCardBings()
        for cell in cardResults:
            assert cell[0] == player.userID
            assert cell[2] < player.card._cardSize
            assert cell[3] < player.card._cardSize

            referenceBing: Bing = playerCells[cell[2]][cell[3]]
            assert cell[2] == referenceBing.x
            assert cell[3] == referenceBing.y
            assert cell[4] == int(referenceBing.marked)

    # Verify the call requests "RECREQUESTS"
    rows = conn.execute(f"SELECT * FROM RECREQUESTS")
    assert rows is not None
    results = rows.fetchall()
    for res in results:
        assert res[1] >= 0
        req = None
        for r in game.requestedCalls:
            if r.requestBing.bingIdx == res[1]:
                req = r
                break
        assert req is not None
        assert res[2] == json.dumps([p.userID for p in req.players])

