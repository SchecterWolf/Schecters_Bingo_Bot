__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from discord.channel import TextChannel
from discord.member import Member
from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from game.Player import Player

from typing import List, Optional

class Mee6Controller:
    __LOGGER = ClassLogger(__name__)

    def __init__(self, commandChannel: TextChannel):
        self._commandChannel = commandChannel

    async def issueEXP(self, players: List[Player]):
        Mee6Controller.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Issuing end game EXP to players.")

        expMultiplier = Config().getConfig('EXPMultiplier', 0)
        bonusBingo = Config().getConfig('BonusBingo')
        bonusSlots = Config().getConfig('BonusSlotsCalled')
        bonusGames = Config().getConfig('BonusGamesPlayed')

        if not expMultiplier:
            Mee6Controller.__LOGGER.log(LogLevel.LEVEL_INFO, "EXP Multiplier set to 0, skipping EXP adjustments.")
            return

        for player in players:
            # Ignore debug/invalid users
            if player.userID < 0:
                continue

            user: Optional[Member] = self._commandChannel.guild.get_member(player.userID)

            # Skip if we cant find the user
            if not user:
                continue

            exp = bonusBingo * 1 if player.card.hasBingo() else 0\
                    + bonusSlots * player.card.getNumMarked()\
                    + bonusGames

            exp *= expMultiplier

            Mee6Controller.__LOGGER.log(LogLevel.LEVEL_INFO, f"Issuing user \"{player.card.getCardOwner()}\" [{exp}] EXP")
            await self._commandChannel.send(content=f"!give-xp {user.mention} {exp}")

