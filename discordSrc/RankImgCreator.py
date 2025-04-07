__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IDiscordGraphical import IDiscordGraphical

from PIL import Image, ImageFont, ImageDraw
from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from game.PersistentStats import PlayerOrdinal, PersistentStats
from io import BytesIO
from typing import Optional

class RankImgCreator(IDiscordGraphical):
    __LOGGER = ClassLogger(__name__)

    __AVATAR_SIZE = 400
    __AVATAR_XPOS = 100
    __AVATAR_YPOS = 100

    def __init__(self, bot: discord.Client, playerOrd: Optional[PlayerOrdinal] = None):
        super().__init__(bot)
        self.fontName = Config().getConfig("Font")
        self.playerOrd: Optional[PlayerOrdinal] = playerOrd

    def setPlayer(self, playerOrd: PlayerOrdinal):
        self.playerOrd = self.playerOrd

    async def createAsset(self) -> discord.File:
        if not self.playerOrd:
            return discord.File(BytesIO())
        RankImgCreator.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Creating rank graphic for player \"{self.playerOrd.name}\"")

        rank = self.playerOrd.ranks[PersistentStats.ITEM_TOTAL]

        # Get the rank graphic
        graphicFile = ""
        if rank == 1:
            graphicFile = GLOBALVARS.IMAGE_RANK_1ST_BOARD
        elif rank == 2:
            graphicFile = GLOBALVARS.IMAGE_RANK_2ND_BOARD
        elif rank == 3:
            graphicFile = GLOBALVARS.IMAGE_RANK_3RD_BOARD
        else:
            graphicFile = GLOBALVARS.IMAGE_RANK_BOARD
        rankGraphic = Image.open(graphicFile).convert("RGBA")

        # Create the user avatar layer
        avatar = await self._getDiscordAvatar(self.playerOrd, RankImgCreator.__AVATAR_SIZE)
        canvas = Image.new("RGBA", rankGraphic.size, (255, 255, 255, 255))
        canvas.paste(avatar, (RankImgCreator.__AVATAR_XPOS, RankImgCreator.__AVATAR_YPOS), avatar)

        # Overlay the rank graphic on top of the avatar layer
        rankGraphic = Image.alpha_composite(canvas, rankGraphic)

        # Add the ranking text

        with BytesIO() as imageData:
            rankGraphic.save(imageData, "PNG")
            imageData.seek(0)
            file = discord.File(imageData, "rank.png")

        return file

    def _drawAllTimeRank(self):
        pass


    def _drawRank(self):
        pass

