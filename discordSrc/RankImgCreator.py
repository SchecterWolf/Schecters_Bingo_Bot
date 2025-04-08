__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord
import textwrap

from .IDiscordGraphical import IDiscordGraphical

from PIL import Image, ImageDraw
from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from game.PersistentStats import PlayerOrdinal, PersistentStats
from io import BytesIO
from typing import Optional

class RankImgCreator(IDiscordGraphical):
    __LOGGER = ClassLogger(__name__)

    __AVATAR_SIZE = 325

    __BOARD_TITLE_WIDTH = 750

    __DESC_BUF = 40
    __DESC_LINE_LEN = 240
    __DESC_WIDTH = 250

    __FONT_SIZE_DESC = 40
    __FONT_SIZE_RANK_TOP = 80
    __FONT_SIZE_TITLE = 75
    __FONT_SIZE_TITLE_MIN = 55

    __RANK_WIDTH = 325

    __TITLE_CHAR_ROW_MAX = 20

    __XPOS_AVATAR = 180
    __YPOS_AVATAR = 178
    __XPOS_DESC = 1010
    __YPOS_DESC = 300
    __XPOS_RANK = 640
    __YPOS_RANK = 165
    __XPOS_TITLE = 1010
    __YPOS_TITLE = 130

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
        canvas.paste(avatar, (RankImgCreator.__XPOS_AVATAR, RankImgCreator.__YPOS_AVATAR), avatar)

        # Overlay the rank graphic on top of the avatar layer
        rankGraphic = Image.alpha_composite(canvas, rankGraphic)

        # Add name title
        draw = ImageDraw.Draw(rankGraphic)
        wrappedName = textwrap.fill(self.playerOrd.name, max_lines=1, width=RankImgCreator.__TITLE_CHAR_ROW_MAX)
        self._drawTitleName(draw, wrappedName, self.fontName,
                fontSize=(RankImgCreator.__FONT_SIZE_TITLE, RankImgCreator.__FONT_SIZE_TITLE_MIN),
                pos=(RankImgCreator.__XPOS_TITLE, RankImgCreator.__YPOS_TITLE),
                sizeMax=(RankImgCreator.__BOARD_TITLE_WIDTH, RankImgCreator.__BOARD_TITLE_WIDTH))

        # Add the ranking text
        self._drawAllTimeRank(self.playerOrd, draw)
        self._drawRank(self.playerOrd, draw)

        with BytesIO() as imageData:
            rankGraphic.save(imageData, "PNG")
            imageData.seek(0)
            file = discord.File(imageData, "rank.png")

        return file

    def _drawAllTimeRank(self, playerOrd: PlayerOrdinal, draw: ImageDraw.ImageDraw):
        rankStr = f"Rank\n{playerOrd.ranks[PersistentStats.ITEM_TOTAL]}"
        fontRank = self._getFont(self.fontName, RankImgCreator.__FONT_SIZE_RANK_TOP)
        bbox = draw.multiline_textbbox((0, 0), rankStr, fontRank)
        textWidth = bbox[2] - bbox[0]
        textHeight = bbox[3] - bbox[1]
        trophyOffset = 50 if playerOrd.ranks[PersistentStats.ITEM_TOTAL] <= 3 else 0
        xPos = RankImgCreator.__XPOS_RANK + (RankImgCreator.__RANK_WIDTH - textWidth) / 2
        yPos = RankImgCreator.__YPOS_RANK + (RankImgCreator.__RANK_WIDTH - textHeight) / 2 - trophyOffset
        draw.multiline_text((xPos, yPos), rankStr, fill=(0, 0, 0, 255), font=fontRank, align="center")

    def _drawRank(self, playerOrd: PlayerOrdinal,  draw: ImageDraw.ImageDraw):
        fontRank = self._getFont(self.fontName, RankImgCreator.__FONT_SIZE_DESC)
        rankTitle = {
            PersistentStats.ITEM_TOTAL: "All-Time",
            PersistentStats.ITEM_MONTH: "Monthly",
            PersistentStats.ITEM_WEEK: "Weekly",
        }

        # TODO SCH rm
        draw.line([(RankImgCreator.__XPOS_DESC, RankImgCreator.__YPOS_DESC), (RankImgCreator.__XPOS_DESC + RankImgCreator.__DESC_WIDTH, RankImgCreator.__YPOS_DESC)], fill='black', width=6)

        offset = RankImgCreator.__XPOS_DESC
        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            # Draw the rank type text
            rankStr = f"{rankTitle[cType]}\n{playerOrd.points[cType]} Pts\n\n\nRank {playerOrd.ranks[cType]}"
            bbox = draw.multiline_textbbox((0, 0), rankStr, fontRank)
            textWidth = bbox[2] - bbox[0]
            draw.multiline_text((offset, RankImgCreator.__YPOS_DESC), rankStr, fill=(0, 0, 0, 255), font=fontRank, align="left")

            # Draw rank line divider
            if cType != PersistentStats.ITEM_WEEK:
                xPos = offset + textWidth + RankImgCreator.__DESC_BUF
                yPos = RankImgCreator.__YPOS_DESC
                yPos2 = RankImgCreator.__YPOS_DESC + RankImgCreator.__DESC_LINE_LEN
                draw.line([(xPos, yPos), (xPos, yPos2)], fill='black', width=6)

            offset += textWidth + RankImgCreator.__DESC_BUF * 2

