__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import discord

from .IDiscordGraphical import IDiscordGraphical

from PIL import Image, ImageDraw
from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS
from game.PersistentStats import PersistentStats, CanonicalCType

class HighScoreCreator(IDiscordGraphical):
    __LOGGER = ClassLogger(__name__)

    __BOARD_TITLE_WIDTH = 2040
    __BOARD_TITLE_HEIGHT = 405

    __FONT_SIZE_BONUS = 120
    __FONT_SIZE_BONUS_DESC = 85
    __FONT_SIZE_DESC = 85
    __FONT_SIZE_NUMS = 120
    __FONT_SIZE_PLAYER = 60
    __FONT_SIZE_TITLE = 140

    __SPACING_NUMS = 30
    __SPACING_LIST = 110
    __SPACING_LIST2 = 88
    __SPACING_BONUSES = 200

    __XPOS_BINGO = 1330
    __XPOS_BONUS = 1080
    __YPOS_BONUS = 2800
    __XPOS_BONUS_DESC = 720
    __YPOS_BONUS_DESC = 2950
    __XPOS_DESC = 590
    __XPOS_GAME = 1850
    __XPOS_NUMS = 310
    __XPOS_PLAYER = 480
    __XPOS_POINTS = 2400
    __XPOS_SLOT = 1615
    __XPOS_TITLE = 340
    __YPOS_DESC = 1160
    __YPOS_LIST = 1320
    __YPOS_LIST2 = 1800
    __YPOS_NUMS = 1770
    __YPOS_TITLE = 650

    def __init__(self, bot: discord.Client, globalStats: PersistentStats):
        super().__init__(bot)

        self.globalStats = globalStats
        self.fontName = Config().getConfig("Font")
        self.cType = ""

    async def createLeaderboard(self, cType: str) -> discord.File:
        self.cType = cType
        return await self.createAsset()

    async def createAsset(self) -> discord.File:
        HighScoreCreator.__LOGGER.log(LogLevel.LEVEL_DEBUG, "Creating high scores graphic")

        if self.cType != PersistentStats.ITEM_TOTAL\
            and self.cType != PersistentStats.ITEM_MONTH\
            and self.cType != PersistentStats.ITEM_WEEK:
                self.cType = PersistentStats.ITEM_TOTAL

        highScoreGraphic = Image.open(GLOBALVARS.IMAGE_HIGH_SCORES).convert("RGBA")
        draw = ImageDraw.Draw(highScoreGraphic)

        # Draw the high scores title
        sn = Config().getConfig("StreamerName")
        title = f"{CanonicalCType(self.cType)}\n\
{sn} Livestream Bingo\nHigh Scores"
        self._drawTitleName(draw, title, self.fontName,
                            fontSize=(HighScoreCreator.__FONT_SIZE_TITLE, HighScoreCreator.__FONT_SIZE_TITLE),
                            pos=(HighScoreCreator.__XPOS_TITLE, HighScoreCreator.__YPOS_TITLE),
                            sizeMax=(HighScoreCreator.__BOARD_TITLE_WIDTH, HighScoreCreator.__BOARD_TITLE_HEIGHT))

        # Draw the descriptor line
        desc = "Player                   Bingos  Slots  Games       Pts"
        font = self._getFont(Config().getConfig("FontSmall"), HighScoreCreator.__FONT_SIZE_DESC)
        draw.text((HighScoreCreator.__XPOS_DESC, HighScoreCreator.__YPOS_DESC), desc, fill=(0, 0, 0, 255), font=font)

        # Draw the high score rank numbers
        nums = "4\n5\n6\n7\n8\n9\n10"
        font = self._getFont(self.fontName, HighScoreCreator.__FONT_SIZE_NUMS)
        draw.multiline_text((HighScoreCreator.__XPOS_NUMS, HighScoreCreator.__YPOS_NUMS),
                            nums, fill=(0, 0, 0, 255), font=font, align="center", spacing=HighScoreCreator.__SPACING_NUMS)

        self._drawRanks(draw)
        self._drawBonusInfo(draw)

        return self._convertFile(highScoreGraphic, "highscores.png")

    def _drawBonusInfo(self, draw: ImageDraw.ImageDraw):
        # Bonus title
        font = self._getFont(self.fontName, HighScoreCreator.__FONT_SIZE_BONUS)
        draw.text((HighScoreCreator.__XPOS_BONUS, HighScoreCreator.__YPOS_BONUS), "Bonuses", fill=(0, 0, 0, 255), font=font)

        data = {
            "Bingos": Config().getConfig('BonusBingo'),
            "Slots": Config().getConfig('BonusSlotsCalled'),
            "Games": Config().getConfig('BonusGamesPlayed')
        }

        font = self._getFont(self.fontName, HighScoreCreator.__FONT_SIZE_BONUS_DESC)
        offset = HighScoreCreator.__XPOS_BONUS_DESC
        for key, val in data.items():
            text = f"{key}\n{val} Pts"
            bbox = draw.multiline_textbbox((0, 0), text, font)
            textWidth = bbox[2] - bbox[0]
            xPos = offset
            yPos = HighScoreCreator.__YPOS_BONUS_DESC
            draw.multiline_text((xPos, yPos), text, fill=(0, 0, 0, 255), font=font, align="center")
            offset += textWidth + HighScoreCreator.__SPACING_BONUSES

    def _drawRanks(self, draw: ImageDraw.ImageDraw):
        font  = self._getFont(self.fontName, HighScoreCreator.__FONT_SIZE_PLAYER)
        yPos = {
            0: HighScoreCreator.__YPOS_LIST,
            1: HighScoreCreator.__YPOS_LIST2
        }
        spacing = {
            0: HighScoreCreator.__SPACING_LIST,
            1: HighScoreCreator.__SPACING_LIST2
        }
        data = {
            "names": {
                "val": {
                    0: "",
                    1: ""
                },
                "x": HighScoreCreator.__XPOS_PLAYER,
            },
            "bingos": {
                "val": {
                    0: "",
                    1: ""
                },
                "x": HighScoreCreator.__XPOS_BINGO,
            },
            "slots": {
                "val": {
                    0: "",
                    1: ""
                },
                "x": HighScoreCreator.__XPOS_SLOT,
            },
            "games": {
                "val": {
                    0: "",
                    1: ""
                },
                "x": HighScoreCreator.__XPOS_GAME,
            },
            "points": {
                "val": {
                    0: "",
                    1: ""
                },
                "x": HighScoreCreator.__XPOS_POINTS,
            },
        }

        # Populate the player text data
        for index, playerOrd in enumerate(self.globalStats.getAllPlayers(self.cType)):
            points = playerOrd.points[self.cType]
            if points < 1:
                continue

            cls = 0 if index < 3 else 1
            data["names"]["val"][cls] += f"{playerOrd.name}\n"
            data["bingos"]["val"][cls] += f"{playerOrd.stats[self.cType][PersistentStats.DATA_ITEM_BINGOS]}\n"
            data["slots"]["val"][cls] += f"{playerOrd.stats[self.cType][PersistentStats.DATA_ITEM_CALLS]}\n"
            data["games"]["val"][cls] += f"{playerOrd.stats[self.cType][PersistentStats.DATA_ITEM_GAMES]}\n"
            data["points"]["val"][cls] += f"{points}\n"
            if index == 9:
                break

        # Draw player text data
        data.values
        for key, val in data.items():
            for cls in [0, 1]:
                if key != "points":
                    draw.multiline_text((val["x"], yPos[cls]), val["val"][cls],
                                        fill=(0, 0, 0, 255), font=font, spacing=spacing[cls])
                else:
                    bbox = draw.textbbox((0, 0), val["val"][cls], font=font)
                    textWidth = bbox[2] - bbox[0]
                    draw.multiline_text((val["x"] - textWidth, yPos[cls]), val["val"][cls],
                                        fill=(0, 0, 0, 255), font=font, spacing=spacing[cls], align="right")

