__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from config.ClassLogger import ClassLogger, LogLevel
from discord import Embed
from game.PersistentStats import PersistentStats, PlayerOrdinal, CanonicalCType, GetBonus

class PlayerStat(Embed):
    __LOGGER = ClassLogger(__name__)

    def __init__(self, bot: discord.Client, playerOrd: PlayerOrdinal):
        super().__init__()
        self.bot = bot
        self.playerOrd = playerOrd

        self.set_author(name="Livesteam Bingo Player Stats")
        self.color = discord.Color.purple()
        self.title = f"\U0001F537 {playerOrd.name} \U0001F537"

        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            self.add_field(name=CanonicalCType(cType).upper(), value=f"Rank: {playerOrd.ranks[cType]}", inline=False)
            for dType in PersistentStats.LIST_DATA_ITEMS:
                val = playerOrd.stats[cType][dType]
                pts = val * GetBonus(dType)
                self.add_field(name=f"{dType}: {val}", value=f"{pts} Pts", inline=True)
            self.add_field(name="\u200b", value="\u200b")

    async def getEmbed(self) -> Embed:
        user = None
        if self.playerOrd.playerID >= 0:
            user = await self.bot.fetch_user(self.playerOrd.playerID)

        if not user:
            PlayerStat.__LOGGER.log(LogLevel.LEVEL_WARN, f"Could not fetch user \"{self.playerOrd.name}\"({self.playerOrd.playerID})")
        else:
            self.playerOrd.name = user.display_name
            self.set_thumbnail(url=user.display_avatar.url)

        return self

