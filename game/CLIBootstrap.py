__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import select
import sys

from config.ClassLogger import ClassLogger
from config.Log import LogLevel

from game.GameInterfaceCLI import GameInterfaceCLI

class CLIBootstrap:
    __LOGGER = ClassLogger(__name__)

    _IDX_CALLBACK = "clb"
    _IDX_DESC = "desc"

    def __init__(self):
        #self.threadCLI = threading.Thread(target=self._cliThread)
        #self.lock = threading.Lock()
        self.game = None
        self.commands = {
            "help": {
                CLIBootstrap._IDX_CALLBACK: self._showHelp,
                CLIBootstrap._IDX_DESC: "\tShow the help message.\n"
            },
            "startgame": {
                CLIBootstrap._IDX_CALLBACK: self.start,
                CLIBootstrap._IDX_DESC: """\
\tStart the game.
\tUsage: Startgame
                """
            },
            "stopgame": {
                CLIBootstrap._IDX_CALLBACK: None,
                CLIBootstrap._IDX_DESC: """\
\tStop the game.
\tUsage: Stopgame
                """
            },
            "addplayer": {
                CLIBootstrap._IDX_CALLBACK: None,
                CLIBootstrap._IDX_DESC: """\
\tAdd a player to the game.
\tUsage: AddPlayer <player name>
                """
            },
            "showcard": {
                CLIBootstrap._IDX_CALLBACK: None,
                CLIBootstrap._IDX_DESC: """\
\tShow the current state of the player card for a specific player.
\tUsage: ShowCard <player name>
                """
            },
            "printcard": {
                CLIBootstrap._IDX_CALLBACK: None,
                CLIBootstrap._IDX_DESC: """\
\tCreates a PNG image of the card and saves it to resources/cards under
\tthe name of the player.
\tUsage: PrintCard <player name>
                """
            },
            "makecall": {
                CLIBootstrap._IDX_CALLBACK: None,
                CLIBootstrap._IDX_DESC: """\
\tMake a game call. Player's cards with the matching call will all be marked.
\tUse the 'Show' command to list indices for bings.
\tUsage: Makecall <Index #>
                """
            },
            "showbings": {
                CLIBootstrap._IDX_CALLBACK: None,
                CLIBootstrap._IDX_DESC: """\
\tShow all of the available call bings with their associated indices.
\tUsage: ShowBings
                """
            }
        }

    def run(self):
        print("CLI started, type \"help\" for help menu.")
        while True:
            #with self.lock:
            #    running = self.running
            #if not running:
            #    break;

            CLIBootstrap.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Waiting for command...")
            pselect, _, _ = select.select([sys.stdin], [], [], 60)

            command = None
            if pselect:
                command = sys.stdin.readline().strip()
                CLIBootstrap.__LOGGER.log(LogLevel.LEVEL_INFO, f"CLI Command received: {command}")

            if command:
                self._handleCommand(command)

    def start(self, command):
        if self.game:
            errStr = "Game has already been started, skipping."
            CLIBootstrap.__LOGGER.log(LogLevel.LEVEL_ERROR, errStr)
            print(errStr)
            return

        self.game = GameInterfaceCLI()
        gameInitialized = self.game.init()

        if not gameInitialized:
            CLIBootstrap.__LOGGER.log(LogLevel.LEVEL_CRIT, "Failed to initialize the bingo game. Aborting.")
        else:
            self.game.start()
            # Game commands
            self.commands["stopgame"][CLIBootstrap._IDX_CALLBACK] = self.stop
            self.commands["addplayer"][CLIBootstrap._IDX_CALLBACK] = self.game.addPlayer
            self.commands["makecall"][CLIBootstrap._IDX_CALLBACK] = self.game.makeCall

            # These arent "true" game commands, they are debug commands
            self.commands["showcard"][CLIBootstrap._IDX_CALLBACK] = self.game.debugShowCard
            self.commands["printcard"][CLIBootstrap._IDX_CALLBACK] = self.game.debugPrintCard
            self.commands["showbings"][CLIBootstrap._IDX_CALLBACK] = self.game.debugShowBings

        # TODO SCH rm
        #self.game.addPlayer(["addplayer", "wolf"])
        #self.game.debugShowCard(["addplayer", "wolf"])
        #self.game.debugPrintCard(["addplayer", "wolf"])

    def stop(self, command):
        if not self.game:
            errStr = "No game is running, skipping."
            CLIBootstrap.__LOGGER.log(LogLevel.LEVEL_ERROR, errStr)
            print(errStr)
            return

        self.game.destroy()
        del self.game
        self.game = None

    def _handleCommand(self, args):
        tokens = args.split()

        if len(tokens) > 0:
            cmd = self.commands.get(tokens[0].lower(), None)
            if cmd:
                cmd[CLIBootstrap._IDX_CALLBACK](tokens)
            else:
                err = f"\"{tokens[0]}\" is an invalid command"
                CLIBootstrap.__LOGGER.log(LogLevel.LEVEL_ERROR, err)
                print(f"\"{tokens[0]}\" is an invalid command")

    def _showHelp(self, command):
        CLIBootstrap.__LOGGER.log(LogLevel.LEVEL_DEBUG, "ShowHelp command called")

        print("===================Showing game help===================\n")
        for key, value in self.commands.items():
            print(key)
            print(f"{value[CLIBootstrap._IDX_DESC]}")
        print("\n\n")

