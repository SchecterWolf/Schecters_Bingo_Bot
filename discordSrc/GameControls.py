__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from .EndGameButton import EndGameButton
from .IContentItem import IContentItem
from .PauseGameButton import PauseGameButton
from .ResumeGameButton import ResumeGameButton
from .StartGameButton import StartGameButton

from discord.ui import View
from enum import Enum

class GameControlState(Enum):
    RUNNING = 1
    PAUSED = 2
    ENDED = 3

class GameControls(View, IContentItem):
    MSG_STR = "Game controls"

    def __init__(self, gameID: int):
        View.__init__(self, timeout=None)
        IContentItem.__init__(self, GameControls.MSG_STR)

        self.startButton = StartGameButton()
        self.pauseButton = PauseGameButton(gameID)
        self.resumeButton = ResumeGameButton(gameID)
        self.endGameButton = EndGameButton()

    def setControllsState(self, state: GameControlState):
        # Clear all items in the view
        self.clear_items()

        # Re-add the necessary buttons
        if state == GameControlState.RUNNING:
            self.pauseButton.addToView(self)
            self.endGameButton.addToView(self)
        elif state == GameControlState.PAUSED:
            self.resumeButton.addToView(self)
            self.endGameButton.addToView(self)
        elif state == GameControlState.ENDED:
            self.startButton.addToView(self)
        else:
            pass

