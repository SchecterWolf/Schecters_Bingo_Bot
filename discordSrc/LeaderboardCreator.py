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

from PIL import Image, ImageFont, ImageDraw
from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from game.PersistentStats import PersistentStats, PlayerOrdinal
from io import BytesIO

class LeaderboardCreator(IDiscordGraphical):
    __LOGGER = ClassLogger(__name__)

    __AVATAR_SIZE = 441
    __AVATAR_YPOS = 385
    __AVATAR_1_XPOS = 1220
    __AVATAR_2_XPOS = 314
    __AVATAR_3_XPOS = 2110

    __BOARD_POINTS_HEIGHT = 1415
    __BOARD_SLATE_WIDTH = 560
    __BOARD_TITLE_HEIGHT = 1175

    __COLUMN_1_XPOS = 1140
    __COLUMN_2_XPOS = 240
    __COLUMN_3_XPOS = 2050

    __FONT_SPACER = 10
    __FONT_SIZE_POINTS = 50
    __FONT_SIZE_TITLE = 100
    __FONT_SIZE_TITLE_MIN = 55

    __TITLE_CHAR_ROW_MAX = 13
    __TITLE_HEIGHT_MAX = 200
    __TITLE_ROWS_MAX = 3

    def __init__(self, bot: discord.Client, globalStats: PersistentStats):
        super().__init__(bot)

        self.globalStats = globalStats
        self.fontName = Config().getConfig("Font")

        self.avatarOffsets = {
            0: LeaderboardCreator.__AVATAR_1_XPOS,
            1: LeaderboardCreator.__AVATAR_2_XPOS,
            2: LeaderboardCreator.__AVATAR_3_XPOS - 2
        }

        self.columnsOffsets = {
            0: LeaderboardCreator.__COLUMN_1_XPOS,
            1: LeaderboardCreator.__COLUMN_2_XPOS + 6,
            2: LeaderboardCreator.__COLUMN_3_XPOS + 6
        }

    async def createAsset(self) -> discord.File:
        LeaderboardCreator.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Creating leaderboard graphic")
        leaderboardGraphic = Image.open(GLOBALVARS.IMAGE_GLOBAL_BOARD).convert("RGBA")

        # Create the user avatar layer
        canvas = Image.new("RGBA", leaderboardGraphic.size, (255, 255, 255, 255))
        for ordinal in list(range(0, 3)):
            player = self.globalStats.getTopPlayer(ordinal + 1)
            if player:
                avatar = await self._getDiscordAvatar(player, LeaderboardCreator.__AVATAR_SIZE)
                canvas.paste(avatar, (self.avatarOffsets[ordinal], LeaderboardCreator.__AVATAR_YPOS), avatar)

        # Overlay the leaderboard graphic on top of the avatar layer
        leaderboardGraphic = Image.alpha_composite(canvas, leaderboardGraphic)

        # Add the leaderboard texts
        draw = ImageDraw.Draw(leaderboardGraphic)
        for ordinal in list(range(0, 3)):
            player = self.globalStats.getTopPlayer(ordinal + 1)
            if player:
                self._drawTitleName(draw, player, self.columnsOffsets[ordinal])
                self._drawGamePoints(draw, player, self.columnsOffsets[ordinal])

        # TODO SCH If this works, redo the bingo card board images to use this method
        # Create a discord file from the leaderboard image
        with BytesIO() as imageData:
            leaderboardGraphic.save(imageData, "PNG")
            imageData.seek(0)
            file = discord.File(imageData, "leaderboard.png")

        return file

    def _drawGamePoints(self, draw: ImageDraw.ImageDraw, player: PlayerOrdinal, offset: int):
        listCategory = ["Bingos", "Slots", "Games"]
        yOffset = LeaderboardCreator.__BOARD_POINTS_HEIGHT
        try:
            fontPoints = ImageFont.truetype(self.fontName, LeaderboardCreator.__FONT_SIZE_POINTS)
        except Exception:
            LeaderboardCreator.__LOGGER.log(LogLevel.LEVEL_ERROR,
                                            f"Unable to load font \"{self.fontName}\", using PIL default.")
            fontPoints = ImageFont.load_default()

        # Draw the bonus point descriptors
        for i, dType in enumerate(PersistentStats.LIST_DATA_ITEMS):
            typeAttr: int = player.stats["total"][dType]
            typeBonus: int = self.globalStats.getBonus(dType)

            descriptor = f"{listCategory[i]} {typeAttr} x {typeBonus} Pts"
            bbox = draw.textbbox((0, 0), descriptor, font=fontPoints)
            textHeight = bbox[3] - bbox[1]
            draw.text((offset, yOffset), descriptor, fill=(0, 0, 0, 255), font=fontPoints, align="left")

            descriptor = f"{typeAttr * typeBonus} Pts"
            bbox = draw.textbbox((0, 0), descriptor, font=fontPoints)
            textWidth = bbox[2] - bbox[1]
            xPos = offset + LeaderboardCreator.__BOARD_SLATE_WIDTH - textWidth
            draw.text((xPos, yOffset + textHeight + LeaderboardCreator.__FONT_SPACER), descriptor, fill=(0, 0, 77, 255), font=fontPoints, align="right")
            textHeight2 = bbox[3] - bbox[1]

            yOffset += (textHeight + textHeight2 + LeaderboardCreator.__FONT_SPACER * 4)

        # Draw the points total
        try:
            fontPoints = ImageFont.truetype(self.fontName, LeaderboardCreator.__FONT_SIZE_POINTS + 20)
        except Exception:
            LeaderboardCreator.__LOGGER.log(LogLevel.LEVEL_ERROR,
                                            f"Unable to load font \"{self.fontName}\", using PIL default.")
            fontPoints = ImageFont.load_default()
        descriptor = f"{player.points['total']} Pts"
        bbox = draw.textbbox((0, 0), descriptor, font=fontPoints)
        textWidth = bbox[2] - bbox[0]
        xPos = offset + (LeaderboardCreator.__BOARD_SLATE_WIDTH - textWidth) / 2
        draw.text((xPos, yOffset + LeaderboardCreator.__FONT_SPACER), descriptor, fill=(0, 0, 77, 255), font=fontPoints, align="center")

    def _drawTitleName(self, draw: ImageDraw.ImageDraw, player: PlayerOrdinal, offset: int):
        fontTitle = None
        nameFits = False
        textWidth = 0
        titleSize = LeaderboardCreator.__FONT_SIZE_TITLE
        wrappedName = textwrap.fill(player.name,
                                    width=LeaderboardCreator.__TITLE_CHAR_ROW_MAX,
                                    break_long_words=True,
                                    max_lines=LeaderboardCreator.__TITLE_ROWS_MAX)

        while not nameFits:
            try:
                fontTitle = ImageFont.truetype(self.fontName, titleSize)
            except Exception:
                LeaderboardCreator.__LOGGER.log(LogLevel.LEVEL_ERROR,
                                                f"Unable to load font \"{self.fontName}\", using PIL default.")
                fontTitle = ImageFont.load_default()
            bbox = draw.multiline_textbbox((0, 0), wrappedName, font=fontTitle)
            textWidth = bbox[2] - bbox[0]
            textHeight = bbox[3] - bbox[1]

            if textWidth <= LeaderboardCreator.__BOARD_SLATE_WIDTH and textHeight <= LeaderboardCreator.__TITLE_HEIGHT_MAX:
                nameFits = True
            else:
                titleSize -= 2

            # This shouldnt happen since textwrap should adequately truncate any name that is too long
            if titleSize < LeaderboardCreator.__FONT_SIZE_TITLE_MIN:
                LeaderboardCreator.__LOGGER.log(LogLevel.LEVEL_ERROR, f"Player name too long \"{player.name}\", skipping name title")

        if nameFits:
            xPos = offset + (LeaderboardCreator.__BOARD_SLATE_WIDTH - textWidth) / 2
            yPos = LeaderboardCreator.__BOARD_TITLE_HEIGHT
            draw.multiline_text((xPos, yPos), wrappedName, fill=(0, 0, 0, 255), font=fontTitle, align="center")

