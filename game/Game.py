__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .BannedData import BannedData
from .Bing import Bing
from .Binglets import Binglets
from .CallRequest import CallRequest
from .PersistentStats import PersistentStats
from .Player import Player
from .Result import Result

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from enum import Enum
from typing import List, Optional, Set, Union

class GameState(Enum):
    NEW = 1 # Uninitialized
    IDLE = 2
    STARTED = 3
    PAUSED = 4
    STOPPED = 5
    DESTROYED = 6

class Game:
    _NUM_GEN_TRIES = 5
    _LOGGER = ClassLogger(__name__)
    _STATE_STRS = {
        GameState.NEW: "new",
        GameState.IDLE: "idle",
        GameState.STARTED: "started",
        GameState.PAUSED: "paused",
        GameState.STOPPED: "paused"
    }

    def __init__(self):
        self.config: Config = Config()
        self.bannedPlayers = BannedData()
        self.persistentStats: Optional[PersistentStats] = None
        self.state: GameState = GameState.NEW

        self.calledBings: Set[Bing] = set()
        self.kickedPlayers: Set[int] = set()
        self.playerBingos: Set[str] = set()
        self.players: Set[Player] = set()
        self.requestedCalls: List[CallRequest] = []

    def initGame(self, stats: PersistentStats) -> bool:
        if self.state != GameState.NEW:
            Game._LOGGER.log(LogLevel.LEVEL_WARN, "Game has already been initialized.")
        else:
            self.state = GameState.IDLE
            self.persistentStats = stats
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, "Game initialized successfully.")

        return self.state != GameState.NEW

    def destroyGame(self):
        self.stopGame()
        self.state = GameState.DESTROYED

    def startGame(self) -> Result:
        Game._LOGGER.log(LogLevel.LEVEL_DEBUG, "Game is starting...")
        ret = Result(True)

        if self.state != GameState.IDLE:
            ret.result = False
            ret.responseMsg = f"Cannot start the bingo game while the game is {self._getStateString()}."

        if ret.result:
            self._resetGame()
            self.state = GameState.STARTED

            ret.result = True
            ret.responseMsg = "A new bingo game has been started."

        if ret.result:
            Game._LOGGER.log(LogLevel.LEVEL_INFO, ret.responseMsg)

        return ret

    def stopGame(self) -> Result:
        Game._LOGGER.log(LogLevel.LEVEL_DEBUG, "Stopping game...")
        ret = Result(False)

        # Sanity Check
        if self.state == GameState.STOPPED:
            return ret

        if self.persistentStats:
            self.persistentStats.updateFromPlayers(self.getAllPlayers())
        self._resetGame()
        self.state = GameState.STOPPED

        ret.result = True
        ret.responseMsg = "Bingo game stopped."
        Game._LOGGER.log(LogLevel.LEVEL_INFO, ret.responseMsg)

        return ret

    def pauseGame(self) -> Result:
        ret = Result(False)
        if self.state != GameState.STARTED:
            ret.responseMsg = f"Cannot pause the bingo game while the game is {self._getStateString()}."
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
        else:
            self.state = GameState.PAUSED
            ret.result = True

        return ret

    def resumeGame(self) -> Result:
        ret = Result(False)
        if self.state != GameState.PAUSED:
            ret.responseMsg = f"Cannot resume the bingo game while the game is {self._getStateString()}."
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
        else:
            self.state = GameState.STARTED
            ret.result = True

        return ret

    def addPlayer(self, playerName: str, userID: int) -> Result:
        ret = Result(False)
        player = Player(playerName, userID)
        matchedCards = []
        tries = 0

        # Check pre-conditions
        if self.state != GameState.STARTED:
            ret.responseMsg = f"New players cannot be added while the game is {self._getStateString()}."
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
            return ret

        # Check if player is eligible
        ret = self.checkEligible(player)
        if not ret.result:
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
            return ret

        # Try to generate a unique game card for the player for a given number of tries
        while tries < Game._NUM_GEN_TRIES:
            Game._LOGGER.log(LogLevel.LEVEL_DEBUG, f"Attempting to generate new card for player {playerName}")
            cardID = player.card.generateNewCard()
            matchedCards = []

            for _player in self.players:
                if _player.card.getCardID() == cardID:
                    matchedCards.append(_player.card)

            if not matchedCards:
                Game._LOGGER.log(LogLevel.LEVEL_INFO, f"Game card \"{cardID}\" is unique.")
                tries = Game._NUM_GEN_TRIES
            else:
                Game._LOGGER.log(LogLevel.LEVEL_WARN,
                                 f"Game card \"{cardID}\" is NOT unique, attempting to re-generate game card for player \"{playerName}\"")
                tries += 1

        # Apply all past calls to the new players card, if configured for retroactive calls
        if self.config.getConfig("RetroactiveCalls"):
            Game._LOGGER.log(LogLevel.LEVEL_INFO, f"Adding all past calls to \"{playerName}'s'\" game card...")
            for call in self.calledBings:
                player.card.markCell(call)

        # Add player's game card to the game
        self.players.add(player)
        ret.result = True
        ret.additional = player
        ret.responseMsg = f"Player \"{playerName}\" has been added to the game."
        Game._LOGGER.log(LogLevel.LEVEL_INFO, ret.responseMsg)

        # Show potential card conflict with other player, if any
        if matchedCards:
            commonCards = ""
            for card in matchedCards:
                if commonCards:
                    commonCards += ", "
                commonCards += card.getCardOwner()
            warn = f" Note that this player shares an identical game card with: {commonCards}"
            ret.responseMsg += f"\n{warn}"
            Game._LOGGER.log(LogLevel.LEVEL_WARN, warn)

        return ret

    def kickPlayer(self, playerID: int) -> Result:
        ret = Result(False)
        kickPlayer = Player("", -1)

        # Try to find the player among the existing game players
        for player in self.players:
            if player.userID == playerID:
                kickPlayer = player
                break

        # Bail if we couldn't find the player
        if kickPlayer.userID < 0 and not Config().getConfig("Debug"):
            ret.responseMsg = f"No player with ID {playerID} exists in the game currently."
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
            return ret

        # Set player validity to false. Some procedures check this value before processing
        kickPlayer.valid = False

        # Add player to the game's kick list
        self.kickedPlayers.add(playerID)

        # Remove player from the game player list
        self.players.discard(kickPlayer)

        # Remove from player bingos, if any
        self.playerBingos.discard(kickPlayer.card.getCardOwner())

        # Remove player from any requested calls
        for request in self.requestedCalls:
            request.removePlayer(kickPlayer)

        ret.result = True
        ret.additional = kickPlayer
        return ret

    def banPlayer(self, playerID: int, playerName: str) -> Result:
        ret = self.kickPlayer(playerID)

        # Ban regardless of kickPlayer result
        self.bannedPlayers.addBanned(playerID, playerName)

        # Remove player from the saved player data
        if self.persistentStats:
            self.persistentStats.removePlayer(playerID)

        return ret

    def makeCall(self, index: int) -> Result:
        ret = Result(False)

        # Check pre-conditions
        if self.state != GameState.STARTED:
            ret.responseMsg = f"Cannot make a call while the game is {self._getStateString()}."
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
            return ret

        calledBing = Binglets().getBingFromIndex(index)

        Game._LOGGER.log(LogLevel.LEVEL_INFO, f"Marking \"{calledBing.bingStr}\" as called!")
        self.calledBings.add(calledBing)

        # Try and mark the bing for each player in the game
        markedPlayers: Set[Player] = set()
        newBingos: Set[Player] = set()
        for player in self.players:
            if player.card.markCell(calledBing):
                markedPlayers.add(player)
            if player.card.hasBingo() and player.card.getCardOwner() not in self.playerBingos:
                newBingos.add(player)
                self.playerBingos.add(player.card.getCardOwner())

        ret.result = True
        ret.responseMsg = f"Slot \"{calledBing.bingStr}\" has been called -> {len(markedPlayers)} game cards have been marked!"
        ret.additional = (markedPlayers, newBingos)
        Game._LOGGER.log(LogLevel.LEVEL_DEBUG, ret.responseMsg)

        return ret

    def requestCall(self, callRequest: CallRequest) -> Result:
        ret = Result(False)
        existingRequest = None

        # Check pre-conditions
        if self.state != GameState.STARTED:
            ret.responseMsg = f"Request call cannot be made while the game is {self._getStateString()}."
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
            return ret

        # Make sure the player is still playing the game
        if not self.getPlayer(callRequest.getRequesterName()).result:
            ret.responseMsg = f"Player {callRequest.getPrimaryRequester().card.getCardOwner()} has not been added\
 to the game. Rejecting the request call."
            Game._LOGGER.log(LogLevel.LEVEL_ERROR, ret.responseMsg)
            return ret

        # Try and find an existing matching request, if any
        for request in self.requestedCalls:
            if callRequest.isMatchingRequest(request):
                existingRequest = request
                break

        # Merge requests if a matching one already exists
        if existingRequest:
            existingRequest.mergeRequests(callRequest)
        # Add in a new call request
        else:
            self.requestedCalls.append(callRequest)
            existingRequest = callRequest

        ret.result = True
        ret.responseMsg = f"Request for {callRequest.requestBing.bingStr} has been made."
        if len(existingRequest.players) > 1:
            ret.responseMsg += f"There are {len(existingRequest.players)} players with this same request."
        ret.additional = existingRequest

        Game._LOGGER.log(LogLevel.LEVEL_INFO, ret.responseMsg)
        return ret

    def deleteRequest(self, index: int) -> Result:
        ret = Result(True)

        # Check game condition
        if self.state != GameState.STARTED and self.state != GameState.PAUSED:
            ret.result = False
            ret.responseMsg = f"Cannot delete call requests while the bingo game is {self._getStateString()}."

        # Attempt to remove call request, if any
        if ret.result:
            removed = False
            for request in self.requestedCalls:
                if index == request.requestBing.bingIdx:
                    removed = True
                    ret.responseMsg = f"Call request \"{request.requestBing.bingStr}\" was removed."
                    self.requestedCalls.remove(request)
            if not removed:
                Game._LOGGER.log(LogLevel.LEVEL_WARN, f"There is no outstanding request for index \"{index}\", skipping.")

        Game._LOGGER.log(LogLevel.LEVEL_INFO if ret.result else LogLevel.LEVEL_ERROR, ret.responseMsg)
        return ret

    def getPlayer(self, playerName: str) -> Result:
        ret = Result(False)
        for player in self.players:
            if player.card.getCardOwner() == playerName:
                ret.responseMsg = f"Game card found for player \"{playerName}\""
                ret.additional = player
                ret.result = True
                Game._LOGGER.log(LogLevel.LEVEL_INFO, ret.responseMsg)
                break

        if not ret.result:
            ret.responseMsg = f"Could not find game card for player \"{playerName}\""

        return ret

    def getGameState(self) -> Result:
        return Result(True, additionalType=self.state)

    def getAllPlayers(self) -> List[Player]:
        return list(self.players)

    def getPlayerBingos(self) -> List[str]:
        return list(self.playerBingos)

    def getCalls(self) -> List[Bing]:
        return list(self.calledBings)

    def checkEligible(self, player: Union[Player, int]) -> Result:
        ret = Result(False)
        pl = player if not isinstance(player, int) else Player(" ", player)
        name = "You are" if isinstance(player, int) else f"{player.card.getCardOwner()} is"

        # Make sure the user has a valid player ID
        if pl.userID < 0 and not Config().getConfig("Debug"):
            ret.responseMsg = f"Cannot add player with invalid ID of: {pl.userID}"
            return ret

        # Check if the player has been banned
        if self.bannedPlayers.isBanned(pl.userID):
            ret.responseMsg = f"{name} banned from the game."
            return ret

        # Check if the player has been kicked before
        if pl.userID in self.kickedPlayers:
            ret.responseMsg = f"{name} kicked from the game, cannot rejoin."
            return ret

        # Check if player has already been added to the game
        if pl in self.players:
            ret.responseMsg = f"{name} already playing the game."
            return ret

        # TODO SCH Use a vulger language filter to check username before adding
        #           Useful libs: better_profanity, profanity-check

        ret.result = True
        return ret

    def _resetGame(self):
        self.players.clear()
        self.calledBings.clear()
        self.requestedCalls.clear()
        self.playerBingos.clear()

    def _decrementState(self, state: Optional[GameState] = None) -> GameState:
        enums = list(GameState)
        indexState = enums.index(state if state else self.state) - 1
        if indexState > 0:
            self.state = enums[indexState]
        return self.state

    def _getStateString(self) -> str:
        return Game._STATE_STRS.get(self.state, "")

