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

    __COLOR_1ST = (204, 150, 0)
    __COLOR_2ND = (145, 159, 163)
    __COLOR_3RD = (196, 118, 59)
    __COLOR_RANK_ALL_TIME = (31, 0, 0)
    __COLOR_RANK_MONTHLY = (0, 0, 31)
    __COLOR_RANK_WEEKLY = (0, 26, 0)

    __BOARD_TITLE_HEIGHT = 150
    __BOARD_TITLE_WIDTH = 750

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
        self.playerOrd = playerOrd

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
        wrappedName = textwrap.fill(self.playerOrd.name, max_lines=2, width=RankImgCreator.__TITLE_CHAR_ROW_MAX)
        self._drawTitleName(draw, wrappedName, self.fontName,
                fontSize=(RankImgCreator.__FONT_SIZE_TITLE, RankImgCreator.__FONT_SIZE_TITLE_MIN),
                pos=(RankImgCreator.__XPOS_TITLE, RankImgCreator.__YPOS_TITLE),
                sizeMax=(RankImgCreator.__BOARD_TITLE_WIDTH, RankImgCreator.__BOARD_TITLE_HEIGHT))

        # Add the ranking text
        self._drawAllTimeRank(self.playerOrd, draw)
        self._drawRank(self.playerOrd, draw)

        return self._convertFile(rankGraphic, "rank.png")

    def _drawAllTimeRank(self, playerOrd: PlayerOrdinal, draw: ImageDraw.ImageDraw):
        rankNum = playerOrd.ranks[PersistentStats.ITEM_TOTAL]
        rankStr = f"Rank\n{rankNum}"
        allTimeColor = {
            1: RankImgCreator.__COLOR_1ST,
            2: RankImgCreator.__COLOR_2ND,
            3: RankImgCreator.__COLOR_3RD
        }
        fontRank = self._getFont(self.fontName, RankImgCreator.__FONT_SIZE_RANK_TOP)

        bbox = draw.multiline_textbbox((0, 0), rankStr, fontRank)
        textWidth = bbox[2] - bbox[0]
        textHeight = bbox[3] - bbox[1]
        trophyOffset = 50 if rankNum <= 3 else 0
        xPos = RankImgCreator.__XPOS_RANK + (RankImgCreator.__RANK_WIDTH - textWidth) / 2
        yPos = RankImgCreator.__YPOS_RANK + (RankImgCreator.__RANK_WIDTH - textHeight) / 2 - trophyOffset

        draw.multiline_text((xPos, yPos), rankStr, fill=allTimeColor.get(rankNum, (0, 0, 0, 255)), font=fontRank, align="center")

    def _drawRank(self, playerOrd: PlayerOrdinal,  draw: ImageDraw.ImageDraw):
        fontRank = self._getFont(self.fontName, RankImgCreator.__FONT_SIZE_DESC)
        rankTitle = {
            PersistentStats.ITEM_TOTAL: "All-Time",
            PersistentStats.ITEM_MONTH: "Monthly",
            PersistentStats.ITEM_WEEK: "Weekly",
        }
        rankColors = {
            PersistentStats.ITEM_TOTAL: RankImgCreator.__COLOR_RANK_ALL_TIME,
            PersistentStats.ITEM_MONTH: RankImgCreator.__COLOR_RANK_MONTHLY,
            PersistentStats.ITEM_WEEK: RankImgCreator.__COLOR_RANK_WEEKLY
        }

        offset = RankImgCreator.__XPOS_DESC
        for cType in PersistentStats.LIST_CATEGORY_ITEMS:
            # Draw the rank type text
            rankStr = f"{rankTitle[cType]}\n\n{playerOrd.points[cType]} Pts\n\nRank {playerOrd.ranks[cType]}"
            bbox = draw.multiline_textbbox((0, 0), rankStr, fontRank)
            textWidth = bbox[2] - bbox[0]
            xPos = offset + (RankImgCreator.__DESC_WIDTH - textWidth) / 2
            yPos = RankImgCreator.__YPOS_DESC
            draw.multiline_text((xPos, yPos), rankStr, fill=rankColors[cType], font=fontRank, align="center")

            # Draw rank line divider
            if cType != PersistentStats.ITEM_WEEK:
                xPos = offset + RankImgCreator.__DESC_WIDTH
                yPos = RankImgCreator.__YPOS_DESC
                yPos2 = RankImgCreator.__YPOS_DESC + RankImgCreator.__DESC_LINE_LEN
                draw.line([(xPos, yPos), (xPos, yPos2)], fill='black', width=6)

            offset += RankImgCreator.__DESC_WIDTH

