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
    __FIELD_MARKED_TITLE = "\U0001F4DD Player Cards Marked"
    __FIELD_MARKED_COL = "\U0001F464"
    __MAX_ROW_COUNT = 8

    def __init__(self, calledBing: Bing, markedPlayers: List[Player], newBingos: str):
        super().__init__()
        _iconName = os.path.basename(GLOBALVARS.IMAGE_CALL_ICON)
        self.file = discord.File(GLOBALVARS.IMAGE_CALL_ICON, filename=_iconName)

        self.color = discord.Color.red()
        self.set_author(name="Bingo slot called", icon_url=f"attachment://{_iconName}")
        self.title = f"\u200b\n\U00002757 {calledBing.bingStr} \U00002757\n\u200b"

        # Add the new bingo players, if any
        if newBingos:
            self.add_field(name="\U0001F3C5 BINGOS \U0001F3C5", value=newBingos, inline=False)
            self._addFieldSeparator()

        # Add the marked players
        if markedPlayers:
            self.add_field(name=CallNoticeEmbed.__FIELD_MARKED_TITLE, value="\u00A0", inline=False)
        curList: List[str] = []
        for i, player in enumerate(markedPlayers):
            if i and i % CallNoticeEmbed.__MAX_ROW_COUNT == 0:
                self.add_field(name=CallNoticeEmbed.__FIELD_MARKED_COL, value="\n".join(curList), inline=True)
                curList.clear()
            else:
                curList.append(player.card.getCardOwner())
        if curList:
            self.add_field(name=CallNoticeEmbed.__FIELD_MARKED_COL, value="\n".join(curList), inline=True)

    def _addFieldSeparator(self):
        self.add_field(name="\u200b", value="\u200b", inline=False)

