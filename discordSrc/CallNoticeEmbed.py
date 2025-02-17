__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord
import os

from discord import Embed
from config.Config import GLOBALVARS
from game.Bing import Bing
from game.Player import Player
from typing import List

class CallNoticeEmbed(Embed):
    __FIELD_MARKED_TITLE = "Player Cards Marked"
    __MAX_ROW_COUNT = 8

    def __init__(self, calledBing: Bing, markedPlayers: List[Player], newBingos: str):
        super().__init__()
        _iconName = os.path.basename(GLOBALVARS.IMAGE_CALL_ICON)
        self.file = discord.File(GLOBALVARS.IMAGE_CALL_ICON, filename=_iconName)

        self.color = discord.Color.red()
        self.set_author(name="Bingo slot called", icon_url=f"attachment://{_iconName}")
        self.title = f"[{calledBing.bingStr}]"

        # Add the new bingo players, if any
        if newBingos:
            self.add_field(name="BINGOS!", value=newBingos, inline=False)

        # Add the marked players
        curList: List[str] = []
        for i, player in enumerate(markedPlayers):
            if i and i % CallNoticeEmbed.__MAX_ROW_COUNT == 0:
                self.add_field(name=CallNoticeEmbed.__FIELD_MARKED_TITLE, value="\n".join(curList), inline=True)
                curList.clear()
            else:
                curList.append(player.card.getCardOwner())
        if curList:
            self.add_field(name=CallNoticeEmbed.__FIELD_MARKED_TITLE, value="\n".join(curList), inline=True)

