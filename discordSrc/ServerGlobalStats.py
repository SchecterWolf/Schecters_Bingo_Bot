__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from config.ClassLogger import ClassLogger
from config.Log import LogLevel
from discord import Embed
from game.IStatusInterface import IStatusInterface
from game.PersistentStats import PersistentStats, TypeStat
from typing import Deque

class ServerGlobalStats(Embed, IStatusInterface):
    __LOGGER = ClassLogger(__name__)
    __STATS_EMBED_TITLE = "Bingo leaderboards"

    def __init__(self, persistentStats: PersistentStats):
        Embed.__init__(self)
        IStatusInterface.__init__(self)

        self.persistentStats = persistentStats

        self.color = discord.Color.green()
        self.title = ServerGlobalStats.__STATS_EMBED_TITLE

        self.refreshStats()

    # TODO SCH Use the PIL module to instead create a decorated picture that has the information
    #       Picture can have a placement podium, trophy, and the user's discord picture
    def refreshStats(self):
        ServerGlobalStats.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Refreshing the global stats embed view.")
        self.clear_fields()
        self._addFieldSeparator(self)
        self._refreshPlaceField(self.persistentStats.topBingos, "place bingo count")
        self._addFieldSeparator(self)
        self._refreshPlaceField(self.persistentStats.topCalls, "place call count")
        self._addFieldSeparator(self)
        self._refreshPlaceField(self.persistentStats.topGames, "place games played")

    def _refreshPlaceField(self, queue: Deque[TypeStat], placeStr: str):
        ords = IStatusInterface.ORDINALS.copy()
        for stat in queue:
            # TODO SCH use mentions instead of the regular name
            self.add_field(name=f"{ords.pop()} {placeStr}", value=f"{stat[0]} [{stat[2]}]")

