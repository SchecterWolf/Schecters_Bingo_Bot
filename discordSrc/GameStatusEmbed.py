__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord
import math

from discord import Embed
from game.Binglets import Binglets
from game.GameStore import GameStore
from game.IStatusInterface import IStatusInterface
from game.Player import Player
from typing import Deque, List, Tuple

# TODO SCH rm
from config.ClassLogger import ClassLogger, LogLevel

class GameStatusEmbed(Embed, IStatusInterface):
    __DISCORD_MAX_INLINE = 3
    __FIELD_BINGO = "Player Bingos"
    __FIELD_CALLS = "Slots Called"
    __ICON_URL = "https://cdn-icons-png.freepik.com/256/3239/3239007.png" # TODO SCH Get an actual icon file
    __LENGTH_MAX_CALLS = 25
    __STATS_EMBED_AUTHOR = "Livestream Bingo Info"
    __STATS_EMBED_TITLE = "Current bingo game: FiveM"
    __WIDTH_MAX_BINGOS = 75

    def __init__(self, gameID: int):
        Embed.__init__(self)
        IStatusInterface.__init__(self)

        self.gameID = gameID
        self.set_author(name=GameStatusEmbed.__STATS_EMBED_AUTHOR, icon_url=GameStatusEmbed.__ICON_URL)
        self.color = discord.Color.blue()
        self.title = GameStatusEmbed.__STATS_EMBED_TITLE

        self.refreshStats()

    def refreshStats(self):
        ClassLogger(__name__).log(LogLevel.LEVEL_DEBUG, "Refreshing game stats")
        self.clear_fields()
        self._refreshBingos()
        self._refreshCalls()
        self._refreshHighestSlotsPlayer()

    def _refreshBingos(self):
        game = GameStore().getGame(self.gameID)
        if not game:
            return

        playerBingoStrs = game.game.getPlayerBingos()
        playerBingos: List[str] = [""] if playerBingoStrs else ["[NONE]"]
        for playerStr in playerBingoStrs:
            playerBingosLine = playerBingos[-1]
            prefix = ""
            if playerBingosLine:
                prefix = ", "

            if len(playerBingosLine) + len(prefix + playerStr) > GameStatusEmbed.__WIDTH_MAX_BINGOS:
                playerBingos.append(playerStr)
            else:
                playerBingos[-1] += prefix + playerStr

        self.add_field(name=GameStatusEmbed.__FIELD_BINGO, value="\n".join(playerBingos), inline=False)
        self._addFieldSeparator(self)

    def _refreshCalls(self):
        game = GameStore().getGame(self.gameID)
        if not game:
            return

        calledStrs: List[List[str]] = [[]]
        for slot in game.game.getCalls():
            calledRow = calledStrs[-1]
            if len(calledRow) >= GameStatusEmbed.__LENGTH_MAX_CALLS:
                calledStrs.append([slot.bingStr])
            else:
                calledStrs[-1].append(slot.bingStr)

        if not calledStrs[0]:
            self.add_field(name=GameStatusEmbed.__FIELD_CALLS, value="[NONE]", inline=False)
        else:
            for row in calledStrs:
                self.add_field(name=GameStatusEmbed.__FIELD_CALLS, value="\n".join(row), inline=True)

            # Pad out empty fields so we can get a new row for the next line item (most player calls)
            pad = math.ceil(Binglets().getNumBings() / GameStatusEmbed.__LENGTH_MAX_CALLS)
            for i in range(pad - len(calledStrs) % GameStatusEmbed.__DISCORD_MAX_INLINE):
                self.add_field(name=GameStatusEmbed.__FIELD_CALLS, value="-----------", inline=True)

            self._addFieldSeparator(self)

    def _refreshHighestSlotsPlayer(self):
        game = GameStore().getGame(self.gameID)
        if not game:
            return

        topPlayers: Deque[Tuple[Player, int]] = Deque()
        for player in game.game.getAllPlayers():
            if not topPlayers:
                topPlayers.appendleft((player, player.card.getNumMarked()))
                continue

            num = player.card.getNumMarked()
            idx = 0
            for index, qStat in enumerate(topPlayers):
                idx = index
                if num >= qStat[1]:
                    break
            topPlayers.insert(idx, (player, num))

            if len(topPlayers) > 3:
                topPlayers.pop()

        ords = IStatusInterface.ORDINALS.copy()
        for player, num in topPlayers:
            self.add_field(name=f"{ords.pop()} place slot count", value=f"{player.card.getCardOwner()} [{num}]")

