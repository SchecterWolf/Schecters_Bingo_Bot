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
from game.PersistentStats import PersistentStats, PlayerOrdinal, GetBonus

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
            player = self.globalStats.getTopPlayer(ordinal + 1) or PlayerOrdinal(-1, "NA")
            avatar = await self._getDiscordAvatar(player, LeaderboardCreator.__AVATAR_SIZE)
            canvas.paste(avatar, (self.avatarOffsets[ordinal], LeaderboardCreator.__AVATAR_YPOS), avatar)

        # Overlay the leaderboard graphic on top of the avatar layer
        leaderboardGraphic = Image.alpha_composite(canvas, leaderboardGraphic)

        # Add the leaderboard texts
        draw = ImageDraw.Draw(leaderboardGraphic)
        for ordinal in list(range(0, 3)):
            player = self.globalStats.getTopPlayer(ordinal + 1)
            if not player:
                self._drawTitleName(draw, "N/A", self.fontName,
                                    fontSize=(LeaderboardCreator.__FONT_SIZE_TITLE, LeaderboardCreator.__FONT_SIZE_TITLE_MIN),
                                    pos=(self.columnsOffsets[ordinal], LeaderboardCreator.__BOARD_TITLE_HEIGHT),
                                    sizeMax=(LeaderboardCreator.__BOARD_SLATE_WIDTH, LeaderboardCreator.__TITLE_HEIGHT_MAX))
            else:
                wrappedName = textwrap.fill(player.name,
                                            width=LeaderboardCreator.__TITLE_CHAR_ROW_MAX,
                                            break_long_words=True,
                                            max_lines=LeaderboardCreator.__TITLE_ROWS_MAX)
                self._drawTitleName(draw, wrappedName, self.fontName,
                        fontSize=(LeaderboardCreator.__FONT_SIZE_TITLE, LeaderboardCreator.__FONT_SIZE_TITLE_MIN),
                        pos=(self.columnsOffsets[ordinal], LeaderboardCreator.__BOARD_TITLE_HEIGHT),
                        sizeMax=(LeaderboardCreator.__BOARD_SLATE_WIDTH, LeaderboardCreator.__TITLE_HEIGHT_MAX))
                self._drawGamePoints(draw, player, self.columnsOffsets[ordinal])

        return self._convertFile(leaderboardGraphic, "leaderboard.png")

    def _drawGamePoints(self, draw: ImageDraw.ImageDraw, player: PlayerOrdinal, offset: int):
        listCategory = ["Bingos", "Slots", "Games"]
        yOffset = LeaderboardCreator.__BOARD_POINTS_HEIGHT
        fontPoints = self._getFont(self.fontName, LeaderboardCreator.__FONT_SIZE_POINTS)

        # Draw the bonus point descriptors
        for i, dType in enumerate(PersistentStats.LIST_DATA_ITEMS):
            typeAttr: int = player.stats["total"][dType]
            typeBonus: int = GetBonus(dType)

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
        fontPoints = self._getFont(self.fontName, LeaderboardCreator.__FONT_SIZE_POINTS + 20)
        descriptor = f"{player.points['total']} Pts"
        bbox = draw.textbbox((0, 0), descriptor, font=fontPoints)
        textWidth = bbox[2] - bbox[0]
        xPos = offset + (LeaderboardCreator.__BOARD_SLATE_WIDTH - textWidth) / 2
        draw.text((xPos, yOffset + LeaderboardCreator.__FONT_SPACER), descriptor, fill=(0, 0, 77, 255), font=fontPoints, align="center")

