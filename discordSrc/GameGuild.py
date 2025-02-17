__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from discord.channel import TextChannel
from game.PersistentStats import PersistentStats

class GameGuild:
    def __init__(self, guildID: int,
                 persistentStats: PersistentStats,
                 channelBingo: TextChannel,
                 channelAdmin: TextChannel):
        self.guildID = guildID
        self.persistentStats = persistentStats
        self.channelBingo = channelBingo
        self.channelAdmin = channelAdmin

