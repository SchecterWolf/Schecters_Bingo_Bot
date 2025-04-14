__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__= "--"

import argparse
import textwrap

from .ActionData import ActionData
from .Binglets import Binglets
from .CardImgCreator import CardImgCreator
from .Game import Game
from .IGameInterface import IGameInterface
from .PersistentStats import PersistentStats
from .Player import Player
from .Result import Result

from config.ClassLogger import ClassLogger, LogLevel

from typing import Optional, cast

class GameInterfaceCLI(IGameInterface):
    """
    Interface for debugging the core game logic. This is meant for debugging only and
    interactable via stdin
    """
    _logger = ClassLogger(__name__)
    __player_id_counter = 0

    def __init__(self):
        super().__init__(Game())

    def init(self) -> bool:
        stats = PersistentStats()
        bInit = self.game.initGame(stats)
        #if bInit and not self.threadCLI.is_alive():
        #    with self.lock:
        #        self.running = True
        #    self.threadCLI.start()

        # Print out global stats
        print("Top Bingos:")
        for player in stats.topPlayers:
            print(f"\t{player}")

        GameInterfaceCLI._logger.log(LogLevel.LEVEL_DEBUG, "Bingo CLI initialized")
        return bInit

    def start(self):
        ret = self.game.startGame()
        print(ret.responseMsg)

    def destroy(self):
        #if self.threadCLI.is_alive():
        #    with self.lock:
        #        self.running = False
        #    self.threadCLI.join()
        self.game.destroyGame()

    def stop(self, _):
        ret = self.game.stopGame()
        print(ret.responseMsg)

    def pause(self, _: ActionData):
        pass

    def resume(self, _: ActionData):
        pass

    def requestCall(self, _: ActionData):
        pass

    def deleteRequest(self, _: ActionData):
        pass

    def addPlayer(self, data: ActionData):
        self._logger.log(LogLevel.LEVEL_DEBUG, "AddPlayer command called")
        command: str = data.get("command")

        # Get name from args
        parser = argparse.ArgumentParser(prog="AddPlayer", add_help=False)
        name = self._getPlayerNameFromArgs(command, parser)
        if not name:
            return

        result = Result(False)
        if name:
            result = self.game.addPlayer(name, GameInterfaceCLI.__player_id_counter)
            GameInterfaceCLI.__player_id_counter += 1

        print(result.responseMsg)

    def kickPlayer(self, data: ActionData) -> Result:
        return self.game.kickPlayer(data.get("playerID"))

    def banPlayer(self, data: ActionData) -> Result:
        return self.game.banPlayer(data.get("playerID"), data.get("playerName"))

    def makeCall(self, data: ActionData):
        self._logger.log(LogLevel.LEVEL_DEBUG, "MakeCall command called")
        command: str =  data.get("command")
        result = Result(False)

        parser = argparse.ArgumentParser(prog="MakeCall", add_help=False)
        parser.add_argument('cmd', type=str)
        parser.add_argument('index', type=int)

        index = -1
        try:
            args = parser.parse_args(command)
            index = args.index
        except SystemError as e:
            result.responseMsg = "Error making call, invalid index given"
            print(result.responseMsg)

        if index >= 0:
            result = self.game.makeCall(index)

        print(result.responseMsg)

    def debugShowBings(self, command):
        self._logger.log(LogLevel.LEVEL_DEBUG, "ShowBings command called")

        bings = Binglets().getBingletsCopy()
        for bing in bings:
            print(f"[{bing.bingIdx}] {bing.bingStr}")

    def debugPrintCard(self, command):
        self._logger.log(LogLevel.LEVEL_DEBUG, "Print command called")

        # Get name from args
        parser = argparse.ArgumentParser(prog="PrintCard", add_help=False)
        name = self._getPlayerNameFromArgs(command, parser)
        if not name:
            return

        player = None
        if name:
            player = self._getPlayerByName(self.game, name)

        if not player:
            print(f"Could not find player with name \"{name}\"")
        else:
            cardFile, _ = CardImgCreator().createGraphicalCard(player.card)
            print(f"Graphical card saved to: {cardFile}")

    def debugShowCard(self, command):
        self._logger.log(LogLevel.LEVEL_DEBUG, "ShowCard command called")

        # Get name from args
        parser = argparse.ArgumentParser(prog="ShowCard", add_help=False)
        name = self._getPlayerNameFromArgs(command, parser)
        if not name:
            return

        player = None
        if name:
            player = self._getPlayerByName(self.game, name)

        if not player:
            print(f"Could not find player with name \"{name}\"")
        else:
            cells = player.card.getCellsStr()

            # "Marked" the called cells in the card
            for i in range(len(cells)):
                for j in range(len(cells[i])):
                    if player.card.isCellMarked(i, j):
                        cells[i][j] = f"######### {cells[i][j]} #########"

            # Add indexes
            row = []
            for i in range(len(cells)):
                row.append(chr(ord('A') + i - 0))
            cells.insert(0, row)
            for i, row in enumerate(cells):
                if i == 0:
                    row.insert(0, "  ")
                else:
                    row.insert(0, str(i))

            # This section isn't really efficient, but whatever, this is for debugging anyways
            colWidth = [max(len(word) for row in cells for word in str(row[col]).split()) for col in range(len(cells[0]))]
            wrappedLines = []
            maxColLines = [0] * len(colWidth)

            for row in cells:
                wrapped_row = []
                for col, cell in enumerate(row):
                    words = str(cell).split()
                    wrapped_cell = textwrap.fill(" ".join(words), width=colWidth[col]).split("\n")
                    wrapped_row.append(wrapped_cell)
                    maxColLines[col] = max(maxColLines[col], len(wrapped_cell))
                wrappedLines.append(wrapped_row)

            print("+" + "+".join(["-" * (width + 2) for width in colWidth]) + "+")
            for row in wrappedLines:
                for line_idx in range(max(maxColLines)):  # Loop through max lines in any column of the row
                    row_line = []
                    for col_idx, cell in enumerate(row):
                        if line_idx < len(cell):
                            row_line.append(f"{cell[line_idx].center(colWidth[col_idx])}")  # Center align text
                        else:
                            row_line.append(" " * colWidth[col_idx])  # Fill empty lines with spaces
                    print("| " + " | ".join(row_line) + " |")
                print("+" + "+".join(["-" * (width + 2) for width in colWidth]) + "+")

    def _getPlayerNameFromArgs(self, command, parser: argparse.ArgumentParser) -> str:
        name = ""

        parser.add_argument('cmd', type=str)
        parser.add_argument('name', type=str)

        try:
            args = parser.parse_args(command)
            name = args.name
        except Exception:
            print("Error getting player: expected a playername")
            pass

        return name

    def _getPlayerByName(self, game: Game, name: str) -> Optional[Player]:
        ret = None
        for player in game.players:
            if player.card.getCardOwner() == name:
                ret = player
                break
        return ret

