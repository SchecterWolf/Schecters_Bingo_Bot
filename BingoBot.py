#!/usr/bin/env python3
__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import asyncio
import signal
import sys

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config

from discordSrc.Bot import Bot
from game.CLIBootstrap import CLIBootstrap

closeTriggered = False

def runBotDiscord(logger):
    bot = Bot()

    # Catch int and term signals to gracefully shut down the bot
    def signalCloseWrapper(sig, frame):
        logger.log(LogLevel.LEVEL_CRIT, "SIGINT or SIGTERM received, attempting to shut down...")

        # Force exist if signaled twice
        global closeTriggered
        if closeTriggered:
            sys.exit(0)

        # Tell the bot to start shutting down
        loop = asyncio.get_event_loop()
        loop.create_task(bot.stopBot())
        closeTriggered = True

    signal.signal(signal.SIGINT, signalCloseWrapper)
    signal.signal(signal.SIGTERM, signalCloseWrapper)

    bot.runBot()

def main():
    logger = ClassLogger("Main")
    logger.log(LogLevel.LEVEL_INFO, "Bingo bot starting up...")

    if Config().getConfig('Mode') == "CLI":
        logger.log(LogLevel.LEVEL_DEBUG, "Running game using CLI mode [debug].")
        CLIBootstrap().run()
    else:
        logger.log(LogLevel.LEVEL_DEBUG, "Running game using discord mode.")
        runBotDiscord(logger)

if __name__ == '__main__':
    main()
